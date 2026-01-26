
#!/bin/bash
set -euo pipefail

echo "🚀 Iniciando Chromasistem com auto-switch Wi‑Fi/Hotspot..."

rfkill unblock wifi || true

is_wifi_connected() {
	SSID=$(iwgetid -r 2>/dev/null || true)
	if [ -n "$SSID" ] && ip route show | grep -q "default"; then
		echo "📶 Conectado ao Wi‑Fi: $SSID"
		return 0
	fi
	return 1
}

start_hotspot() {
	echo "📡 Ativando hotspot..."

	# Parar serviços que conflitam
	pkill -f wpa_supplicant 2>/dev/null || true
	pkill -f dhcpcd 2>/dev/null || true
	systemctl stop NetworkManager 2>/dev/null || true
	systemctl stop dnsmasq 2>/dev/null || true
	pkill -f hostapd 2>/dev/null || true

	# Configurar interface
	iw reg set BR || true
	ip link set wlan0 down 2>/dev/null || true
	sleep 1
	ip addr flush dev wlan0 2>/dev/null || true
	ip addr add 192.168.4.1/24 dev wlan0
	ip link set wlan0 up 2>/dev/null || true

	# Garantir configs em /etc
	install -D -m 644 /home/pi/Chromasistem/hostapd.conf /etc/hostapd/hostapd.conf
	install -D -m 644 /home/pi/Chromasistem/dnsmasq-hotspot.conf /etc/dnsmasq.d/99-chromasistem-hotspot.conf

	# Iniciar serviços
	systemctl restart dnsmasq 2>/dev/null || true
	sleep 2
	hostapd -B /etc/hostapd/hostapd.conf 2>/dev/null || true

	echo "✅ Hotspot 'Chromasistem' ativo (192.168.4.1)"
}

stop_hotspot() {
	echo "📴 Parando hotspot..."
	pkill -f hostapd 2>/dev/null || true
	systemctl stop dnsmasq 2>/dev/null || true
}

# Aguarda Wi‑Fi por até 60s
WIFI_TIMEOUT=60
WIFI_FOUND=0
echo "⏳ Verificando Wi‑Fi (até 60s)..."
for i in $(seq 1 $WIFI_TIMEOUT); do
	if is_wifi_connected; then
		WIFI_FOUND=1
		break
	fi
	if [ $((i % 15)) -eq 0 ]; then
		echo "   Aguardando Wi‑Fi... ($i/$WIFI_TIMEOUT)"
	fi
	sleep 1
done

HOTSPOT_ACTIVE=0
if [ $WIFI_FOUND -eq 0 ]; then
	start_hotspot
	HOTSPOT_ACTIVE=1
fi

# Inicia aplicação
echo "🚀 Iniciando servidor web..."
cd /home/pi/Chromasistem
/home/pi/Chromasistem/venv/bin/python app.py &
APP_PID=$!

# Monitoramento a cada 30s
while true; do
	sleep 30
	if is_wifi_connected; then
		if [ $HOTSPOT_ACTIVE -eq 1 ]; then
			stop_hotspot
			HOTSPOT_ACTIVE=0
			echo "✅ Wi‑Fi detectado, hotspot desligado"
		fi
	else
		if [ $HOTSPOT_ACTIVE -eq 0 ]; then
			start_hotspot
			HOTSPOT_ACTIVE=1
		fi
	fi

	# Se o app morrer, sair para systemd reiniciar
	if ! kill -0 $APP_PID 2>/dev/null; then
		echo "⚠️ Servidor web finalizado, encerrando wrapper"
		exit 1
	fi
done
