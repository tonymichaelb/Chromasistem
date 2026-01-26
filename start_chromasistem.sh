#!/bin/bash

echo "🚀 Iniciando Chromasistem..."

# Aguarda 3 minutos tentando encontrar Wi-Fi
echo "⏳ Procurando redes Wi-Fi disponíveis (180 segundos)..."
WIFI_TIMEOUT=180
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
    echo "❌ Wi-Fi não encontrado após 3 minutos. Ativando hotspot..."
    
    # Aguarda um pouco
    sleep 2
    
    # Para networkmanager se estiver rodando
    sudo systemctl stop NetworkManager 2>/dev/null
    sudo systemctl disable NetworkManager 2>/dev/null
    
    # Configura IP estático em wlan0
    echo "🔧 Configurando IP estático em wlan0..."
    sudo ip addr flush dev wlan0
    sudo ip addr add 192.168.4.1/24 dev wlan0
    sudo ip link set wlan0 up
    
    # Para dnsmasq se estiver rodando
    sudo systemctl stop dnsmasq 2>/dev/null
    
    # Inicia dnsmasq com config customizada
    echo "🌐 Iniciando DHCP/DNS..."
    sudo dnsmasq -C /home/pi/Chromasistem/dnsmasq-hotspot.conf -d &
    DNSMASQ_PID=$!
    sleep 2
    
    # Para hostapd se estiver rodando
    sudo pkill -f hostapd 2>/dev/null
    
    # Inicia hostapd
    echo "📡 Iniciando hotspot Chromasistem..."
    sudo hostapd /home/pi/Chromasistem/hostapd.conf -B
    
    sleep 2
    echo "✅ Hotspot ativado! Conecte em 'Chromasistem' com senha '12345678'"
fi

# Inicia a aplicação
echo "🚀 Iniciando servidor web..."
cd /home/pi/Chromasistem
exec /home/pi/Chromasistem/venv/bin/python app.py
