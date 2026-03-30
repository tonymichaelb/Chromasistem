#!/usr/bin/env python3
"""
Gerenciador de Wi-Fi para Raspberry Pi
- Inicia hotspot se não houver conexão
- Permite configurar novas redes
"""

import json
import subprocess
import time
import os
import sys

HOTSPOT_SSID = "Croma-3D-Printer"
HOTSPOT_PASSWORD = "croma1234"
HOTSPOT_IP = "10.0.0.1"
CHECK_INTERVAL = 30  # segundos

# Lock: monitor não mexe no hotspot enquanto escaneamos com NM.
SCAN_LOCK_PATH = "/run/chromasistem-wifi-scan.lock"
WIFI_CACHE_PATH = "/run/chromasistem-wifi-cache.json"


def scan_lock_acquire():
    try:
        with open(SCAN_LOCK_PATH, "w") as f:
            f.write(str(os.getpid()))
    except OSError as e:
        print(f"Aviso: não foi possível criar lock de scan: {e}")


def scan_lock_release():
    try:
        os.remove(SCAN_LOCK_PATH)
    except OSError:
        pass


def scan_lock_held():
    return os.path.isfile(SCAN_LOCK_PATH)


def run_command(cmd):
    """Executa comando shell"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def get_wifi_iface():
    """Interface Wi-Fi para AP (env WIFI_IFACE ou primeira detectada)."""
    env = os.environ.get("WIFI_IFACE", "").strip()
    if env:
        return env
    success, output, _ = run_command("iw dev")
    if success and output:
        for line in output.splitlines():
            line = line.strip()
            if line.startswith("Interface "):
                return line.split()[1]
    success, output, _ = run_command("nmcli -t -f DEVICE,TYPE device status")
    if success and output:
        for line in output.strip().split("\n"):
            if not line:
                continue
            if line.endswith(":wifi"):
                return line.rsplit(":", 1)[0]
    return "wlan0"


def hotspot_country_code():
    """ISO 3166-1 alpha-2 — necessário para hostapd em várias regiões."""
    cc = os.environ.get("WIFI_COUNTRY", "BR").strip().upper()[:2]
    return cc if cc else "BR"

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
    iface = get_wifi_iface()
    country = hotspot_country_code()
    print(f"Iniciando hotspot em {iface} (país/regulatório: {country})...")

    # Evita conflito com dnsmasq do systemd (mesma porta / interface).
    run_command("sudo systemctl stop dnsmasq 2>/dev/null")
    # Parar NetworkManager
    run_command("sudo systemctl stop NetworkManager")

    run_command(f"sudo iw reg set {country}")

    # Configurar IP estático na interface Wi-Fi
    run_command(f"sudo ip addr flush dev {iface}")
    run_command(f"sudo ip addr add {HOTSPOT_IP}/24 dev {iface}")
    run_command(f"sudo ip link set {iface} up")

    # Criar arquivo de configuração do hostapd
    hostapd_conf = f"""interface={iface}
driver=nl80211
country_code={country}
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

    with open("/tmp/hostapd.conf", "w") as f:
        f.write(hostapd_conf)

    # Configurar dnsmasq (DHCP) — bind só nesta interface
    dnsmasq_conf = f"""bind-interfaces
interface={iface}
except-interface=lo
dhcp-range=10.0.0.10,10.0.0.50,255.255.255.0,24h
domain=local
address=/croma.local/{HOTSPOT_IP}
"""

    with open("/tmp/dnsmasq.conf", "w") as f:
        f.write(dnsmasq_conf)

    # Parar serviços existentes
    run_command("sudo killall hostapd 2>/dev/null")
    run_command("sudo killall dnsmasq 2>/dev/null")

    # Iniciar dnsmasq (instância dedicada ao hotspot)
    ok_dns, _, err_dns = run_command("sudo dnsmasq -C /tmp/dnsmasq.conf")
    if not ok_dns:
        print(f"✗ Erro ao iniciar dnsmasq: {err_dns}")
        run_command("sudo killall hostapd 2>/dev/null")
        return False

    # Iniciar hostapd
    success, out, error = run_command("sudo hostapd /tmp/hostapd.conf -B")
    if not success:
        combined = (error or "") + (out or "")
        print(f"✗ Erro ao iniciar hostapd: {combined.strip() or 'sem stderr'}")
        run_command("sudo killall dnsmasq 2>/dev/null")

    if success:
        print(f"✓ Hotspot iniciado: {HOTSPOT_SSID}")
        print(f"  Senha: {HOTSPOT_PASSWORD}")
        print(f"  IP: {HOTSPOT_IP}")
        print(f"  Acesse: http://{HOTSPOT_IP}/ (porta 80 se PORT não definido no app)")
        return True
    return False

def stop_hotspot():
    """Para o hotspot"""
    iface = get_wifi_iface()
    print("Parando hotspot...")

    run_command("sudo killall hostapd 2>/dev/null")
    run_command("sudo killall dnsmasq 2>/dev/null")
    run_command(f"sudo ip addr flush dev {iface}")
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

def _include_ap_for_printer_24ghz(band: str, chan: str) -> bool:
    """Exclui 5/6 GHz quando detectável; mantém desconhecido (TIM / dual-band)."""
    b = (band or "").strip().lower()
    ch = str(chan or "").strip()
    try:
        c = int(ch) if ch.isdigit() else None
    except ValueError:
        c = None
    if c is not None and c > 14:
        return False
    if b in ("a",):  # NetworkManager: frequentemente só 5 GHz
        return False
    if "6ghz" in b or b == "6":
        return False
    return True


def _parse_nmcli_wifi_tab(output: str):
    """Parse saída nmcli -m tab (SSID pode conter ':')."""
    networks = []
    for line in output.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        ssid, sig, sec = parts[0], parts[1], parts[2]
        band = parts[3] if len(parts) > 3 else ""
        chan = parts[4] if len(parts) > 4 else ""
        if not ssid or ssid == "--":
            continue
        if not _include_ap_for_printer_24ghz(band, chan):
            continue
        try:
            signal = int(sig) if str(sig).strip().lstrip("-").isdigit() else 0
        except ValueError:
            signal = 0
        networks.append({
            "ssid": ssid,
            "signal": signal,
            "security": sec or "—",
            "band": band or "",
            "chan": chan or "",
        })
    # Mesmo SSID em 2.4 e 5: fica o de maior sinal entre os já filtrados
    best = {}
    for n in networks:
        sid = n["ssid"]
        if sid not in best or n["signal"] > best[sid]["signal"]:
            best[sid] = n
    out = list(best.values())
    out.sort(key=lambda x: x["signal"], reverse=True)
    return out


def _nmcli_wifi_list_tab():
    cmd = (
        "sudo nmcli -m tab -t -f SSID,SIGNAL,SECURITY,BAND,CHAN device wifi list"
    )
    ok, out, _ = run_command(cmd)
    if ok and out.strip():
        return out
    ok, out, _ = run_command(
        "sudo nmcli -m tab -t -f SSID,SIGNAL,SECURITY device wifi list"
    )
    return out if ok else ""


def scan_networks():
    """Escaneia redes (NetworkManager precisa estar ativo)."""
    return _parse_nmcli_wifi_tab(_nmcli_wifi_list_tab())


def scan_to_cache():
    """Para o AP, escaneia com NM, grava JSON e religa o hotspot (uso pelo painel web)."""
    scan_lock_acquire()
    try:
        print("scan-cache: parando hotspot e escaneando…")
        stop_hotspot()
        time.sleep(2)
        run_command("sudo nmcli radio wifi on")
        run_command("sudo nmcli dev wifi rescan 2>/dev/null || true")
        time.sleep(6)
        raw = _nmcli_wifi_list_tab()
        networks = _parse_nmcli_wifi_tab(raw)
        payload = {
            "networks": [
                {"ssid": n["ssid"], "signal": n["signal"], "security": n["security"]}
                for n in networks
            ],
            "ts": time.time(),
        }
        with open(WIFI_CACHE_PATH, "w") as f:
            json.dump(payload, f)
        print(f"✓ scan-cache: {len(networks)} redes (2,4 GHz / sem 5 GHz detectável)")
    except Exception as e:
        print(f"✗ scan-cache: {e}")
        try:
            with open(WIFI_CACHE_PATH, "w") as f:
                json.dump({"networks": [], "ts": time.time(), "error": str(e)}, f)
        except OSError:
            pass
    finally:
        print("scan-cache: religando hotspot…")
        if not start_hotspot():
            print("✗ Falha ao religar hotspot após scan")
        scan_lock_release()

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
            if scan_lock_held():
                time.sleep(3)
                continue

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
                print(
                    f"SSID: {net['ssid']}, Sinal: {net['signal']}%, "
                    f"Segurança: {net['security']}"
                )
        elif cmd == "scan-cache":
            scan_to_cache()
        elif cmd == "connect" and len(sys.argv) >= 4:
            ssid = sys.argv[2]
            password = sys.argv[3]
            connect_wifi(ssid, password)
        else:
            print(
                "Uso: wifi_manager.py "
                "[start|stop|monitor|scan|scan-cache|connect SSID PASSWORD]"
            )
    else:
        monitor_connection()
