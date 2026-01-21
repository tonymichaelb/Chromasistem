# 📦 Instalação do Croma no Raspberry Pi

## 🎯 Pré-requisitos

- Raspberry Pi 2W (ou superior)
- Raspbian OS instalado
- Conexão à internet
- Acesso SSH ou monitor conectado

## 🚀 Instalação Rápida

### 1. Conectar ao Raspberry Pi

```bash
# Via SSH (substitua pelo IP do seu Raspberry)
ssh pi@192.168.1.X

# Senha padrão: raspberry
```

### 2. Atualizar o Sistema

```bash
sudo apt update && sudo apt upgrade -y
```

### 3. Instalar Dependências

```bash
# Git
sudo apt install git -y

# Python 3 e pip
sudo apt install python3 python3-pip python3-venv -y

# Bibliotecas do sistema
sudo apt install python3-dev python3-rpi.gpio -y

# NetworkManager, hostapd e dnsmasq (para Wi-Fi)
sudo apt install network-manager hostapd dnsmasq -y
```

### 4. Clonar o Projeto do GitHub

```bash
cd ~
git clone https://github.com/tonymichaelb/Chromasistem.git
cd Chromasistem
```

### 5. Criar e Ativar Ambiente Virtual

```bash
python3 -m venv venv
source venv/bin/activate
```

### 6. Instalar Dependências Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 7. Configurar Permissões

```bash
# Criar diretórios necessários
mkdir -p gcode_files
mkdir -p static/thumbnails

# Dar permissões
chmod +x install.sh
chmod +x run.sh

# Adicionar usuário ao grupo dialout (para serial)
sudo usermod -a -G dialout $USER

# Adicionar ao grupo gpio
sudo usermod -a -G gpio $USER
```

### 8. Configurar Serial

```bash
# Desabilitar console serial (liberar para impressora)
sudo raspi-config
# Navegar: Interface Options → Serial Port
# Login shell: NO
# Serial port hardware: YES
```

### 9. Testar Instalação

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Executar servidor
python app.py
```

Acesse no navegador: `http://IP_DO_RASPBERRY:8080`

## 🔧 Configuração como Serviço (Iniciar Automaticamente)

### 1. Criar Serviço Principal

```bash
sudo cp croma.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable croma.service
sudo systemctl start croma.service
```

### 2. Criar Serviço Wi-Fi Manager

```bash
sudo cp croma-wifi.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable croma-wifi.service
sudo systemctl start croma-wifi.service
```

### 3. Verificar Status

```bash
# Status do servidor principal
sudo systemctl status croma.service

# Status do Wi-Fi manager
sudo systemctl status croma-wifi.service

# Ver logs
sudo journalctl -u croma.service -f
```

## 📡 Configuração do Hotspot Wi-Fi

O sistema cria automaticamente um hotspot quando não há conexão Wi-Fi:

**SSID:** `Croma-3D-Printer`  
**Senha:** `croma1234`

Para alterar, edite o arquivo `wifi_manager.py`:

```python
HOTSPOT_SSID = "Croma-3D-Printer"  # Alterar aqui
HOTSPOT_PASSWORD = "croma1234"      # Alterar aqui
```

## 🔌 Configuração do Sensor de Filamento

O sensor está configurado para:
- **GPIO:** 17 (pino físico 11)
- **Modo:** Normalmente Aberto (NO)
- **Pull:** Pull-up interno ativado

### Esquema de Conexão:

```
Sensor de Filamento
├─ Terminal 1 → GPIO 17 (Pino 11)
└─ Terminal 2 → GND (Pino 9 ou 14)
```

Quando o filamento acaba, o contato abre e a impressão pausa automaticamente.

## 🖨️ Configuração Serial da Impressora

Por padrão configurado para:
- **Porta:** `/dev/ttyUSB0`
- **Baud Rate:** 115200

Se sua impressora usar porta diferente, edite `app.py`:

```python
SERIAL_PORT = '/dev/ttyUSB0'  # Alterar se necessário
BAUD_RATE = 115200
```

Para encontrar a porta correta:

```bash
ls -l /dev/tty*
# Procure por ttyUSB0, ttyACM0, etc.
```

## 🎨 Primeiro Acesso

1. Conecte-se ao Raspberry Pi na porta 8080
2. Clique em "Criar Conta"
3. Defina usuário e senha (apenas o primeiro usuário pode se registrar)
4. Faça login e comece a usar!

## 🔄 Atualizações

Para atualizar o sistema:

```bash
cd ~/Chromasistem
git pull origin main

# Reativar ambiente virtual
source venv/bin/activate

# Atualizar dependências
pip install -r requirements.txt --upgrade

# Reiniciar serviços
sudo systemctl restart croma.service
sudo systemctl restart croma-wifi.service
```

## 🛠️ Comandos Úteis

```bash
# Iniciar servidor manualmente
cd ~/Chromasistem
source venv/bin/activate
python app.py

# Ver logs do sistema
sudo journalctl -u croma.service -f

# Reiniciar serviços
sudo systemctl restart croma.service

# Parar serviços
sudo systemctl stop croma.service

# Ver IP do Raspberry
hostname -I

# Testar conexão serial
ls -l /dev/ttyUSB*
```

## 🐛 Solução de Problemas

### Servidor não inicia

```bash
# Verificar logs
sudo journalctl -u croma.service -n 50

# Verificar se porta está em uso
sudo lsof -i:8080

# Matar processo se necessário
sudo kill -9 $(lsof -t -i:8080)
```

### Serial não funciona

```bash
# Verificar dispositivos
ls -l /dev/tty*

# Testar permissões
groups $USER
# Deve incluir: dialout

# Adicionar ao grupo se necessário
sudo usermod -a -G dialout $USER
# Fazer logout e login novamente
```

### Wi-Fi não conecta

```bash
# Verificar NetworkManager
sudo systemctl status NetworkManager

# Reiniciar NetworkManager
sudo systemctl restart NetworkManager

# Ver redes disponíveis
nmcli device wifi list
```

### GPIO não funciona

```bash
# Verificar se está no grupo gpio
groups $USER

# Adicionar ao grupo
sudo usermod -a -G gpio $USER

# Reiniciar
sudo reboot
```

## 📱 Acesso Remoto

### Pelo IP Local

```
http://IP_DO_RASPBERRY:8080
```

### Pelo Hotspot

Quando o hotspot estiver ativo:
```
http://10.42.0.1:8080
```

## 🔒 Segurança

### Alterar senha padrão do Raspberry

```bash
passwd
```

### Firewall (Opcional)

```bash
sudo apt install ufw -y
sudo ufw allow 8080/tcp
sudo ufw allow 22/tcp
sudo ufw enable
```

## 📞 Suporte

Problemas ou dúvidas:
- GitHub Issues: https://github.com/tonymichaelb/Chromasistem/issues
- Documentação completa no repositório

---

**✅ Instalação Concluída!**

Seu sistema Croma está pronto para monitorar sua impressora 3D! 🎉
