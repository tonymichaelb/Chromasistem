#!/bin/bash
set -euo pipefail

echo "🚀 Iniciando Chromasistem..."

# Desbloqueia Wi-Fi por segurança
rfkill unblock wifi || true

# Aguarda 1 minuto tentando encontrar Wi-Fi
echo "⏳ Procurando redes Wi-Fi disponíveis (60 segundos)..."
WIFI_TIMEOUT=60
WIFI_FOUND=0

for i in $(seq 1 $WIFI_TIMEOUT); do
    # Verifica se há interface wlan0
    if ! ip link show wlan0 &>/dev/null; then
        if [ $((i % 30)) -eq 0 ]; then
            echo "⚠️ Interface wlan0 não encontrada"
        fi
        sleep 1
        continue
    fi

    # Verifica se tem IP (conectado a Wi-Fi)
    if ip addr show wlan0 | grep -q "inet "; then
        CURRENT_IP=$(ip addr show wlan0 | grep "inet " | awk '{print $2}')
        echo "✅ Conexão Wi-Fi encontrada! IP: $CURRENT_IP"
        WIFI_FOUND=1
        break
    fi

    if [ $((i % 30)) -eq 0 ]; then
        echo "⏳ Aguardando Wi-Fi... ($i/$WIFI_TIMEOUT segundos)"
    fi
    sleep 1
done

# Se não encontrou Wi-Fi, ativa hotspot
if [ $WIFI_FOUND -eq 0 ]; then
    echo "❌ Wi-Fi não encontrado após 1 minuto. Ativando hotspot..."

    # País/regulatório para o Wi-Fi (necessário para hostapd)
    iw reg set BR || true

    # Para serviços que conflitam
    systemctl stop NetworkManager 2>/dev/null || true
    systemctl disable NetworkManager 2>/dev/null || true
    systemctl stop wpa_supplicant@wlan0.service 2>/dev/null || true
    systemctl stop wpa_supplicant.service 2>/dev/null || true
    systemctl stop dhcpcd@wlan0.service 2>/dev/null || true

    # Reconfigura interface wlan0 com IP estático
    echo "🔧 Configurando IP estático em wlan0 (192.168.4.1)..."
    ip link set wlan0 down || true
    ip addr flush dev wlan0 || true
    ip addr add 192.168.4.1/24 dev wlan0
    ip link set wlan0 up

    # Garante configs atualizadas no sistema
    install -D -m 644 /home/pi/Chromasistem/hostapd.conf /etc/hostapd/hostapd.conf
    install -D -m 644 /home/pi/Chromasistem/dnsmasq-hotspot.conf /etc/dnsmasq.d/99-chromasistem-hotspot.conf

    # Reinicia dnsmasq
    echo "🌐 Iniciando DHCP/DNS (dnsmasq)..."
    systemctl restart dnsmasq || true

    # Inicia hostapd (ponto de acesso)
    echo "📡 Iniciando hotspot Chromasistem (hostapd)..."
    pkill -f hostapd 2>/dev/null || true
    hostapd /etc/hostapd/hostapd.conf -B

    sleep 3
    echo "✅ Hotspot ativado! SSID: 'Chromasistem' senha: '12345678' IP: 192.168.4.1"
fi

# Inicia a aplicação
echo "🚀 Iniciando servidor web..."
cd /home/pi/Chromasistem
exec /home/pi/Chromasistem/venv/bin/python app.py
