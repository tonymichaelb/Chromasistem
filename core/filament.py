"""Filament sensor code (GPIO and Marlin M119)."""

import time
import threading
from datetime import datetime
from typing import Optional

from core.config import (GPIO_AVAILABLE, FILAMENT_SENSOR_PIN, FILAMENT_SENSOR_MODE,
                         FILAMENT_CHECK_INTERVAL_SEC, FILAMENT_CHECK_INTERVAL_PRINT_SEC,
                         MARLIN_FILAMENT_INVERT, FILAMENT_M119_DURING_PRINT)
import core.state as st

if GPIO_AVAILABLE:
    from core.config import GPIO


def _maybe_mark_filament_runout_from_printer_line(line: str) -> bool:
    """Detecta mensagens de runout do Marlin no fluxo serial.

    Observação: isso NÃO faz polling. Apenas reage a mensagens que o firmware já envia.
    """
    if not line:
        return False

    l = line.strip().lower()

    runout_markers = (
        'filament runout',
        'filament_runout',
        'out of filament',
        'no filament',
        'runout',
        'action:pause',
    )
    if not any(m in l for m in runout_markers):
        return False

    if 'runout' in l and ('filament' not in l) and ('action:pause' not in l) and ('out of filament' not in l) and ('no filament' not in l):
        return False

    st.filament_status['has_filament'] = False
    st.filament_status['sensor_enabled'] = True
    st.filament_status['source'] = 'marlin'
    st.filament_status['last_check'] = datetime.now().isoformat()

    if st.printing_in_progress:
        st.print_paused_by_filament = True
        st.print_paused = True
        print("🚨 Marlin sinalizou falta de filamento (runout). Impressão pausada.")

    return True


def _extract_marlin_m119_candidates(m119_response: str):
    """Retorna candidatos detectados no M119 relacionados a filamento/runout."""
    candidates = []
    if not m119_response:
        return candidates

    for line in m119_response.split('\n'):
        l = line.strip()
        if not l or ':' not in l:
            continue

        key, value = l.split(':', 1)
        key_norm = key.strip().lower().replace(' ', '_')
        value_norm = value.strip().lower().replace(' ', '_')

        if any(k in key_norm for k in ('filament', 'runout', 'fil_runout', 'fil_runout', 'filament_runout')):
            candidates.append({'key': key_norm, 'value': value_norm, 'raw': l})

    return candidates


def _m119_value_to_has_filament(value_norm: str) -> Optional[bool]:
    if not value_norm:
        return None

    if 'not_triggered' in value_norm or 'nottriggered' in value_norm:
        return True
    if 'triggered' in value_norm:
        return False

    if value_norm in ('open',):
        return True
    if value_norm in ('closed',):
        return False

    return None


def _parse_marlin_m119_for_filament(m119_response: str) -> Optional[bool]:
    """Extrai o estado do filamento do M119 (sensor ligado na placa / Marlin)."""
    candidates = _extract_marlin_m119_candidates(m119_response)
    if not candidates:
        return None

    def score(c):
        key = c['key']
        if 'filament_runout' in key or 'fil_runout' in key or 'runout' in key:
            return 3
        if 'filament' in key:
            return 2
        return 1

    candidates.sort(key=score, reverse=True)

    for c in candidates:
        has_filament = _m119_value_to_has_filament(c['value'])
        if has_filament is None:
            continue
        if MARLIN_FILAMENT_INVERT:
            has_filament = not has_filament
        return has_filament

    return None


def setup_filament_sensor():
    """Inicializa o sensor de filamento"""
    if FILAMENT_SENSOR_MODE == 'none':
        st.filament_status['sensor_enabled'] = False
        st.filament_status['source'] = 'none'
        st.filament_status['has_filament'] = True
        print("ℹ️ Sensor de filamento desabilitado (FILAMENT_SENSOR_MODE=none)")
        return True

    if FILAMENT_SENSOR_MODE == 'marlin':
        st.filament_status['sensor_enabled'] = True
        st.filament_status['source'] = 'marlin'
        print("✓ Sensor de filamento via Marlin (M119) habilitado")
        return True

    # default: gpio
    st.filament_status['source'] = 'gpio'
    if not GPIO_AVAILABLE:
        print("⚠️ GPIO não disponível - modo gpio indisponível. Use FILAMENT_SENSOR_MODE=marlin para ler pela placa.")
        st.filament_status['sensor_enabled'] = False
        st.filament_status['has_filament'] = True
        return True

    try:
        try:
            GPIO.cleanup()
        except:
            pass

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(FILAMENT_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        st.gpio_live_updates_active = False

        try:
            GPIO.add_event_detect(
                FILAMENT_SENSOR_PIN,
                GPIO.BOTH,
                callback=filament_sensor_callback,
                bouncetime=300,
            )
            st.gpio_live_updates_active = True
        except Exception as e:
            print(f"⚠️ Falha ao ativar detecção por borda (GPIO.add_event_detect): {e}")

            if not st._gpio_poll_thread_started:
                st._gpio_poll_thread_started = True

                def _gpio_filament_poll_loop():
                    st.gpio_live_updates_active = True
                    last_value = None
                    while True:
                        try:
                            gpio_state = GPIO.input(FILAMENT_SENSOR_PIN)
                            has_filament = bool(gpio_state)

                            if last_value is None or has_filament != last_value:
                                st.filament_status['has_filament'] = has_filament
                                st.filament_status['last_check'] = datetime.now().isoformat()
                                if not has_filament:
                                    print("⚠️ ALERTA: Filamento acabou (GPIO/poll)")
                                else:
                                    print("✓ Filamento detectado (GPIO/poll)")
                                last_value = has_filament
                            else:
                                st.filament_status['last_check'] = datetime.now().isoformat()

                        except Exception:
                            pass

                        time.sleep(0.2)

                threading.Thread(target=_gpio_filament_poll_loop, daemon=True).start()

        st.filament_status['sensor_enabled'] = True
        print(f"✓ Sensor de filamento configurado no GPIO{FILAMENT_SENSOR_PIN}")
        return True
    except Exception as e:
        print(f"⚠️ Erro ao configurar sensor de filamento: {e}")
        print("   Sensor de filamento ficará desabilitado até corrigir o GPIO")
        st.filament_status['sensor_enabled'] = False
        st.filament_status['has_filament'] = True
        return True


def filament_sensor_callback(channel):
    """Callback executado quando o sensor detecta mudança"""
    gpio_state = GPIO.input(FILAMENT_SENSOR_PIN)
    has_filament = bool(gpio_state)

    st.filament_status['has_filament'] = has_filament
    st.filament_status['last_check'] = datetime.now().isoformat()

    if not has_filament:
        print("⚠️ ALERTA: Filamento acabou (GPIO)")
    else:
        print("✓ Filamento detectado (GPIO)")


def check_filament_sensor(during_print: bool = False):
    """Verifica estado atual do sensor de filamento"""
    now_ts = time.time()

    interval = FILAMENT_CHECK_INTERVAL_PRINT_SEC if during_print else FILAMENT_CHECK_INTERVAL_SEC
    last_ts = st._filament_last_check_print_ts if during_print else st._filament_last_check_idle_ts
    if interval > 0 and (now_ts - last_ts) < interval:
        return st.filament_status
    if during_print:
        st._filament_last_check_print_ts = now_ts
    else:
        st._filament_last_check_idle_ts = now_ts

    if FILAMENT_SENSOR_MODE == 'none':
        st.filament_status['sensor_enabled'] = False
        st.filament_status['source'] = 'none'
        st.filament_status['has_filament'] = True
        st.filament_status['last_check'] = datetime.now().isoformat()
        return st.filament_status

    if FILAMENT_SENSOR_MODE == 'marlin':
        st.filament_status['sensor_enabled'] = True
        st.filament_status['source'] = 'marlin'
        try:
            if during_print and st.printing_in_progress and (not st.print_paused) and (not FILAMENT_M119_DURING_PRINT):
                st.filament_status['last_check'] = datetime.now().isoformat()
                return st.filament_status

            from core.printer import send_gcode
            m119 = send_gcode('M119', wait_for_ok=True, timeout=5, retries=1)
            parsed = _parse_marlin_m119_for_filament(m119 or '')
            if parsed is not None:
                st.filament_status['has_filament'] = parsed
            st.filament_status['last_check'] = datetime.now().isoformat()
        except Exception as e:
            print(f"Erro ao ler filamento via Marlin (M119): {e}")
            st.filament_status['last_check'] = datetime.now().isoformat()
        return st.filament_status

    if not GPIO_AVAILABLE:
        st.filament_status['sensor_enabled'] = False
        st.filament_status['source'] = 'gpio'
        st.filament_status['has_filament'] = True
        st.filament_status['last_check'] = datetime.now().isoformat()
        return st.filament_status

    try:
        if during_print and st.filament_status.get('sensor_enabled') and st.gpio_live_updates_active:
            st.filament_status['last_check'] = datetime.now().isoformat()
            return st.filament_status

        gpio_state = GPIO.input(FILAMENT_SENSOR_PIN)
        st.filament_status['has_filament'] = bool(gpio_state)
        st.filament_status['last_check'] = datetime.now().isoformat()
    except Exception as e:
        print(f"Erro ao ler sensor de filamento: {e}")

    return st.filament_status
