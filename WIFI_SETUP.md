# Configuração do Sistema Wi-Fi com Hotspot Automático

## Funcionalidades

✅ **Hotspot Automático**: Quando o Raspberry Pi não conseguir conectar a nenhuma rede Wi-Fi, ele cria automaticamente um hotspot
✅ **Configuração Web**: Interface web para escanear e conectar em novas redes Wi-Fi  
✅ **Gerenciamento de Redes**: Salvar, esquecer e gerenciar redes Wi-Fi
✅ **Monitoramento Contínuo**: Verifica conexão constantemente e reativa hotspot se necessário

## Informações do Hotspot

- **SSID**: `Croma-3D-Printer`
- **Senha**: `croma1234`
- **IP do Raspberry**: `10.0.0.1`
- **Acesso Web**: `http://10.0.0.1:8080`

## Instalação no Raspberry Pi 2W

### 1. Instalar Dependências

```bash
sudo apt-get update
sudo apt-get install -y hostapd dnsmasq network-manager
```

### 2. Configurar Permissões

```bash
# Dar permissão de execução
chmod +x wifi_manager.py

# Permitir comandos sudo sem senha para WiFi (necessário)
sudo visudo
```

Adicione no final do arquivo:
```
pi ALL=(ALL) NOPASSWD: /usr/bin/python3 /home/pi/croma/wifi_manager.py*
pi ALL=(ALL) NOPASSWD: /usr/bin/nmcli*
pi ALL=(ALL) NOPASSWD: /usr/sbin/hostapd*
pi ALL=(ALL) NOPASSWD: /usr/sbin/dnsmasq*
pi ALL=(ALL) NOPASSWD: /sbin/ip*
pi ALL=(ALL) NOPASSWD: /bin/systemctl*
```

### 3. Instalar Serviço Systemd

```bash
# Copiar arquivo de serviço
sudo cp croma-wifi.service /etc/systemd/system/

# Atualizar caminho no serviço se necessário
sudo nano /etc/systemd/system/croma-wifi.service

# Recarregar systemd
sudo systemctl daemon-reload

# Habilitar serviço para iniciar automaticamente
sudo systemctl enable croma-wifi.service

# Iniciar serviço
sudo systemctl start croma-wifi.service

# Verificar status
sudo systemctl status croma-wifi.service
```

### 4. Testar Manualmente

```bash
# Testar hotspot
sudo python3 wifi_manager.py start

# Escanear redes
sudo python3 wifi_manager.py scan

# Conectar a uma rede
sudo python3 wifi_manager.py connect "Nome_da_Rede" "senha"

# Parar hotspot
sudo python3 wifi_manager.py stop

# Iniciar modo monitor (automático)
sudo python3 wifi_manager.py monitor
```

## Uso

### Primeira Inicialização

1. Ligue o Raspberry Pi sem nenhuma rede Wi-Fi configurada
2. Aguarde 30-60 segundos
3. O hotspot `Croma-3D-Printer` será criado automaticamente
4. Conecte seu celular/computador ao hotspot usando a senha `croma1234`
5. Acesse `http://10.0.0.1:8080` no navegador
6. Faça login no sistema
7. Vá em **Wi-Fi** no menu
8. Clique em "Atualizar" para escanear redes
9. Selecione sua rede Wi-Fi e conecte
10. O hotspot será desligado automaticamente e o Raspberry conectará à sua rede

### Conectar a Nova Rede

1. Acesse o sistema Croma (via navegador)
2. Vá em **Wi-Fi** no menu superior
3. Clique em **"🔄 Atualizar"** para escanear redes
4. Clique em **"Conectar"** na rede desejada
5. Digite a senha
6. Aguarde a conexão

### Quando o Raspberry Perde Conexão

O sistema monitora a conexão constantemente:
- Se perder conexão com a rede Wi-Fi configurada
- Ou se não conseguir conectar na inicialização
- **Automaticamente** cria o hotspot `Croma-3D-Printer`
- Você pode conectar novamente e configurar outra rede

## Arquitetura

```
┌─────────────────────────────────────┐
│     Raspberry Pi 2W Inicializa      │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   wifi_manager.py (serviço)         │
│   Verifica conexão a cada 30s       │
└────────────┬────────────────────────┘
             │
         ┌───┴───┐
         │       │
    ✅ Sim     ❌ Não
    Conectado? 
         │       │
         ▼       ▼
┌────────────┐ ┌──────────────────────┐
│ Normal     │ │ Inicia Hotspot       │
│ Modo       │ │ Croma-3D-Printer     │
│ Cliente    │ │ IP: 10.0.0.1         │
└────────────┘ └──────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │ Usuario conecta ao   │
              │ hotspot e configura  │
              │ nova rede via web    │
              └──────────────────────┘
```

## Logs e Diagnóstico

```bash
# Ver logs do serviço WiFi
sudo journalctl -u croma-wifi.service -f

# Ver status do NetworkManager
sudo systemctl status NetworkManager

# Listar redes salvas
sudo nmcli connection show

# Ver dispositivos de rede
sudo nmcli device status

# Testar conexão
ping -c 4 google.com
```

## Resolução de Problemas

### Hotspot não inicia

```bash
# Verificar se hostapd está instalado
which hostapd

# Verificar se dnsmasq está instalado  
which dnsmasq

# Verificar logs
sudo journalctl -u croma-wifi.service -n 50
```

### Não consegue conectar a redes

```bash
# Verificar NetworkManager
sudo systemctl status NetworkManager

# Reiniciar NetworkManager
sudo systemctl restart NetworkManager

# Limpar redes antigas
sudo nmcli connection delete "nome_da_rede"
```

### Hotspot continua ativo mesmo conectado

```bash
# Parar manualmente
sudo python3 wifi_manager.py stop

# Reiniciar serviço
sudo systemctl restart croma-wifi.service
```

## Segurança

**IMPORTANTE**: Altere a senha do hotspot em produção!

Edite o arquivo `wifi_manager.py`:
```python
HOTSPOT_SSID = "Croma-3D-Printer"
HOTSPOT_PASSWORD = "sua_senha_segura_aqui"  # ALTERE ISSO!
```

Depois reinicie o serviço:
```bash
sudo systemctl restart croma-wifi.service
```

## Desinstalação

```bash
# Parar e desabilitar serviço
sudo systemctl stop croma-wifi.service
sudo systemctl disable croma-wifi.service

# Remover arquivo de serviço
sudo rm /etc/systemd/system/croma-wifi.service

# Recarregar systemd
sudo systemctl daemon-reload
```
