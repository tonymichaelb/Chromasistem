# Guia de Instalação - Raspberry Pi 2W

## Sistema Croma - Monitoramento de Impressora 3D

### Pré-requisitos

- Raspberry Pi 2W com Raspberry Pi OS instalado
- Conexão com internet
- Acesso SSH ou monitor/teclado conectados
- Impressora 3D com porta USB

---

## Passo 1: Transferir Arquivos para o Raspberry Pi

### Opção A - Usando SCP (do seu computador):
```bash
scp -r "/Users/tonymichaelbatistadelima/Documents/Novo modo Wi-Fi de cores" pi@[IP-DO-RASPBERRY]:~/croma
```

### Opção B - Usando pendrive:
1. Copie a pasta para um pendrive
2. Conecte no Raspberry Pi
3. Copie para /home/pi/croma

---

## Passo 2: Instalar Dependências

Conecte-se ao Raspberry Pi via SSH ou terminal local:

```bash
cd ~/croma
chmod +x install.sh
./install.sh
```

O script irá:
- Atualizar o sistema
- Instalar Python 3 e pip
- Criar ambiente virtual
- Instalar todas as dependências

---

## Passo 3: Executar o Sistema Manualmente

```bash
cd ~/croma
source venv/bin/activate
python app.py
```

O sistema estará disponível em:
- http://localhost:5000 (no próprio Raspberry Pi)
- http://[IP-DO-RASPBERRY]:5000 (em outros dispositivos na rede)

---

## Passo 4: Configurar Inicialização Automática (Opcional)

Para que o sistema inicie automaticamente quando o Raspberry Pi ligar:

```bash
# Copiar arquivo de serviço
sudo cp croma.service /etc/systemd/system/

# Ajustar permissões
sudo chmod 644 /etc/systemd/system/croma.service

# Recarregar systemd
sudo systemctl daemon-reload

# Habilitar serviço
sudo systemctl enable croma.service

# Iniciar serviço
sudo systemctl start croma.service

# Verificar status
sudo systemctl status croma.service
```

### Comandos úteis do serviço:

```bash
# Parar o serviço
sudo systemctl stop croma.service

# Reiniciar o serviço
sudo systemctl restart croma.service

# Ver logs
sudo journalctl -u croma.service -f
```

---

## Passo 5: Conectar a Impressora 3D

### Identificar a porta da impressora:

```bash
# Antes de conectar a impressora, veja as portas existentes
ls /dev/tty*

# Conecte a impressora USB

# Veja novamente as portas (a nova porta é sua impressora)
ls /dev/tty*

# Geralmente será /dev/ttyUSB0 ou /dev/ttyACM0
```

### Dar permissão ao usuário para acessar a porta serial:

```bash
sudo usermod -a -G dialout pi
sudo usermod -a -G tty pi

# Reiniciar para aplicar as mudanças
sudo reboot
```

### Modificar o app.py para conectar com a impressora:

No arquivo `app.py`, procure por comentários com "Em produção" e adicione o código de conexão serial. Exemplo:

```python
import serial

# Adicionar no início do arquivo, após as importações
PRINTER_PORT = '/dev/ttyUSB0'  # ou /dev/ttyACM0
PRINTER_BAUDRATE = 115200

try:
    printer = serial.Serial(PRINTER_PORT, PRINTER_BAUDRATE, timeout=1)
    print(f"Conectado à impressora em {PRINTER_PORT}")
except Exception as e:
    print(f"Erro ao conectar: {e}")
    printer = None
```

---

## Passo 6: Configurar IP Estático (Recomendado)

Para facilitar o acesso, configure um IP estático no Raspberry Pi:

```bash
sudo nano /etc/dhcpcd.conf
```

Adicione no final do arquivo:

```
interface wlan0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8
```

Ajuste os valores conforme sua rede. Reinicie:

```bash
sudo reboot
```

---

## Passo 7: Primeiro Acesso

1. Abra o navegador em qualquer dispositivo na mesma rede
2. Acesse: http://[IP-DO-RASPBERRY]:5000
3. Clique em "Criar conta"
4. Digite seu usuário e senha
5. Faça login

---

## Solução de Problemas

### Porta 5000 já em uso:

Mude a porta no arquivo `app.py`:
```python
app.run(host='0.0.0.0', port=8080, debug=True)
```

### Não consegue acessar de outros dispositivos:

Verifique o firewall:
```bash
sudo ufw allow 5000
```

### Erro ao conectar com a impressora:

Verifique as permissões:
```bash
sudo chmod 666 /dev/ttyUSB0
```

### Ver logs do sistema:

```bash
# Logs do serviço
sudo journalctl -u croma.service -f

# Ou executar manualmente para ver erros
cd ~/croma
source venv/bin/activate
python app.py
```

---

## Recursos Adicionais

### Acessar via Internet (Avançado)

Para acessar de fora da sua rede local:

1. Configure port forwarding no roteador (porta 5000)
2. Use um serviço de DNS dinâmico (No-IP, DuckDNS)
3. **IMPORTANTE**: Use HTTPS e senha forte por segurança

### Backup do Banco de Dados

O banco de dados está em `croma.db`. Para fazer backup:

```bash
cp ~/croma/croma.db ~/croma/backup_$(date +%Y%m%d).db
```

### Atualizar o Sistema

```bash
cd ~/croma
git pull  # Se estiver usando git
sudo systemctl restart croma.service
```

---

## Especificações do Sistema

- **Backend**: Python + Flask
- **Frontend**: HTML5 + CSS3 + JavaScript
- **Banco de Dados**: SQLite
- **Porta padrão**: 5000
- **Requisitos mínimos**: Raspberry Pi 2W, 512MB RAM

---

## Suporte

Para problemas ou dúvidas, verifique:
- Logs do sistema
- Conexão de rede
- Permissões de arquivos
- Status do serviço systemd

---

**Sistema Croma v1.0**  
Desenvolvido para monitoramento e controle de impressoras 3D
