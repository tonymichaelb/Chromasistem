#!/bin/bash

if [ "$1" == "stop" ]; then
    echo "📴 Parando hotspot..."
    pkill -f hostapd 2>/dev/null || true
    systemctl stop dnsmasq 2>/dev/null || true
    echo "✅ Hotspot parado. Conecte no Wi-Fi com internet."
    echo ""
    echo "Quando terminar as atualizações, reinicie o serviço:"
    echo "  sudo systemctl restart chromasistem"
    
elif [ "$1" == "start" ]; then
    echo "📡 Ativando hotspot..."
    systemctl start dnsmasq 2>/dev/null || true
    sleep 1
    hostapd -B /etc/hostapd/hostapd.conf 2>/dev/null || true
    echo "✅ Hotspot ativado"
    
elif [ "$1" == "status" ]; then
    echo "🔍 Status do hotspot:"
    pgrep -f hostapd >/dev/null && echo "  ✅ Hostapd: ativo" || echo "  ❌ Hostapd: parado"
    systemctl is-active dnsmasq >/dev/null && echo "  ✅ DHCP: ativo" || echo "  ❌ DHCP: parado"
else
    echo "Uso: $0 {stop|start|status}"
    echo ""
    echo "  stop   - Desativa hotspot para conectar no Wi-Fi"
    echo "  start  - Ativa hotspot novamente"
    echo "  status - Mostra status do hotspot"
fi
