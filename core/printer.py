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


def check_printer_ready():
    """Envia M115 (firmware info) e verifica se impressora responde ok"""
    try:
        print("  🔍 Verificando se impressora está pronta...")
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

                st.printer_serial.write(command.encode())
                st.printer_serial.flush()

                with history_lock:
                    commands_history.append({
                        'time': datetime.now().isoformat(),
                        'command': command.strip(),
                        'type': 'sent'
                    })

                if not wait_for_ok:
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
                                with history_lock:
                                    commands_history.append({
                                        'time': datetime.now().isoformat(),
                                        'command': '\n'.join(responses),
                                        'type': 'response'
                                    })
                                return '\n'.join(responses)
                    else:
                        time.sleep(0.01)

                if attempt < retries - 1:
                    print(f"  ⚠️ Timeout ao enviar '{command.strip()}', tentando novamente ({attempt + 2}/{retries})...")
                    time.sleep(0.5)
                    continue

                return '\n'.join(responses) if responses else None
            except Exception as e:
                if attempt < retries - 1:
                    print(f"  ⚠️ Erro ao enviar '{command.strip()}': {e}, tentando novamente ({attempt + 2}/{retries})...")
                    time.sleep(0.5)
                    continue
                print(f"Erro ao enviar comando '{command.strip()}': {e}")
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
    """Obtém posição atual X,Y,Z,E via M114 (Marlin). Retorna dict com x, y, z, e ou None."""
    resp = send_gcode('M114', wait_for_ok=True, timeout=5)
    if not resp:
        return None
    out = {}
    for match in re.finditer(r'([XYZE]):\s*([-\d.]+)', resp, re.IGNORECASE):
        out[match.group(1).lower()] = float(match.group(2))
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

        progress_response = send_gcode('M27')

        if progress_response and 'SD printing' in progress_response:
            try:
                match = re.search(r'(\d+)/(\d+)', progress_response)
                if match:
                    current = int(match.group(1))
                    total = int(match.group(2))
                    status['progress'] = (current / total) * 100 if total > 0 else 0
                    status['printing'] = True
            except Exception as e:
                print(f"Erro ao parsear progresso: {e}")

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
