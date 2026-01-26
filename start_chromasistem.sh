#!/bin/bash

# Aguarda a interface de rede estar pronta (máximo 30 segundos)
echo "⏳ Aguardando interface de rede..."
for i in {1..30}; do
    if ip link show | grep -q "wlan0"; then
        echo "✅ Interface wlan0 detectada"
        break
    fi
    sleep 1
done

# Aguarda conexão ou 15 segundos
echo "⏳ Aguardando rede estar disponível..."
sleep 5

# Inicia a aplicação
echo "🚀 Iniciando Chromasistem..."
cd /home/pi/Chromasistem
exec /home/pi/Chromasistem/venv/bin/python app.py
