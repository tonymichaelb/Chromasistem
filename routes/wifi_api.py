"""WiFi configuration API routes."""

from flask import Blueprint, request, jsonify, session
import subprocess

wifi_bp = Blueprint('wifi_api', __name__)


@wifi_bp.route('/api/wifi/scan', methods=['GET'])
def wifi_scan():
    """Escaneia redes Wi-Fi disponíveis"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401

    try:
        result = subprocess.run(['sudo', 'python3', 'wifi_manager.py', 'scan'],
                                capture_output=True, text=True, timeout=15)

        networks = []
        for line in result.stdout.strip().split('\n'):
            if 'SSID:' in line:
                parts = line.split(',')
                ssid = parts[0].replace('SSID:', '').strip()
                signal = parts[1].replace('Sinal:', '').replace('%', '').strip() if len(parts) > 1 else '0'
                security = parts[2].replace('Segurança:', '').strip() if len(parts) > 2 else 'Aberta'

                networks.append({
                    'ssid': ssid,
                    'signal': int(signal) if signal.isdigit() else 0,
                    'security': security
                })

        return jsonify({'success': True, 'networks': networks})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


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
