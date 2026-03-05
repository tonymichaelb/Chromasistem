"""Print engine: thread function that sends G-code to the printer line by line."""

import sqlite3
import re
import time
from datetime import datetime

from core.config import (
    DB_NAME, PAUSE_RETRACT_MM, PAUSE_Z_LIFT_MM,
    PAUSE_PARK_X, PAUSE_PARK_Y,
)
from core.printer import send_gcode, connect_printer, check_printer_ready, get_current_position
from core.filament import check_filament_sensor
import core.state as st


def _log_failure_to_db(job_id, code, message):
    """Registra falha detectada automaticamente na tabela print_failure_log."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO print_failure_log (print_job_id, failure_code, failure_message, action)
            VALUES (?, ?, ?, ?)
        ''', (job_id, code, message, 'detected'))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"  ⚠️ Erro ao registrar falha no log: {e}")


def run_print_job(filepath, original_name, job_id):
    """Thread function that sends G-code to the printer line by line."""
    st.printing_in_progress = True
    pause_state_saved_this_pause = False
    try:
        st.print_paused = False
        st.print_stopped = False
        st.g28_executed = False
        st.g29_executed = False
        st.current_pause_state_job_id = None
        st._consecutive_cmd_failures = 0
        pause_state_saved_this_pause = False

        print(f"\n▶️ Iniciando impressão: {original_name}")

        if not check_printer_ready():
            print("✗ Impressão cancelada: impressora não está respondendo")
            conn_local = sqlite3.connect(DB_NAME)
            cursor_local = conn_local.cursor()
            cursor_local.execute('''
                UPDATE print_jobs 
                SET status = 'error', completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (job_id,))
            conn_local.commit()
            conn_local.close()
            return

        time.sleep(0.1)

        print("  🛠️ Enviando comandos de inicialização...")
        if not send_gcode('G21', retries=3):
            print("✗ Falha no G21")
            return
        if not send_gcode('G90', retries=3):
            print("✗ Falha no G90")
            return

        print("  Comandos de inicialização enviados")

        with open(filepath, 'r') as f:
            total_lines = sum(1 for line in f if line.split(';')[0].strip())

        print(f"  Total de comandos: {total_lines}")

        with open(filepath, 'r') as f:
            line_count = 0
            lines_sent = 0
            object_counter = 0

            for line in f:
                if st.print_stopped:
                    print("✗ Impressão PARADA pelo usuário")
                    break

                while st.print_paused and not st.print_stopped:
                    if not pause_state_saved_this_pause:
                        pos = None
                        target_nozzle = target_bed = 0
                        try:
                            pos = get_current_position()
                        except Exception as e:
                            print(f"  ⚠️ Erro ao obter posição (M114): {e}")
                        try:
                            temp_resp = send_gcode('M105')
                            if temp_resp and 'T:' in temp_resp:
                                for ln in temp_resp.split('\n'):
                                    if 'T:' in ln:
                                        t = re.search(r'T:[\d.]+\s*/([\d.]+)', ln)
                                        b = re.search(r'B:[\d.]+\s*/([\d.]+)', ln)
                                        if t: target_nozzle = float(t.group(1))
                                        if b: target_bed = float(b.group(1))
                                        break
                        except Exception as e:
                            print(f"  ⚠️ Erro ao ler temperaturas (M105): {e}")

                        option = 'keep_temp' if st.print_paused_by_filament else st.pause_option_requested

                        st._pause_mem_state['pos_x'] = pos.get('x') if pos else None
                        st._pause_mem_state['pos_y'] = pos.get('y') if pos else None
                        st._pause_mem_state['pos_z'] = pos.get('z') if pos else None
                        st._pause_mem_state['pos_e'] = pos.get('e') if pos else None
                        st._pause_mem_state['target_nozzle'] = target_nozzle
                        st._pause_mem_state['target_bed'] = target_bed
                        st._pause_mem_state['option'] = option
                        st._pause_mem_state['valid'] = True

                        try:
                            send_gcode('G91')
                            send_gcode(f'G1 E-{PAUSE_RETRACT_MM:.2f} F300')
                            send_gcode(f'G1 Z{PAUSE_Z_LIFT_MM:.2f} F300')
                            send_gcode('G90')
                            send_gcode(f'G0 X{PAUSE_PARK_X:.2f} Y{PAUSE_PARK_Y:.2f} F3000')
                            print("  📍 Bico estacionado no canto (park)")
                        except Exception as park_e:
                            print(f"  ⚠️ Erro no park: {park_e}")

                        if option == 'cold':
                            try:
                                send_gcode('M104 S0')
                                send_gcode('M140 S0')
                                print("  ⏸️ Temperaturas desligadas (pausa fria)")
                            except Exception as cold_e:
                                print(f"  ⚠️ Erro ao desligar temperaturas: {cold_e}")
                        elif option == 'filament_change':
                            try:
                                send_gcode('M600', wait_for_ok=True, timeout=60)
                                print("  ⏸️ Comando M600 (troca de filamento) enviado")
                            except Exception as fc_e:
                                print(f"  ⚠️ Erro ao enviar M600: {fc_e}")

                        try:
                            file_offset = f.tell()
                            conn_pause = sqlite3.connect(DB_NAME)
                            cur_pause = conn_pause.cursor()
                            cur_pause.execute('''
                                INSERT INTO print_pause_state
                                (print_job_id, gcode_filename, file_offset, pos_x, pos_y, pos_z, pos_e,
                                 target_nozzle, target_bed, pause_option)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (job_id, original_name, file_offset,
                                  pos.get('x') if pos else None, pos.get('y') if pos else None,
                                  pos.get('z') if pos else None, pos.get('e') if pos else None,
                                  target_nozzle, target_bed, option))
                            conn_pause.commit()
                            conn_pause.close()
                            st.current_pause_state_job_id = job_id
                        except Exception as db_e:
                            print(f"  ⚠️ Erro ao salvar estado de pausa no banco: {db_e}")
                            st.current_pause_state_job_id = job_id

                        pause_state_saved_this_pause = True
                    print("⏸️ Impressão em PAUSA...")
                    time.sleep(1)

                pause_state_saved_this_pause = False

                if st.print_stopped:
                    print("✗ Impressão PARADA durante pausa")
                    break

                filament_check = check_filament_sensor(during_print=True)
                if not filament_check.get('has_filament'):
                    st.print_paused_by_filament = True
                    st.print_paused = True
                    print("🚨 ALERTA: Filamento acabou! Impressão pausada automaticamente.")
                    print("   Recarregue o filamento e clique em CONTINUAR para retomar.")

                    while st.print_paused and not st.print_stopped:
                        filament_check = check_filament_sensor(during_print=True)
                        if filament_check.get('has_filament') and not st.print_paused_by_filament:
                            print("✓ Filamento recarregado e impressão retomada!")
                            break
                        time.sleep(1)

                    if st.print_stopped:
                        print("✗ Impressão PARADA durante falta de filamento")
                        break

                raw_line = line
                raw_lower = raw_line.lower().strip()
                line = line.split(';')[0].strip()

                if raw_lower.startswith(';') and 'printing object' in raw_lower and 'stop' not in raw_lower:
                    object_counter += 1

                if not line:
                    line_count += 1
                    continue

                if st.skip_requested:
                    skip_id = st.skip_object_id
                    if skip_id is None:
                        if 'object' in raw_lower or 'layer' in raw_lower:
                            st.skip_requested = False
                            print("  ⏭️ Fim do skip; continuando no próximo objeto/camada")
                        line_count += 1
                        continue
                    current_index = object_counter - 1
                    if current_index == skip_id:
                        line_count += 1
                        continue
                    if current_index > skip_id:
                        st.skip_requested = False
                        print(f"  ⏭️ Fim do skip do objeto {skip_id}; continuando no objeto {current_index}")
                        # fall through para processar esta linha (início do próximo objeto)

                cmd_upper = line.upper()

                if cmd_upper.startswith('G28'):
                    if st.g28_executed:
                        print("⏭️  Pulando G28 (já foi executado)")
                        line_count += 1
                        continue
                    st.g28_executed = True
                    print("  🏠 Executando homing (G28)... pode levar até 60 segundos")
                elif cmd_upper.startswith('G29'):
                    if st.g29_executed:
                        print("⏭️  Pulando G29 (já foi executado)")
                        line_count += 1
                        continue
                    st.g29_executed = True
                    print("  📐 Executando nivelamento de mesa (G29)... pode levar até 2 minutos")
                elif cmd_upper.startswith('M109'):
                    print("  🔥 Aquecendo bico e aguardando temperatura...")
                elif cmd_upper.startswith('M190'):
                    print("  🔥 Aquecendo mesa e aguardando temperatura...")
                elif cmd_upper.startswith('T'):
                    print(f"  🔧 Selecionando extrusora: {line}")

                response = send_gcode(line, retries=2)

                if st.print_failure_detected:
                    _log_failure_to_db(job_id, st.current_failure_code, st.current_failure_message)
                    st._consecutive_cmd_failures = 0
                    continue

                if response is None:
                    st._consecutive_cmd_failures += 1
                    if st._consecutive_cmd_failures >= st.CONSECUTIVE_FAILURES_THRESHOLD:
                        msg = (f"Impressora não respondeu a {st._consecutive_cmd_failures} "
                               f"comandos consecutivos (último: {line.strip()})")
                        st.print_failure_detected = True
                        st.current_failure_message = msg
                        st.current_failure_code = 'COMM_FAILURE'
                        st.print_paused = True
                        print(f"🚨 FALHA DE COMUNICAÇÃO: {msg}")
                        _log_failure_to_db(job_id, 'COMM_FAILURE', msg)
                        st._consecutive_cmd_failures = 0
                        continue
                    print(f"⚠️ Comando falhou (linha {line_count}): {line} - "
                          f"tentativas sem resposta: {st._consecutive_cmd_failures}/{st.CONSECUTIVE_FAILURES_THRESHOLD}")
                else:
                    st._consecutive_cmd_failures = 0

                line_count += 1
                lines_sent += 1

                if lines_sent % 50 == 0:
                    progress = (lines_sent / total_lines) * 100
                    conn_local = sqlite3.connect(DB_NAME)
                    cursor_local = conn_local.cursor()
                    cursor_local.execute('''
                        UPDATE print_jobs 
                        SET progress = ?
                        WHERE id = ?
                    ''', (progress, job_id))
                    conn_local.commit()
                    conn_local.close()
                    print(f"  Progresso: {progress:.1f}% ({lines_sent}/{total_lines})")

        conn_local = sqlite3.connect(DB_NAME)
        cursor_local = conn_local.cursor()

        cursor_local.execute('SELECT started_at FROM print_jobs WHERE id = ?', (job_id,))
        started_row = cursor_local.fetchone()
        actual_print_time = None

        if started_row and started_row[0]:
            try:
                start_time = datetime.strptime(started_row[0], '%Y-%m-%d %H:%M:%S')
                elapsed = datetime.now() - start_time
                total_seconds = int(elapsed.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60

                if hours > 0:
                    actual_print_time = f"{hours}h {minutes}m {seconds}s"
                else:
                    actual_print_time = f"{minutes}m {seconds}s"

                print(f"⏱️ Tempo real de impressão: {actual_print_time}")
            except Exception as e:
                print(f"⚠️ Erro ao calcular tempo real: {e}")

        cursor_local.execute('''
            UPDATE print_jobs 
            SET status = 'completed', progress = 100, completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (job_id,))

        if actual_print_time:
            cursor_local.execute('''
                UPDATE gcode_files 
                SET print_time = ? 
                WHERE original_name = (SELECT filename FROM print_jobs WHERE id = ?)
            ''', (actual_print_time, job_id))
            print(f"✓ Tempo real salvo no banco: {actual_print_time}")

        conn_local.commit()
        conn_local.close()

        print(f"✓ Impressão concluída: {lines_sent} linhas enviadas")

    except Exception as e:
        print(f"✗ Erro durante impressão: {e}")
        try:
            conn_local = sqlite3.connect(DB_NAME)
            cursor_local = conn_local.cursor()
            cursor_local.execute('''
                UPDATE print_jobs 
                SET status = 'error', completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (job_id,))
            conn_local.commit()
            conn_local.close()
        except:
            pass
    finally:
        st.printing_in_progress = False
