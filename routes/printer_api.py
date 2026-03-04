"""Printer control API routes."""

from flask import Blueprint, request, jsonify, session
import sqlite3
import re
import time
import os
from datetime import datetime

from core.config import (
    DB_NAME, GCODE_FOLDER, PAUSE_RETRACT_MM,
    BED_WIDTH_MM, BED_DEPTH_MM, TEMP_REHEAT_MARGIN,
    TEMP_CHECK_INTERVAL_PRINT_SEC, commands_history, history_lock,
    FILAMENT_SENSOR_MODE, FILAMENT_CHECK_INTERVAL_SEC,
    FILAMENT_CHECK_INTERVAL_PRINT_SEC, FILAMENT_M119_DURING_PRINT,
    MARLIN_FILAMENT_INVERT, app as flask_app,
)
from core.printer import (
    send_gcode as printer_send_gcode, connect_printer,
    disconnect_printer, get_printer_status_serial, parse_m105_temps,
    get_current_position,
)
from core.filament import (
    check_filament_sensor, setup_filament_sensor,
    _extract_marlin_m119_candidates, _parse_marlin_m119_for_filament,
)
from core.gcode import parse_gcode_objects_for_bed
import core.state as st

printer_bp = Blueprint('printer_api', __name__)


@printer_bp.route('/api/printer/status', methods=['GET'])
def printer_status():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT pj.id, pj.filename, pj.progress, pj.started_at, gf.print_time
        FROM print_jobs pj
        LEFT JOIN gcode_files gf ON pj.filename = gf.original_name
        WHERE pj.status = 'printing'
        ORDER BY pj.started_at DESC
        LIMIT 1
    ''')
    current_job = cursor.fetchone()
    current_job_id = current_job[0] if current_job else None
    cursor.execute(
        'SELECT COUNT(*) FROM print_failure_log WHERE print_job_id = ? AND action = ?',
        (current_job_id, 'skipped')
    )
    skipped_count = cursor.fetchone()[0] if current_job_id else 0
    conn.close()

    if current_job:
        is_printing = True
        current_progress = current_job[2] if current_job else 0
        current_filename = current_job[1] if current_job else ''
        started_at = current_job[3] if current_job else None
        print_time_str = current_job[4] if len(current_job) > 4 else None

        now_ts = time.time()
        bed_temp = st._temp_cache_print['bed']
        nozzle_temp = st._temp_cache_print['nozzle']
        target_bed = st._temp_cache_print['target_bed']
        target_nozzle = st._temp_cache_print['target_nozzle']

        temp_response = None
        if TEMP_CHECK_INTERVAL_PRINT_SEC <= 0 or (now_ts - st._temp_last_check_print_ts) >= TEMP_CHECK_INTERVAL_PRINT_SEC:
            st._temp_last_check_print_ts = now_ts
            temp_response = printer_send_gcode('M105')

        if temp_response and 'T:' in temp_response:
            try:
                for line in temp_response.split('\n'):
                    if 'T:' in line:
                        t_match = re.search(r'T:(\d+\.?\d*)\s*/(\d+\.?\d*)', line)
                        if t_match:
                            nozzle_temp = float(t_match.group(1))
                            target_nozzle = float(t_match.group(2))
                        b_match = re.search(r'B:(\d+\.?\d*)\s*/(\d+\.?\d*)', line)
                        if b_match:
                            bed_temp = float(b_match.group(1))
                            target_bed = float(b_match.group(2))
                        break
            except Exception as e:
                print(f"⚠️ Erro ao parsear temperatura: {e}")

        st._temp_cache_print = {
            'bed': bed_temp,
            'nozzle': nozzle_temp,
            'target_bed': target_bed,
            'target_nozzle': target_nozzle,
        }

        time_elapsed = '00:00:00'
        time_remaining = 'Calculando...'
        if started_at:
            try:
                start_time = datetime.strptime(started_at, '%Y-%m-%d %H:%M:%S')
                elapsed = datetime.now() - start_time
                hours = int(elapsed.total_seconds() // 3600)
                minutes = int((elapsed.total_seconds() % 3600) // 60)
                seconds = int(elapsed.total_seconds() % 60)
                time_elapsed = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

                if print_time_str and current_progress > 0:
                    file_total_seconds = 0
                    h_match = re.search(r'(\d+)h', print_time_str)
                    m_match = re.search(r'(\d+)m', print_time_str)
                    s_match = re.search(r'(\d+)s', print_time_str)

                    if h_match:
                        file_total_seconds += int(h_match.group(1)) * 3600
                    if m_match:
                        file_total_seconds += int(m_match.group(1)) * 60
                    if s_match:
                        file_total_seconds += int(s_match.group(1))

                    if file_total_seconds > 0:
                        if current_progress < 10:
                            remaining = file_total_seconds - elapsed.total_seconds()
                        else:
                            progress_based_total = elapsed.total_seconds() / (current_progress / 100)
                            file_weight = max(0, (50 - current_progress) / 50)
                            progress_weight = 1 - file_weight
                            weighted_total = (file_total_seconds * file_weight) + (progress_based_total * progress_weight)
                            remaining = weighted_total - elapsed.total_seconds()

                        if remaining > 0:
                            r_hours = int(remaining // 3600)
                            r_minutes = int((remaining % 3600) // 60)
                            r_seconds = int(remaining % 60)
                            time_remaining = f"{r_hours:02d}:{r_minutes:02d}:{r_seconds:02d}"
                        else:
                            time_remaining = '00:00:00'
                    else:
                        if current_progress > 0:
                            total_time = elapsed.total_seconds() / (current_progress / 100)
                            remaining = total_time - elapsed.total_seconds()
                            if remaining > 0:
                                r_hours = int(remaining // 3600)
                                r_minutes = int((remaining % 3600) // 60)
                                r_seconds = int(remaining % 60)
                                time_remaining = f"{r_hours:02d}:{r_minutes:02d}:{r_seconds:02d}"
                            else:
                                time_remaining = '00:00:00'
                        else:
                            time_remaining = '00:00:00'
            except Exception as e:
                print(f"⚠️ Erro ao calcular tempo: {e}, started_at={started_at}")

        if st.printing_in_progress and st.print_failure_detected:
            state = 'failure'
        elif st.printing_in_progress and st.print_paused:
            state = 'paused'
        else:
            state = 'printing'

        status = {
            'connected': st.printer_serial and st.printer_serial.is_open,
            'temperature': {
                'bed': bed_temp,
                'nozzle': nozzle_temp,
                'target_bed': target_bed,
                'target_nozzle': target_nozzle
            },
            'state': state,
            'progress': current_progress,
            'filename': current_filename,
            'time_elapsed': time_elapsed,
            'time_remaining': time_remaining,
            'filament': check_filament_sensor(during_print=True),
            'failure_detected': st.print_failure_detected,
            'failure_message': st.current_failure_message,
            'failure_code': st.current_failure_code,
            'skipped_objects_count': skipped_count,
        }
        return jsonify({'success': True, 'status': status})

    status_data = get_printer_status_serial()
    filament_info = check_filament_sensor()

    status = {
        'connected': status_data['connected'],
        'temperature': {
            'bed': status_data['bed_temp'],
            'nozzle': status_data['nozzle_temp'],
            'target_bed': status_data['target_bed_temp'],
            'target_nozzle': status_data['target_nozzle_temp']
        },
        'state': 'idle',
        'progress': 0,
        'filename': '',
        'time_elapsed': '00:00:00',
        'time_remaining': '00:00:00',
        'filament': filament_info,
        'failure_detected': False,
        'failure_message': None,
        'failure_code': None,
        'skipped_objects_count': 0,
    }
    return jsonify({'success': True, 'status': status})


@printer_bp.route('/api/printer/failure', methods=['POST'])
def printer_failure():
    """Recebe notificação de falha (ex.: OctoPrint). Pausa a impressão e aguarda ação: resolver/skip/cancelar."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401

    data = request.get_json(silent=True) or {}
    message = data.get('message') or 'Falha detectada na impressão'
    code = data.get('code')
    st.print_failure_detected = True
    st.current_failure_message = message
    st.current_failure_code = code
    st.print_paused = True
    print(f"⚠️ Falha detectada: {message}" + (f" (código: {code})" if code else ""))
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute(
            'SELECT id FROM print_jobs WHERE status = ? ORDER BY started_at DESC LIMIT 1',
            ('printing',)
        )
        row = cur.fetchone()
        if row:
            cur.execute('''
                INSERT INTO print_failure_log (print_job_id, failure_code, failure_message, action)
                VALUES (?, ?, ?, ?)
            ''', (row[0], code, message, 'detected'))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️ Erro ao registrar falha no log: {e}")
    return jsonify({'success': True, 'message': 'Falha registrada; aguardando ação'})


@printer_bp.route('/api/printer/failure/resolve', methods=['POST'])
def printer_failure_resolve():
    """Marca que o usuário foi resolver o problema (feedback para UI/histórico)."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    return jsonify({'success': True, 'message': 'Aguardando problema resolvido'})


@printer_bp.route('/api/printer/failure/resolved', methods=['POST'])
def printer_failure_resolved():
    """Problema resolvido: limpa falha e retoma a impressão (mesmo que resume)."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    st.print_failure_detected = False
    st.current_failure_message = None
    st.current_failure_code = None
    st.print_paused = False
    return jsonify({'success': True, 'message': 'Problema resolvido; retomando impressão'})


@printer_bp.route('/api/printer/skip-object', methods=['POST'])
def printer_skip_object():
    """Pular item com defeito: avança no G-code até o próximo objeto sem enviar (não consome filamento)."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401

    data = request.get_json(silent=True) or {}
    object_id = data.get('object_id')
    st.skip_object_id = object_id
    st.skip_requested = True
    st.print_failure_detected = False
    st.current_failure_message = None
    st.current_failure_code = None
    st.print_paused = False

    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute(
            'SELECT id FROM print_jobs WHERE status = ? ORDER BY started_at DESC LIMIT 1',
            ('printing',)
        )
        row = cur.fetchone()
        if row:
            cur.execute('''
                INSERT INTO print_failure_log (print_job_id, failure_message, action, object_index_or_name)
                VALUES (?, ?, ?, ?)
            ''', (row[0], 'Pular item solicitado pelo usuário', 'skipped', str(object_id) if object_id is not None else None))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️ Erro ao registrar skip no log: {e}")

    print("⏭️ Skip de objeto solicitado; thread avançará até o próximo objeto")
    return jsonify({'success': True, 'message': 'Pulando item; impressão continuará no próximo objeto'})


@printer_bp.route('/api/printer/failure-history', methods=['GET'])
def printer_failure_history():
    """Lista últimas entradas do log de falhas (para o job atual ou gerais)."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    limit = min(int(request.args.get('limit', 50)), 100)
    print_job_id = request.args.get('print_job_id')
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if print_job_id:
        cur.execute('''
            SELECT id, print_job_id, occurred_at, failure_code, failure_message, action, object_index_or_name
            FROM print_failure_log WHERE print_job_id = ? ORDER BY occurred_at DESC LIMIT ?
        ''', (int(print_job_id), limit))
    else:
        cur.execute('''
            SELECT id, print_job_id, occurred_at, failure_code, failure_message, action, object_index_or_name
            FROM print_failure_log ORDER BY occurred_at DESC LIMIT ?
        ''', (limit,))
    rows = cur.fetchall()
    conn.close()
    entries = [
        {
            'id': r['id'],
            'print_job_id': r['print_job_id'],
            'occurred_at': r['occurred_at'],
            'failure_code': r['failure_code'],
            'failure_message': r['failure_message'],
            'action': r['action'],
            'object_index_or_name': r['object_index_or_name'],
        }
        for r in rows
    ]
    return jsonify({'success': True, 'entries': entries})


@printer_bp.route('/api/printer/bed-preview', methods=['GET'])
def printer_bed_preview():
    """Retorna dimensões da mesa e lista de objetos do G-code atual (para visualização e escolher peça a pular)."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT pj.filename
        FROM print_jobs pj
        WHERE pj.status = ?
        ORDER BY pj.started_at DESC
        LIMIT 1
    ''', ('printing',))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'success': True, 'bed': {'width_mm': BED_WIDTH_MM, 'depth_mm': BED_DEPTH_MM}, 'objects': []})
    original_name = row[0]
    cursor.execute(
        'SELECT filename FROM gcode_files WHERE original_name = ? AND user_id = ?',
        (original_name, session['user_id'])
    )
    file_row = cursor.fetchone()
    conn.close()
    if not file_row:
        return jsonify({'success': True, 'bed': {'width_mm': BED_WIDTH_MM, 'depth_mm': BED_DEPTH_MM}, 'objects': []})
    filepath = os.path.join(flask_app.config['GCODE_FOLDER'], file_row[0])
    if not os.path.isfile(filepath):
        return jsonify({'success': True, 'bed': {'width_mm': BED_WIDTH_MM, 'depth_mm': BED_DEPTH_MM}, 'objects': []})
    objects = parse_gcode_objects_for_bed(filepath)
    out = []
    for o in objects:
        out.append({
            'id': o['id'],
            'name': o.get('name'),
            'min_x': round(o['min_x'], 2) if o.get('min_x') is not None else None,
            'min_y': round(o['min_y'], 2) if o.get('min_y') is not None else None,
            'max_x': round(o['max_x'], 2) if o.get('max_x') is not None else None,
            'max_y': round(o['max_y'], 2) if o.get('max_y') is not None else None,
        })
    return jsonify({
        'success': True,
        'bed': {'width_mm': BED_WIDTH_MM, 'depth_mm': BED_DEPTH_MM},
        'objects': out,
    })


@printer_bp.route('/api/printer/pause', methods=['POST'])
def printer_pause():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401

    option = 'keep_temp'
    data = request.get_json(silent=True) or {}
    if data.get('option') in ('keep_temp', 'cold', 'filament_change'):
        option = data['option']
    st.pause_option_requested = option
    st.print_paused = True
    st.print_paused_by_filament = False
    print(f"⏸️ Impressão pausada (opção: {option})")
    return jsonify({'success': True, 'message': 'Impressão pausada', 'option': option})


@printer_bp.route('/api/printer/resume', methods=['POST'])
def printer_resume():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401

    st.print_failure_detected = False
    st.current_failure_message = None
    st.current_failure_code = None

    target_nozzle = 0
    target_bed = 0
    pause_option = 'keep_temp'
    pos_x = pos_y = pos_z = None
    state_loaded = False

    if st.current_pause_state_job_id:
        try:
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute(
                'SELECT target_nozzle, target_bed, pause_option, pos_x, pos_y, pos_z FROM print_pause_state WHERE print_job_id = ? ORDER BY id DESC LIMIT 1',
                (st.current_pause_state_job_id,)
            )
            row = cur.fetchone()
            conn.close()
            if row:
                target_nozzle = row[0] or 0
                target_bed = row[1] or 0
                pause_option = row[2] or 'keep_temp'
                pos_x, pos_y, pos_z = row[3], row[4], row[5]
                state_loaded = True
                print(f"  📋 Estado de pausa carregado do banco (opção: {pause_option})")
        except Exception as e:
            print(f"  ⚠️ Erro ao carregar estado de pausa do banco: {e}")

    if not state_loaded and st._pause_mem_state.get('valid'):
        target_nozzle = st._pause_mem_state.get('target_nozzle', 0)
        target_bed = st._pause_mem_state.get('target_bed', 0)
        pause_option = st._pause_mem_state.get('option', 'keep_temp')
        pos_x = st._pause_mem_state.get('pos_x')
        pos_y = st._pause_mem_state.get('pos_y')
        pos_z = st._pause_mem_state.get('pos_z')
        state_loaded = True
        print(f"  📋 Estado de pausa carregado da memória (opção: {pause_option})")

    if state_loaded:
        try:
            if target_nozzle > 0 or target_bed > 0:
                temp_resp = printer_send_gcode('M105')
                cur_nozzle, cur_bed = parse_m105_temps(temp_resp)

                if pause_option == 'cold':
                    need_heat_nozzle = target_nozzle > 0
                    need_heat_bed = target_bed > 0
                else:
                    need_heat_nozzle = target_nozzle > 0 and (cur_nozzle is None or cur_nozzle < target_nozzle - TEMP_REHEAT_MARGIN)
                    need_heat_bed = target_bed > 0 and (cur_bed is None or cur_bed < target_bed - TEMP_REHEAT_MARGIN)

                if need_heat_bed:
                    print(f"  🔥 Reaquecendo mesa para {int(target_bed)}°C...")
                    printer_send_gcode(f'M140 S{int(target_bed)}')
                    printer_send_gcode(f'M190 S{int(target_bed)}', timeout=300)
                if need_heat_nozzle:
                    print(f"  🔥 Reaquecendo bico para {int(target_nozzle)}°C...")
                    printer_send_gcode(f'M104 S{int(target_nozzle)}')
                    printer_send_gcode(f'M109 S{int(target_nozzle)}', timeout=300)
                if need_heat_nozzle or need_heat_bed:
                    print("  🔥 Reaquecimento concluído (retomada)")
        except Exception as heat_e:
            print(f"  ⚠️ Erro no reaquecimento: {heat_e}")

        if pos_x is not None and pos_y is not None and pos_z is not None:
            try:
                printer_send_gcode('G90')
                printer_send_gcode(f'G0 X{pos_x:.2f} Y{pos_y:.2f} F3000')
                printer_send_gcode(f'G0 Z{pos_z:.2f} F300')
                printer_send_gcode('G91')
                printer_send_gcode(f'G1 E{PAUSE_RETRACT_MM:.2f} F300')
                printer_send_gcode('G90')
                print("  📍 Retorno à posição de impressão (unpark)")
            except Exception as e:
                print(f"  ⚠️ Erro no unpark: {e}")
    else:
        print("  ⚠️ Nenhum estado de pausa encontrado — retomando sem reaquecimento/unpark")

    st._pause_mem_state['valid'] = False

    st.print_paused = False
    st.print_paused_by_filament = False
    st.current_pause_state_job_id = None
    print("▶️ Impressão retomada")
    return jsonify({'success': True, 'message': 'Impressão retomada'})


@printer_bp.route('/api/printer/connect', methods=['POST'])
def printer_connect():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401

    if connect_printer():
        return jsonify({'success': True, 'message': 'Impressora conectada com sucesso'})
    else:
        return jsonify({'success': False, 'message': 'Falha ao conectar à impressora'}), 500


@printer_bp.route('/api/printer/disconnect', methods=['POST'])
def printer_disconnect():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401

    disconnect_printer()
    return jsonify({'success': True, 'message': 'Impressora desconectada'})


@printer_bp.route('/api/printer/stop', methods=['POST'])
def printer_stop():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401

    st.print_stopped = True
    st.print_paused = False
    st.print_failure_detected = False
    st.current_failure_message = None
    st.current_failure_code = None
    st._pause_mem_state['valid'] = False

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE print_jobs 
        SET status = 'cancelled', completed_at = CURRENT_TIMESTAMP
        WHERE status = 'printing'
    ''')
    conn.commit()
    conn.close()

    printer_send_gcode('M104 S0')
    printer_send_gcode('M140 S0')
    printer_send_gcode('M107')
    printer_send_gcode('G91')
    printer_send_gcode('G1 Z10')
    printer_send_gcode('G90')
    printer_send_gcode('G28 X Y')

    print("✗ Impressão PARADA pelo usuário")

    return jsonify({'success': True, 'message': 'Impressão parada'})


@printer_bp.route('/api/printer/start', methods=['POST'])
def printer_start():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401

    data = request.get_json()
    filename = data.get('filename')

    return jsonify({'success': True, 'message': f'Impressão iniciada: {filename}'})


@printer_bp.route('/api/printer/gcode', methods=['POST'])
def send_gcode_api():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401

    data = request.get_json()
    command = data.get('command', '').strip()

    if not command:
        return jsonify({'success': False, 'message': 'Comando vazio'}), 400

    with history_lock:
        commands_history.append({
            'timestamp': datetime.now().isoformat(),
            'command': command,
            'type': 'sent'
        })

    response = printer_send_gcode(command)

    if response is not None:
        with history_lock:
            commands_history.append({
                'timestamp': datetime.now().isoformat(),
                'command': response,
                'type': 'response'
            })
        return jsonify({'success': True, 'response': response})
    else:
        return jsonify({'success': False, 'message': 'Sem resposta da impressora'}), 500


@printer_bp.route('/api/printer/commands-history', methods=['GET'])
def get_commands_history():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401

    with history_lock:
        history = list(commands_history)

    return jsonify({
        'success': True,
        'history': history,
        'count': len(history)
    })


@printer_bp.route('/api/printer/select-brush', methods=['POST'])
def select_brush():
    """Seleciona um pincel (extrusor T0-T18)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401

    try:
        data = request.get_json()
        brush = int(data.get('brush', 0))

        if brush < 0 or brush > 18:
            return jsonify({'success': False, 'message': 'Pincel inválido (T0-T18)'}), 400

        command = f'T{brush}'
        response = printer_send_gcode(command, wait_for_ok=True, timeout=10)

        if response:
            st.current_brush = brush
            print(f"✓ Pincel T{brush} selecionado")
            return jsonify({
                'success': True,
                'message': f'Pincel T{brush} selecionado',
                'brush': brush
            })
        else:
            return jsonify({'success': False, 'message': 'Erro ao enviar comando para impressora'}), 500

    except ValueError:
        return jsonify({'success': False, 'message': 'Formato de pincel inválido'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@printer_bp.route('/api/printer/current-brush', methods=['GET'])
def get_current_brush():
    """Retorna o pincel atualmente selecionado"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401

    return jsonify({
        'success': True,
        'brush': st.current_brush
    })


@printer_bp.route('/api/printer/send-mixture', methods=['POST'])
def send_mixture():
    """Envia comando M182 de mistura de filamentos"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401

    try:
        data = request.get_json()
        command = data.get('command', '').strip()

        if not command:
            return jsonify({'success': False, 'message': 'Comando vazio'}), 400

        if not command.startswith('M182'):
            return jsonify({'success': False, 'message': 'Comando inválido. Deve ser M182'}), 400

        response = printer_send_gcode(command, wait_for_ok=True, timeout=10)

        if response:
            print(f"✓ Mistura enviada: {command}")
            return jsonify({
                'success': True,
                'message': f'Mistura enviada: {command}',
                'response': response
            })
        else:
            return jsonify({'success': False, 'message': 'Erro ao enviar comando para impressora'}), 500

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@printer_bp.route('/api/printer/save-brush-mixtures', methods=['POST'])
def save_brush_mixtures():
    """Salva as misturas e cores de todos os pincéis no banco de dados"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401

    try:
        data = request.get_json()
        mixtures = data.get('mixtures', {})
        colors = data.get('colors', {})
        tintaColors = data.get('tintaColors', {})

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        for brush_index, mixture in mixtures.items():
            try:
                brush_id = int(brush_index)
                if 0 <= brush_id <= 18:
                    custom_color = colors.get(brush_index, None)
                    tinta_color = tintaColors.get(brush_index, None)
                    cursor.execute("""
                        INSERT OR REPLACE INTO brush_mixtures (brush_id, a_percent, b_percent, c_percent, custom_color, tinta_color, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (brush_id, mixture['a'], mixture['b'], mixture['c'], custom_color, tinta_color))
            except (ValueError, KeyError):
                continue

        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Misturas e cores salvas com sucesso'})

    except Exception as e:
        print(f"Erro ao salvar misturas: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@printer_bp.route('/api/printer/load-brush-mixtures', methods=['GET'])
def load_brush_mixtures():
    """Carrega as misturas e cores de todos os pincéis do banco de dados"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401

    try:
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT brush_id, a_percent, b_percent, c_percent, custom_color, tinta_color FROM brush_mixtures")
            rows = cursor.fetchall()
            conn.close()

            mixtures = {}
            colors = {}
            tintaColors = {}
            for row in rows:
                mixtures[str(row[0])] = {
                    'a': row[1],
                    'b': row[2],
                    'c': row[3]
                }
                if row[4]:
                    colors[str(row[0])] = row[4]
                if row[5]:
                    tintaColors[str(row[0])] = row[5]

            if mixtures:
                return jsonify({'success': True, 'mixtures': mixtures, 'colors': colors, 'tintaColors': tintaColors})
        except:
            pass

        default_mixtures = {}
        for i in range(19):
            default_mixtures[str(i)] = {'a': 33, 'b': 33, 'c': 34}

        return jsonify({'success': True, 'mixtures': default_mixtures, 'colors': {}})

    except Exception as e:
        print(f"Erro ao carregar misturas: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@printer_bp.route('/api/filament/status', methods=['GET'])
def filament_status_api():
    """Retorna status do sensor de filamento"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401

    status = check_filament_sensor(during_print=st.printing_in_progress)
    return jsonify({
        'success': True,
        'filament': status
    })


@printer_bp.route('/api/filament/debug', methods=['GET'])
def filament_debug_api():
    """Diagnóstico do sensor de filamento (especialmente para modo Marlin/M119)."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401

    force = request.args.get('force', '').strip() in ('1', 'true', 'True', 'yes', 'YES')
    debug = {
        'mode': FILAMENT_SENSOR_MODE,
        'check_interval_sec': FILAMENT_CHECK_INTERVAL_SEC,
        'check_interval_print_sec': FILAMENT_CHECK_INTERVAL_PRINT_SEC,
        'm119_during_print': FILAMENT_M119_DURING_PRINT,
        'invert': MARLIN_FILAMENT_INVERT,
        'printing_in_progress': st.printing_in_progress,
    }

    if force:
        st._filament_last_check_idle_ts = 0.0
        st._filament_last_check_print_ts = 0.0
        debug['cache_bypassed'] = True
    else:
        debug['cache_bypassed'] = False

    status = check_filament_sensor()
    debug['status'] = status

    if FILAMENT_SENSOR_MODE == 'marlin':
        try:
            raw_m119 = printer_send_gcode('M119', wait_for_ok=True, timeout=5, retries=1)
        except Exception as e:
            raw_m119 = None
            debug['m119_error'] = str(e)

        debug['m119_raw'] = raw_m119
        debug['m119_candidates'] = _extract_marlin_m119_candidates(raw_m119 or '')
        debug['m119_parsed_has_filament'] = _parse_marlin_m119_for_filament(raw_m119 or '')

    return jsonify({'success': True, 'debug': debug})
