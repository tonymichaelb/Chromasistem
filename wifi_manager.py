#!/usr/bin/env python3
"""
Gerenciador de Wi-Fi para Raspberry Pi
- Inicia hotspot se não houver conexão
- Permite configurar novas redes
"""

import subprocess
import time
import os
import sys

HOTSPOT_SSID = "Croma-3D-Printer"
HOTSPOT_PASSWORD = "croma1234"
HOTSPOT_IP = "10.0.0.1"
CHECK_INTERVAL = 30  # segundos

def run_command(cmd):
    """Executa comando shell"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_internet():
    """Verifica se há conexão com internet"""
    success, _, _ = run_command("ping -c 1 -W 2 8.8.8.8")
    return success

def check_wifi_connected():
    """Verifica se está conectado a alguma rede Wi-Fi"""
    success, output, _ = run_command("iwgetid -r")
    return success and output.strip() != ""

def get_current_ssid():
    """Retorna SSID da rede atual"""
    success, output, _ = run_command("iwgetid -r")
    return output.strip() if success else None

def start_hotspot():
    """Inicia o hotspot"""
    print("Iniciando hotspot...")
    
    # Parar NetworkManager
    run_command("sudo systemctl stop NetworkManager")
    
    # Configurar IP estático para wlan0
    run_command("sudo ip addr flush dev wlan0")
    run_command(f"sudo ip addr add {HOTSPOT_IP}/24 dev wlan0")
    run_command("sudo ip link set wlan0 up")
    
    # Criar arquivo de configuração do hostapd
    hostapd_conf = f"""interface=wlan0
driver=nl80211
ssid={HOTSPOT_SSID}
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase={HOTSPOT_PASSWORD}
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
"""
    
    with open('/tmp/hostapd.conf', 'w') as f:
        f.write(hostapd_conf)
    
    # Configurar dnsmasq (DHCP)
    dnsmasq_conf = f"""interface=wlan0
dhcp-range=10.0.0.10,10.0.0.50,255.255.255.0,24h
domain=local
address=/croma.local/{HOTSPOT_IP}
"""
    
    with open('/tmp/dnsmasq.conf', 'w') as f:
        f.write(dnsmasq_conf)
    
    # Parar serviços existentes
    run_command("sudo killall hostapd 2>/dev/null")
    run_command("sudo killall dnsmasq 2>/dev/null")
    
    # Iniciar dnsmasq
    run_command("sudo dnsmasq -C /tmp/dnsmasq.conf")
    
    # Iniciar hostapd
    success, _, error = run_command("sudo hostapd /tmp/hostapd.conf -B")
    
    if success:
        print(f"✓ Hotspot iniciado: {HOTSPOT_SSID}")
        print(f"  Senha: {HOTSPOT_PASSWORD}")
        print(f"  IP: {HOTSPOT_IP}")
        print(f"  Acesse: http://{HOTSPOT_IP}:8080")
        return True
    else:
        print(f"✗ Erro ao iniciar hotspot: {error}")
        return False

def stop_hotspot():
    """Para o hotspot"""
    print("Parando hotspot...")
    
    run_command("sudo killall hostapd 2>/dev/null")
    run_command("sudo killall dnsmasq 2>/dev/null")
    run_command("sudo ip addr flush dev wlan0")
    run_command("sudo systemctl start NetworkManager")
    
    print("✓ Hotspot parado")

def connect_wifi(ssid, password):
    """Conecta a uma rede Wi-Fi"""
    print(f"Conectando à rede: {ssid}")
    
    # Para o hotspot se estiver ativo
    stop_hotspot()
    
    # Criar conexão usando nmcli
    cmd = f"sudo nmcli dev wifi connect '{ssid}' password '{password}'"
    success, output, error = run_command(cmd)
    
    if success:
        print(f"✓ Conectado à rede: {ssid}")
        return True
    else:
        print(f"✗ Erro ao conectar: {error}")
        # Reiniciar hotspot se falhou
        start_hotspot()
        return False

def scan_networks():
    """Escaneia redes Wi-Fi disponíveis"""
    success, output, _ = run_command("sudo nmcli -t -f SSID,SIGNAL,SECURITY dev wifi list")
    
    if not success:
        return []
    
    networks = []
    for line in output.strip().split('\n'):
        if line:
            parts = line.split(':')
            if len(parts) >= 3:
                networks.append({
                    'ssid': parts[0],
                    'signal': parts[1],
                    'security': parts[2]
                })
    
    return networks

def get_saved_networks():
    """Retorna redes salvas"""
    success, output, _ = run_command("sudo nmcli -t -f NAME,TYPE connection show")
    
    if not success:
        return []
    
    networks = []
    for line in output.strip().split('\n'):
        if '802-11-wireless' in line:
            name = line.split(':')[0]
            networks.append(name)
    
    return networks

def forget_network(ssid):
    """Remove uma rede salva"""
    cmd = f"sudo nmcli connection delete '{ssid}'"
    success, _, _ = run_command(cmd)
    return success

def monitor_connection():
    """Monitor de conexão - inicia hotspot se desconectar"""
    hotspot_active = False
    
    while True:
        try:
            wifi_connected = check_wifi_connected()
            current_ssid = get_current_ssid()
            
            if wifi_connected and current_ssid != HOTSPOT_SSID:
                # Conectado a uma rede normal
                if hotspot_active:
                    print(f"Conectado a {current_ssid}, parando hotspot...")
                    stop_hotspot()
                    hotspot_active = False
                else:
                    print(f"✓ Conectado: {current_ssid}")
            else:
                # Não conectado - iniciar hotspot
                if not hotspot_active:
                    print("Sem conexão Wi-Fi, iniciando hotspot...")
                    if start_hotspot():
                        hotspot_active = True
            
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\nEncerrando monitor...")
            if hotspot_active:
                stop_hotspot()
            break
        except Exception as e:
            print(f"Erro no monitor: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Este script precisa ser executado como root")
        print("Use: sudo python3 wifi_manager.py")
        sys.exit(1)
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "start":
            start_hotspot()
        elif cmd == "stop":
            stop_hotspot()
        elif cmd == "monitor":
            monitor_connection()
        elif cmd == "scan":
            networks = scan_networks()
            for net in networks:
                print(f"SSID: {net['ssid']}, Sinal: {net['signal']}%, Segurança: {net['security']}")
        elif cmd == "connect" and len(sys.argv) >= 4:
            ssid = sys.argv[2]
            password = sys.argv[3]
            connect_wifi(ssid, password)
        else:
            print("Uso: wifi_manager.py [start|stop|monitor|scan|connect SSID PASSWORD]")
    else:
        monitor_connection()
