#!/bin/bash
# Script para configurar hotspot no Raspberry Pi

echo "🔧 Configurando hotspot..."

# Configura IP estático para wlan0
sudo ip addr add 192.168.4.1/24 dev wlan0 2>/dev/null

# Copia arquivos de configuração
sudo cp /home/pi/Chromasistem/hostapd.conf /etc/hostapd/
sudo cp /home/pi/Chromasistem/dnsmasq-hotspot.conf /etc/dnsmasq.d/

# Reinicia dnsmasq
sudo systemctl restart dnsmasq

# Inicia hostapd
sudo hostapd /etc/hostapd/hostapd.conf &

echo "✅ Hotspot configurado!"
