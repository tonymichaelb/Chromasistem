"""Serial connection management and printer communication."""

import time
import re
import serial
from datetime import datetime

from core.config import (SERIAL_PORT, SERIAL_BAUDRATE, SERIAL_TIMEOUT,
                         serial_lock, commands_history, history_lock)
import core.state as st


_CRITICAL_ERROR_PATTERNS = (
    'error:',
    '!! ',
    'printer halted',
    'kill() called',
    'thermal runaway',
    'heating failed',
    'mintemp triggered',
    'maxtemp triggered',
    'probing failed',
    'homing failed',
    'stop called',
    'emergency stop',
)

_FALSE_POSITIVE_FRAGMENTS = (
    'error:checksum',
    'error:line number',
    'error:no line number',
    'format error',
    'error:no checksum',
)


def _maybe_mark_failure_from_printer_line(line: str) -> bool:
    """Detecta mensagens de erro critico do firmware (Marlin/RepRap) no fluxo serial.

    Retorna True se uma falha critica foi detectada.
    So dispara durante impressao ativa para evitar falsos positivos em comandos avulsos.
    """
    if not line or not st.printing_in_progress:
        return False

    if st.print_failure_detected:
        return False

    low = line.strip().lower()

    if any(fp in low for fp in _FALSE_POSITIVE_FRAGMENTS):
        return False

    matched_pattern = None
    for pattern in _CRITICAL_ERROR_PATTERNS:
        if pattern in low:
            matched_pattern = pattern
            break

    if not matched_pattern:
        return False

    error_msg = line.strip()
    if len(error_msg) > 200:
        error_msg = error_msg[:200] + '...'

    code = 'FIRMWARE'
    if 'thermal runaway' in low:
        code = 'THERMAL_RUNAWAY'
    elif 'mintemp' in low:
        code = 'MINTEMP'
    elif 'maxtemp' in low:
        code = 'MAXTEMP'
    elif 'heating failed' in low:
        code = 'HEATING_FAILED'
    elif 'halted' in low or 'kill' in low:
        code = 'HALTED'
    elif 'homing' in low:
        code = 'HOMING_FAILED'
    elif 'probing' in low:
        code = 'PROBING_FAILED'
    elif 'emergency' in low or 'stop called' in low:
        code = 'EMERGENCY_STOP'

    st.print_failure_detected = True
    st.current_failure_message = error_msg
    st.current_failure_code = code
    st.print_paused = True

    print(f"🚨 FALHA DETECTADA NA IMPRESSORA: [{code}] {error_msg}")

    return True


def connect_printer():
    try:
        if st.printer_serial and st.printer_serial.is_open:
            print(f"✓ Já conectado à impressora em {SERIAL_PORT}")
            return True

        import os
        if not os.path.exists(SERIAL_PORT):
            print(f"✗ ERRO: Porta {SERIAL_PORT} não existe!")
            print("   Portas disponíveis:")
            try:
                import glob
                ports = glob.glob('/dev/tty[AU]*')
                for port in ports:
                    print(f"     - {port}")
            except:
                pass
            return False

        print(f"🔌 Tentando conectar à impressora...")
        print(f"   Porta: {SERIAL_PORT}")
        print(f"   Baudrate: {SERIAL_BAUDRATE}")
        print(f"   Timeout: {SERIAL_TIMEOUT}s")

        st.printer_serial = serial.Serial(
            port=SERIAL_PORT,
            baudrate=SERIAL_BAUDRATE,
            timeout=SERIAL_TIMEOUT,
            write_timeout=SERIAL_TIMEOUT,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False
        )

        print(f"   Aguardando inicialização da impressora...")
        time.sleep(2)

        try:
            st.printer_serial.write(b'M115\n')
            time.sleep(0.5)
            response = st.printer_serial.readline().decode('utf-8', errors='ignore').strip()
            if response:
                print(f"   Resposta da impressora: {response[:50]}...")
        except Exception as e:
            print(f"   Aviso ao verificar resposta: {e}")

        print(f"✓ Conectado à impressora em {SERIAL_PORT} @ {SERIAL_BAUDRATE} baud")
        return True
    except serial.SerialException as e:
        print(f"✗ ERRO Serial: {e}")
        if 'Permission denied' in str(e):
            print("   SOLUÇÃO: Execute 'sudo usermod -a -G dialout $USER' e faça logout/login")
            print("   OU execute o servidor com sudo")
        elif 'Device or resource busy' in str(e):
            print("   SOLUÇÃO: Outra aplicação está usando a porta. Feche-a primeiro.")
        st.printer_serial = None
        return False
    except Exception as e:
        print(f"✗ Erro inesperado ao conectar impressora: {type(e).__name__}: {e}")
        st.printer_serial = None
        return False


def disconnect_printer():
    try:
        if st.printer_serial and st.printer_serial.is_open:
            st.printer_serial.close()
            print("✓ Impressora desconectada")
    except Exception as e:
        print(f"Erro ao desconectar: {e}")
    finally:
        st.printer_serial = None


def _truncate_cmd(cmd: str, max_len: int = 76) -> str:
    s = cmd.strip()
    if len(s) <= max_len:
        return s
    return s[: max_len - 2] + "…"


def _resp_preview(full_resp: str, max_len: int = 96) -> str:
    preview = full_resp.replace("\n", " │ ")
    if len(preview) > max_len:
        return preview[: max_len - 1] + "…"
    return preview


def describe_gcode(cmd_line: str) -> str:
    """Breve descrição em PT-BR do efeito do comando G-code (para logs)."""
    raw = (cmd_line or "").split(";")[0].strip()
    if not raw:
        return "—"
    parts = raw.upper().split()
    head = parts[0] if parts else ""

    def num_after(prefix: str):
        for p in parts:
            if p.startswith(prefix):
                try:
                    return int(float(p[len(prefix) :]))
                except ValueError:
                    try:
                        return float(p[len(prefix) :])
                    except ValueError:
                        pass
        return None

    if re.match(r"^T\d+$", head):
        return f"Selecionar extrusora {head[1:]}"

    if head == "G20":
        return "Unidades: polegadas"
    if head == "G21":
        return "Unidades: milímetros"
    if head == "G28":
        return "Homing (referência dos eixos)"
    if head == "G29":
        return "Nivelamento automático da mesa (mesh)"
    if head == "G90":
        return "Posicionamento absoluto"
    if head == "G91":
        return "Posicionamento relativo"
    if head.startswith("G4"):
        s = num_after("S")
        if s is not None:
            ss = int(s) if float(s) == int(float(s)) else s
            return f"Pausa na sequência (dwell {ss} s)"
        p = num_after("P")
        if p is not None:
            return f"Pausa na sequência (dwell {p} ms)"
        return "Pausa na sequência (dwell)"

    ru = raw.upper()
    if head.startswith("G0") or (head == "G0" and len(parts) > 1):
        return _describe_move(ru, rapid=True)
    if head.startswith("G1") or (head == "G1" and len(parts) > 1):
        return _describe_move(ru, rapid=False)

    if head == "M104":
        t = num_after("S")
        return (
            f"Definir temperatura do bico (sem aguardar){f' → {t}°C' if t is not None else ''}"
        )
    if head == "M109":
        t = num_after("S")
        return f"Aquecer bico e aguardar temperatura{f' → {t}°C' if t is not None else ''}"
    if head == "M140":
        t = num_after("S")
        return (
            f"Definir temperatura da mesa (sem aguardar){f' → {t}°C' if t is not None else ''}"
        )
    if head == "M190":
        t = num_after("S")
        return f"Aquecer mesa e aguardar temperatura{f' → {t}°C' if t is not None else ''}"
    if head == "M105":
        return "Ler temperaturas (bico e mesa)"
    if head == "M115":
        return "Informações do firmware"
    if head == "M114":
        return "Ler posição atual dos eixos"
    if head == "M119":
        return "Ler fim de curso"
    if head == "M106":
        return "Ligar ventoinha de arrefecimento"
    if head == "M107":
        return "Desligar ventoinha"
    if head == "M600":
        return "Troca de filamento (M600)"
    if head == "M84":
        return "Desligar motores (inativo)"
    if head == "M82":
        return "Extrusão em modo absoluto"
    if head == "M83":
        return "Extrusão em modo relativo"
    if head == "M201":
        return "Limites de aceleração (M201)"
    if head == "M203":
        return "Velocidades máximas dos eixos (M203)"
    if head == "M204":
        return "Aceleração P/R/T (M204)"
    if head == "M205":
        return "Jerk (M205)"
    if head.startswith("M"):
        return f"Comando auxiliar {head}"

    if head.startswith("G"):
        return f"Comando de movimento {head}"

    return "G-code"


def _describe_move(u: str, rapid: bool) -> str:
    has_e = bool(re.search(r"\bE[-\d.]+", u))
    axes = []
    for ax in ("X", "Y", "Z"):
        if ax + ":" in u or re.search(rf"\b{ax}[-\d.]+", u):
            axes.append(ax)
    if has_e:
        axes.append("extrusão")
    base = "Movimento rápido (G0)" if rapid else "Movimento linear (G1)"
    if axes:
        return f"{base}: {', '.join(axes)}"
    return base


def check_printer_ready():
    """Envia M115 (firmware info) e verifica se impressora responde ok"""
    try:
        print("  Verificando impressora (M115)...")
        response = send_gcode('M115', wait_for_ok=True, timeout=10)
        if response and 'ok' in response.lower():
            print("  ✓ Impressora pronta para imprimir")
            return True
        else:
            print("  ✗ Impressora não respondeu ao M115")
            return False
    except Exception as e:
        print(f"  ✗ Erro ao verificar prontidão: {e}")
        return False


def send_gcode(command, wait_for_ok=True, timeout=None, retries=1):
    with serial_lock:
        for attempt in range(retries):
            try:
                if not st.printer_serial or not st.printer_serial.is_open:
                    if not connect_printer():
                        return None

                if not command.endswith('\n'):
                    command += '\n'

                cmd = command.strip().upper()

                if timeout is None:
                    if cmd.startswith('G28'):
                        timeout = 60
                    elif cmd.startswith('G29'):
                        timeout = 120
                    elif cmd.startswith('M109') or cmd.startswith('M190'):
                        timeout = 300
                    elif cmd.startswith('T'):
                        timeout = 10
                    elif cmd.startswith(('G0 ', 'G1 ')) and ' E' in cmd:
                        timeout = 10
                    elif cmd.startswith(('G0 ', 'G1 ')):
                        timeout = 10
                    else:
                        timeout = 5

                if not cmd.startswith(('G0 ', 'G1 ')):
                    try:
                        st.printer_serial.reset_input_buffer()
                    except:
                        pass
                    time.sleep(0.01)

                desc = describe_gcode(command)
                cmd_show = _truncate_cmd(command.strip())
                print(f"➡️  [{timeout:.0f}s] {desc} → {cmd_show}")
                st.printer_serial.write(command.encode())
                st.printer_serial.flush()

                with history_lock:
                    commands_history.append({
                        'time': datetime.now().isoformat(),
                        'command': command.strip(),
                        'type': 'sent'
                    })

                if not wait_for_ok:
                    print("   ← ok (sem aguardar resposta)")
                    return 'ok'

                responses = []
                start_time = time.time()

                while time.time() - start_time < timeout:
                    if st.printer_serial.in_waiting > 0:
                        line = st.printer_serial.readline().decode('utf-8', errors='ignore').strip()
                        if line:
                            try:
                                from core.filament import _maybe_mark_filament_runout_from_printer_line
                                _maybe_mark_filament_runout_from_printer_line(line)
                            except Exception:
                                pass

                            _maybe_mark_failure_from_printer_line(line)

                            responses.append(line)
                            if 'ok' in line.lower():
                                full_resp = '\n'.join(responses)
                                with history_lock:
                                    commands_history.append({
                                        'time': datetime.now().isoformat(),
                                        'command': full_resp,
                                        'type': 'response'
                                    })
                                print("   ← ok")
                                return full_resp
                    else:
                        time.sleep(0.01)

                if attempt < retries - 1:
                    print(
                        f"   ⚠ timeout ({timeout:.0f}s) · nova tentativa "
                        f"{attempt + 2}/{retries} · {describe_gcode(command)}"
                    )
                    time.sleep(0.5)
                    continue

                if responses:
                    full_resp = '\n'.join(responses)
                    print(f"   ← sem linha 'ok' ({timeout:.0f}s) · {_resp_preview(full_resp)}")
                    return full_resp
                else:
                    print(
                        f"   ✗ sem resposta ({timeout:.0f}s) · {describe_gcode(command)} "
                        f"→ {_truncate_cmd(command.strip(), 60)}"
                    )
                    return None
            except (OSError, serial.SerialException) as e:
                print(f"   ✗ serial · {describe_gcode(command)} — {e}")
                try:
                    if st.printer_serial:
                        st.printer_serial.close()
                except Exception:
                    pass
                st.printer_serial = None
                return None
            except Exception as e:
                if attempt < retries - 1:
                    print(
                        f"   ⚠ erro · {describe_gcode(command)} · "
                        f"tentativa {attempt + 2}/{retries} — {e}"
                    )
                    time.sleep(0.5)
                    continue
                print(f"   ✗ {describe_gcode(command)} — {e}")
                return None

        return None


def parse_m105_temps(response):
    """Extrai temperatura atual do bico e da mesa da resposta do M105 (Marlin: T:atual/alvo B:atual/alvo)."""
    if not response:
        return None, None
    cur_n = cur_b = None
    for line in (response or '').split('\n'):
        if 'T:' in line:
            m = re.search(r'T:\s*([\d.]+)\s*/\s*[\d.]+', line)
            if m:
                cur_n = float(m.group(1))
        if 'B:' in line:
            m = re.search(r'B:\s*([\d.]+)\s*/\s*[\d.]+', line)
            if m:
                cur_b = float(m.group(1))
    return cur_n, cur_b


def get_current_position():
    """Obtém posição atual X,Y,Z,E em mm via M114 (Marlin). Retorna dict com x, y, z, e ou None.
    Ignora 'Count' (steps) para não confundir Z em mm com Z em steps."""
    resp = send_gcode('M114', wait_for_ok=True, timeout=5)
    if not resp:
        return None
    # Pegar só a parte de posição lógica (até "Count" ou "|"), para não usar Z em steps
    pos_part = resp.split('Count')[0].split('|')[0].strip()
    out = {}
    for match in re.finditer(r'([XYZE]):\s*([-\d.]+)', pos_part, re.IGNORECASE):
        k = match.group(1).lower()
        if k not in out:  # primeira ocorrência só (posição em mm)
            out[k] = float(match.group(2))
    return out if out else None


def get_printer_status_serial():
    try:
        status = {
            'connected': st.printer_serial and st.printer_serial.is_open,
            'printing': False,
            'progress': 0,
            'bed_temp': 0,
            'nozzle_temp': 0,
            'target_bed_temp': 0,
            'target_nozzle_temp': 0
        }

        if not status['connected']:
            return status

        temp_response = None
        for attempt in range(2):
            temp_response = send_gcode('M105')
            if temp_response and 'T:' in temp_response:
                break
            time.sleep(0.1)

        if temp_response:
            try:
                for line in temp_response.split('\n'):
                    if 'T:' in line:
                        t_match = re.search(r'T:(\d+\.?\d*)\s*/(\d+\.?\d*)', line)
                        if t_match:
                            status['nozzle_temp'] = float(t_match.group(1))
                            status['target_nozzle_temp'] = float(t_match.group(2))

                        b_match = re.search(r'B:(\d+\.?\d*)\s*/(\d+\.?\d*)', line)
                        if b_match:
                            status['bed_temp'] = float(b_match.group(1))
                            status['target_bed_temp'] = float(b_match.group(2))
                        break
            except Exception as e:
                print(f"Erro ao parsear temperatura: {e}")
                print(f"Resposta: {temp_response}")

        # M27 (SD print status) não é suportado por muitas firmwares — progresso vem do backend quando imprimindo
        # progress_response = send_gcode('M27')
        # if progress_response and 'SD printing' in progress_response: ...

        return status
    except Exception as e:
        print(f"Erro ao obter status: {e}")
        return {
            'connected': False,
            'printing': False,
            'progress': 0,
            'bed_temp': 0,
            'nozzle_temp': 0,
            'target_bed_temp': 0,
            'target_nozzle_temp': 0
        }
