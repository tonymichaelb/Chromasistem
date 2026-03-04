#!/bin/bash

case "$1" in
  start)
    echo "📡 Ativando hotspot..."
    systemctl restart dnsmasq 2>/dev/null || true
    sleep 1
    hostapd -B /etc/hostapd/hostapd.conf 2>/dev/null || true
    echo "✅ Hotspot ativado"
    ;;
  stop)
    echo "📴 Parando hotspot..."
    pkill -f hostapd 2>/dev/null || true
    systemctl stop dnsmasq 2>/dev/null || true
    echo "✅ Hotspot parado"
    ;;
  status)
    pgrep -f hostapd >/dev/null && echo "✅ hostapd: ativo" || echo "❌ hostapd: parado"
    systemctl is-active dnsmasq >/dev/null && echo "✅ dnsmasq: ativo" || echo "❌ dnsmasq: parado"
    ;;
  *)
    echo "Uso: $0 {start|stop|status}"
    exit 1
    ;;

esac
