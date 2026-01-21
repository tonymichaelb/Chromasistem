# Configuração da Conexão Serial

## Especificações

- **Porta Serial**: `/dev/ttyUSB0` (padrão) ou `/dev/ttyAMA0` (GPIO do Raspberry Pi)
- **Baudrate**: 115200
- **Timeout**: 2 segundos

## Configuração no Raspberry Pi 2W

### 1. Identificar a Porta Serial

```bash
# Listar portas seriais disponíveis
ls -l /dev/tty*

# Verificar qual porta a impressora está conectada
dmesg | grep tty
```

### 2. Dar Permissões ao Usuário

```bash
# Adicionar usuário ao grupo dialout
sudo usermod -a -G dialout $USER

# Reiniciar para aplicar as permissões
sudo reboot
```

### 3. Testar Conexão Serial

```bash
# Instalar screen para teste
sudo apt-get install screen

# Conectar à porta serial
screen /dev/ttyUSB0 115200

# Para sair: Ctrl+A depois K
```

### 4. Ajustar Porta no Código

Edite o arquivo `app.py` e altere a variável `SERIAL_PORT`:

```python
SERIAL_PORT = '/dev/ttyUSB0'  # Ou /dev/ttyAMA0 se usar GPIO
```

## Comandos G-Code Suportados

### Controle de Temperatura
- `M105` - Ler temperatura atual
- `M104 S[temp]` - Definir temperatura do bico
- `M140 S[temp]` - Definir temperatura da mesa
- `M109 S[temp]` - Aguardar temperatura do bico
- `M190 S[temp]` - Aguardar temperatura da mesa

### Controle de Impressão
- `M24` - Iniciar/retomar impressão do SD
- `M25` - Pausar impressão do SD
- `M27` - Relatar progresso de impressão
- `M108` - Cancelar aquecimento

### Movimento
- `G28` - Home de todos os eixos
- `G28 X Y` - Home apenas X e Y
- `G1 X[pos] Y[pos] Z[pos]` - Movimento linear

### Outros
- `M107` - Desligar ventilador
- `M106 S[0-255]` - Ligar ventilador (0-255)

## Resolução de Problemas

### Erro: Permission Denied
```bash
sudo chmod 666 /dev/ttyUSB0
# Ou adicionar usuário ao grupo dialout
```

### Erro: Device Busy
```bash
# Verificar processos usando a porta
sudo lsof /dev/ttyUSB0

# Matar processo se necessário
sudo kill -9 [PID]
```

### Conexão Instável
- Verificar cabo USB
- Testar com baudrate diferente (9600, 57600, 250000)
- Verificar alimentação da impressora
- Usar cabo USB com ferrite

## Monitoramento

Para ver logs da comunicação serial em tempo real:

```bash
# Seguir logs do servidor
tail -f /var/log/croma/app.log

# Ou ver output direto do terminal onde o servidor está rodando
```
