#!/bin/bash
set -euo pipefail

echo "🚀 Iniciando Chromasistem com auto-switch Wi-Fi/Hotspot..."

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
HOTSPOT_ACTIVE=0
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
    HOTSPOT_ACTIVE=1
    
    sleep 3
    echo "✅ Hotspot 'Chromasistem' ativo! (192.168.4.1)"
fi

# Função para parar hotspot
stop_hotspot() {
    if [ $HOTSPOT_ACTIVE -eq 1 ]; then
        echo "📴 Parando hotspot..."
        pkill -f hostapd 2>/dev/null || true
        systemctl stop dnsmasq 2>/dev/null || true
        HOTSPOT_ACTIVE=0
    fi
}

# Inicia Flask em background
echo "🚀 Iniciando servidor..."
cd /home/pi/Chromasistem
/home/pi/Chromasistem/venv/bin/python app.py &
FLASK_PID=$!

# Monitor de conexão Wi-Fi (roda a cada 30 segundos)
while true; do
    sleep 30
    
    # Verifica se tem Wi-Fi conectado
    if ip addr show wlan0 2>/dev/null | grep -q "inet 192.168.4" || ! ip addr show wlan0 2>/dev/null | grep -q "inet"; then
        # Sem Wi-Fi ou usando IP do hotspot
        if [ $HOTSPOT_ACTIVE -eq 0 ] && ! ip route show | grep -q "default"; then
            echo "📡 Nenhum Wi-Fi. Ativando hotspot..."
            
            pkill -f wpa_supplicant 2>/dev/null || true
            pkill -f dhcpcd 2>/dev/null || true
            systemctl stop NetworkManager 2>/dev/null || true
            systemctl stop dnsmasq 2>/dev/null || true
            
            ip link set wlan0 down 2>/dev/null || true
            sleep 1
            ip link set wlan0 up
            sleep 1
            ip addr flush dev wlan0 2>/dev/null || true
            ip addr add 192.168.4.1/24 dev wlan0
            
            systemctl start dnsmasq 2>/dev/null || true
            sleep 2
            hostapd -B /etc/hostapd/hostapd.conf 2>/dev/null || true
            HOTSPOT_ACTIVE=1
            echo "✅ Hotspot ativado"
        fi
    else
        # Tem Wi-Fi conectado
        if [ $HOTSPOT_ACTIVE -eq 1 ]; then
            stop_hotspot
            echo "✅ Wi-Fi detectado, hotspot desativado"
        fi
    fi
done
