# Fluxo de Instalação - Croma (Raspberry Pi)

## Primeira instalação (uma vez)

```bash
# 1. Atualizar sistema e instalar dependências
sudo apt update && sudo apt upgrade -y
sudo apt install git python3 python3-pip python3-venv \
                 python3-dev python3-rpi.gpio \
                 network-manager hostapd dnsmasq -y

# 2. Node.js (para frontend React)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# 3. Clonar e entrar na branch
cd ~
git clone https://github.com/tonymichaelb/Chromasistem.git
cd Chromasistem
git checkout feat/skip-and-failures-feature

# 4. Permissões (serial/GPIO)
sudo usermod -a -G dialout,gpio $USER

# 5. Serial (liberar para impressora)
sudo raspi-config
# Interface Options → Serial Port: Login shell = NO, Serial hardware = YES

# 6. Reiniciar para aplicar grupos (ou fazer logout/login)
# sudo reboot

# 7. Rodar o sistema
./run-prod.sh
```

Acesse: **http://[IP-DO-RASPBERRY]** (porta 80)

---

## Depois da primeira instalação

Sempre que quiser iniciar o sistema (o script faz pull automático e pega as últimas atualizações):

```bash
cd ~/Chromasistem
./run-prod.sh
```

---

## Opcional: iniciar automaticamente no boot

```bash
sudo cp croma.service croma-wifi.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now croma.service croma-wifi.service
```

> **Nota:** Antes de usar o systemd, rode `./run-prod.sh --build` uma vez para gerar o build do React. O serviço usa o build já gerado.
