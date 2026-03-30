"""WiFi configuration API routes."""

import json
import pathlib
import subprocess
import threading

from flask import Blueprint, jsonify, request, session

wifi_bp = Blueprint('wifi_api', __name__)

_PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
_WIFI_MANAGER = _PROJECT_ROOT / "wifi_manager.py"
_CACHE_PATH = pathlib.Path("/run/chromasistem-wifi-cache.json")
_SCAN_LOCK = threading.Lock()


def _read_wifi_cache():
    try:
        with open(_CACHE_PATH, encoding="utf-8") as f:
            data = json.load(f)
        nets = data.get("networks") or []
        ts = data.get("ts")
        err = data.get("error")
        return nets, ts, err
    except (OSError, json.JSONDecodeError, TypeError):
        return [], None, None


def _run_scan_cache_subprocess():
    subprocess.run(
        [
            "sudo",
            "/usr/bin/python3",
            str(_WIFI_MANAGER),
            "scan-cache",
        ],
        cwd=str(_PROJECT_ROOT),
        timeout=120,
        check=False,
    )


@wifi_bp.route('/api/wifi/scan', methods=['GET'])
def wifi_scan():
    """Lista redes do cache. Use ?refresh=1 para escanear (derruba AP ~20–40 s e religa)."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401

    refresh = request.args.get('refresh', '').lower() in ('1', 'true', 'yes')

    if refresh:
        if not _SCAN_LOCK.acquire(blocking=False):
            return jsonify({
                'success': True,
                'pending': True,
                'message': (
                    'Já existe uma busca em andamento. Aguarde e toque em Atualizar de novo.'
                ),
            })

        def worker():
            try:
                _run_scan_cache_subprocess()
            finally:
                _SCAN_LOCK.release()

        threading.Thread(target=worker, daemon=True).start()
        return jsonify({
            'success': True,
            'pending': True,
            'message': (
                'O Wi-Fi da impressora será reiniciado por cerca de 20–40 s. '
                'Reconecte à rede "Croma-3D-Printer" e aguarde a lista aparecer.'
            ),
        })

    networks, ts, err = _read_wifi_cache()
    body = {
        'success': True,
        'networks': networks,
        'from_cache': ts is not None,
        'cache_ts': ts,
    }
    if err:
        body['cache_error'] = err
    return jsonify(body)


@wifi_bp.route('/api/wifi/connect', methods=['POST'])
def wifi_connect():
    """Conecta a uma rede Wi-Fi"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401

    data = request.get_json()
    ssid = data.get('ssid')
    password = data.get('password', '')

    if not ssid:
        return jsonify({'success': False, 'message': 'SSID não fornecido'}), 400

    try:
        result = subprocess.run(['sudo', 'python3', 'wifi_manager.py', 'connect', ssid, password],
                                capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            return jsonify({'success': True, 'message': f'Conectado à rede {ssid}'})
        else:
            return jsonify({'success': False, 'message': 'Erro ao conectar'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@wifi_bp.route('/api/wifi/status', methods=['GET'])
def wifi_status():
    """Retorna status da conexão Wi-Fi"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401

    try:
        result = subprocess.run(['iwgetid', '-r'], capture_output=True, text=True, timeout=5)
        current_ssid = result.stdout.strip() if result.returncode == 0 else None

        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=5)
        ip_address = result.stdout.strip().split()[0] if result.returncode == 0 else None

        is_hotspot = current_ssid == 'Croma-3D-Printer' if current_ssid else False

        return jsonify({
            'success': True,
            'status': {
                'connected': bool(current_ssid),
                'ssid': current_ssid,
                'ip': ip_address,
                'is_hotspot': is_hotspot
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@wifi_bp.route('/api/wifi/saved', methods=['GET'])
def wifi_saved():
    """Lista redes Wi-Fi salvas"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401

    try:
        result = subprocess.run(['sudo', 'nmcli', '-t', '-f', 'NAME,TYPE', 'connection', 'show'],
                                capture_output=True, text=True, timeout=10)

        networks = []
        for line in result.stdout.strip().split('\n'):
            if '802-11-wireless' in line:
                name = line.split(':')[0]
                networks.append(name)

        return jsonify({'success': True, 'networks': networks})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@wifi_bp.route('/api/wifi/forget', methods=['POST'])
def wifi_forget():
    """Remove uma rede Wi-Fi salva"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401

    data = request.get_json()
    ssid = data.get('ssid')

    if not ssid:
        return jsonify({'success': False, 'message': 'SSID não fornecido'}), 400

    try:
        result = subprocess.run(['sudo', 'nmcli', 'connection', 'delete', ssid],
                                capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            return jsonify({'success': True, 'message': f'Rede {ssid} removida'})
        else:
            return jsonify({'success': False, 'message': 'Erro ao remover rede'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
