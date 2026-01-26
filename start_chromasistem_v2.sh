#!/bin/bash
set -euo pipefail

echo "🚀 Iniciando Chromasistem (versão simplificada)..."

# Desbloqueia Wi-Fi
rfkill unblock wifi || true

# Aguarda 1 minuto tentando encontrar Wi-Fi
echo "⏳ Procurando Wi-Fi (60 segundos)..."
WIFI_TIMEOUT=60
WIFI_FOUND=0

for i in $(seq 1 $WIFI_TIMEOUT); do
    if ip addr show wlan0 2>/dev/null | grep -q "inet "; then
        echo "✅ Wi-Fi conectado!"
        WIFI_FOUND=1
        break
    fi
    
    if [ $((i % 15)) -eq 0 ]; then
        echo "   Ainda aguardando... ($i/$WIFI_TIMEOUT)"
    fi
    sleep 1
done

# Se não encontrou Wi-Fi, ativa hotspot
if [ $WIFI_FOUND -eq 0 ]; then
    echo "❌ Wi-Fi não encontrado. Ativando hotspot..."
    
    # Para conflitos
    pkill -f wpa_supplicant 2>/dev/null || true
    pkill -f dhcpcd 2>/dev/null || true
    systemctl stop NetworkManager 2>/dev/null || true
    systemctl stop dnsmasq 2>/dev/null || true
    pkill -f hostapd 2>/dev/null || true
    
    sleep 2
    
    # Configuração da interface
    echo "🔧 Configurando wlan0..."
    iw reg set BR || true
    ip link set wlan0 down 2>/dev/null || true
    sleep 1
    ip link set wlan0 up
    sleep 1
    ip addr flush dev wlan0 2>/dev/null || true
    ip addr add 192.168.4.1/24 dev wlan0
    
    sleep 2
    
    # Inicia dnsmasq
    echo "🌐 Iniciando DHCP..."
    systemctl start dnsmasq
    sleep 2
    
    # Inicia hostapd
    echo "📡 Iniciando hotspot..."
    hostapd -B /etc/hostapd/hostapd.conf
    
    sleep 3
    echo "✅ Hotspot 'Chromasistem' ativo! (192.168.4.1)"
fi

# Inicia Flask
echo "🚀 Iniciando servidor..."
cd /home/pi/Chromasistem
exec /home/pi/Chromasistem/venv/bin/python app.py
