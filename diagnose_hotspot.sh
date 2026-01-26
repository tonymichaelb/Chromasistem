#!/bin/bash
set -euo pipefail

echo "🔍 Diagnosticando Hotspot..."
echo ""

echo "1️⃣ Status do Wi-Fi (rfkill):"
rfkill list || echo "❌ rfkill não disponível"
echo ""

echo "2️⃣ Interface wlan0:"
ip link show wlan0 || echo "❌ wlan0 não encontrada"
ip addr show wlan0 || echo "❌ Sem IP em wlan0"
echo ""

echo "3️⃣ Status do serviço Chromasistem:"
systemctl status chromasistem || echo "❌ Serviço não ativo"
echo ""

echo "4️⃣ Últimos logs (últimas 30 linhas):"
journalctl -u chromasistem -n 30 --no-pager || echo "❌ Sem logs"
echo ""

echo "5️⃣ Testando hostapd manualmente:"
echo "   Parando serviços em conflito..."
systemctl stop wpa_supplicant@wlan0.service 2>/dev/null || true
systemctl stop wpa_supplicant.service 2>/dev/null || true
systemctl stop dhcpcd@wlan0.service 2>/dev/null || true

echo "   Configurando IP estático..."
ip link set wlan0 down || true
ip addr flush dev wlan0 || true
ip addr add 192.168.4.1/24 dev wlan0
ip link set wlan0 up

echo "   Iniciando hostapd com debug..."
timeout 10 hostapd -dd /etc/hostapd/hostapd.conf || echo "⚠️ hostapd saiu ou timed out"
echo ""

echo "6️⃣ Testando dnsmasq:"
systemctl status dnsmasq || echo "❌ dnsmasq não ativo"
journalctl -u dnsmasq -n 20 --no-pager || echo "❌ Sem logs de dnsmasq"
echo ""

echo "✅ Diagnóstico completo!"
