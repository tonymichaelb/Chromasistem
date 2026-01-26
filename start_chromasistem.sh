#!/bin/bash

echo "🚀 Iniciando Chromasistem..."

# Aguarda 3 minutos tentando encontrar Wi-Fi
echo "⏳ Procurando redes Wi-Fi disponíveis (180 segundos)..."
WIFI_TIMEOUT=180
WIFI_FOUND=0

for i in $(seq 1 $WIFI_TIMEOUT); do
    # Verifica se há conexão de rede (pinging gateway)
    if ip route show | grep -q default && ping -c 1 8.8.8.8 &>/dev/null; then
        echo "✅ Conexão Wi-Fi encontrada!"
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
    echo "❌ Wi-Fi não encontrado. Ativando hotspot..."
    
    # Inicia hostapd (ponto de acesso)
    sudo systemctl start hostapd 2>/dev/null
    sudo systemctl start dnsmasq 2>/dev/null
    
    echo "📡 Hotspot ativado: Chromasistem"
    sleep 2
fi

# Inicia a aplicação
echo "🚀 Iniciando servidor web..."
cd /home/pi/Chromasistem
exec /home/pi/Chromasistem/venv/bin/python app.py
