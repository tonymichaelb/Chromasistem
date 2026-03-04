# Sensor de Filamento - Configuração

Este projeto suporta **dois modos** de leitura do sensor:

1) **GPIO do Raspberry (modo `gpio`)**: sensor ligado direto no Raspberry.
2) **Marlin (modo `marlin`)**: sensor ligado na **placa da impressora** e o sistema lê o estado via serial usando `M119`.

## Especificações

- **GPIO**: GPIO17 (Pino físico 11)
- **Tipo**: Sensor mecânico Normalmente Aberto (NO)
- **Lógica**:
  - **COM FILAMENTO**: Sensor ABERTO → GPIO HIGH (1) → ✅ OK
  - **SEM FILAMENTO**: Sensor FECHADO → GPIO LOW (0) → ⚠️ ALERTA

## Diagrama de Conexão

```
Raspberry Pi 2W          Sensor de Filamento
┌─────────────┐          ┌──────────────┐
│             │          │              │
│  GPIO17 (11)├─────────►│  Signal      │
│             │          │              │
│  GND (6)    ├─────────►│  GND         │
│             │          │              │
└─────────────┘          └──────────────┘
```

### Pinagem do Raspberry Pi 2W

```
     3.3V  (1) (2)  5V
    GPIO2  (3) (4)  5V
    GPIO3  (5) (6)  GND  ◄── GND do sensor
    GPIO4  (7) (8)  GPIO14
      GND  (9) (10) GPIO15
 ►GPIO17 (11) (12) GPIO18  ◄── Signal do sensor
   GPIO27 (13) (14) GND
   GPIO22 (15) (16) GPIO23
     3.3V (17) (18) GPIO24
   GPIO10 (19) (20) GND
```

## Funcionamento

### 1. Estado Normal (Com Filamento)

- Sensor mecânico está ABERTO (filamento pressiona a alavanca)
- GPIO17 lê HIGH (1)
- Dashboard mostra: "🧵 Filamento: OK" (verde)

### 2. Sem Filamento

- Filamento acaba, alavanca solta
- Sensor FECHA o contato
- GPIO17 lê LOW (0)
- **Ação Automática**:
  - Sistema pausa a impressão (comando `M25`)
  - Envia mensagem para display: "Sem filamento!"
  - Dashboard mostra: "⚠️ Filamento: SEM FILAMENTO!" (vermelho)

### 3. Callback de Interrupção

O sistema usa interrupção GPIO (event detect) para resposta imediata:
- Não precisa polling constante
- Detecção instantânea quando sensor muda de estado
- Debounce de 300ms para evitar leituras falsas

## Instalação

### 1. Instalar Biblioteca GPIO

```bash
cd /home/pi/croma
source venv/bin/activate
pip install RPi.GPIO==0.7.1

## Modo Marlin (sensor ligado na placa)

Se você quer usar o **sensor da própria impressora** (Marlin), não precisa de GPIO no Raspberry.

### 1) Ativar no Marlin

- Conecte o sensor de filamento na entrada de **FIL_RUNOUT**/runout da sua placa.
- No firmware Marlin, habilite o recurso de runout (nomes podem variar por versão/placa):
  - `FILAMENT_RUNOUT_SENSOR`
  - (opcional) `HOST_ACTION_COMMANDS` / `ADVANCED_PAUSE_FEATURE`

### 2) Configurar o Chromasistem para ler via `M119`

Defina a variável de ambiente:

- `FILAMENT_SENSOR_MODE=marlin`

Opcional:

- `FILAMENT_CHECK_INTERVAL_SEC=2.0` (quanto tempo entre leituras; padrão 2s)
- `MARLIN_FILAMENT_INVERT=1` (se o seu Marlin reportar invertido: `open` = sem filamento)

No Raspberry (systemd), você pode adicionar no service:

```ini
Environment="FILAMENT_SENSOR_MODE=marlin"
```

Depois:

```bash
sudo systemctl daemon-reload
sudo systemctl restart croma
```

### 3) Como funciona a leitura

O sistema envia `M119` e procura uma linha parecida com:

- `filament: open` (normalmente = COM filamento)
- `filament: TRIGGERED` (normalmente = SEM filamento)

Quando detectar sem filamento, a impressão é pausada pelo próprio sistema (interrompe o envio do G-code) e você retoma ao clicar em **Continuar**.
```

### 2. Conectar Sensor Físico

1. **Desligue o Raspberry Pi**
2. Conecte o cabo Signal do sensor ao **GPIO17 (pino físico 11)**
3. Conecte o GND do sensor ao **GND (pino físico 6)**
4. Ligue o Raspberry Pi

### 3. Testar Sensor

```bash
# Verificar se o GPIO está funcionando
python3 -c "
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
print('Estado do sensor:', GPIO.input(17))
GPIO.cleanup()
"
```

**Resultado esperado:**
- Com filamento: `1` (HIGH)
- Sem filamento: `0` (LOW)

## Código do Sistema

### Configuração no código (core/config.py e core/filament.py)

```python
# Pino do sensor
FILAMENT_SENSOR_PIN = 17  # GPIO17 (Pino físico 11)

# Configurar GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(FILAMENT_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Callback automático
GPIO.add_event_detect(FILAMENT_SENSOR_PIN, GPIO.BOTH, 
                     callback=filament_sensor_callback, 
                     bouncetime=300)
```

### Callback de Detecção

```python
def filament_sensor_callback(channel):
    gpio_state = GPIO.input(FILAMENT_SENSOR_PIN)
    has_filament = bool(gpio_state)
    
    if not has_filament:
        # SEM FILAMENTO!
        send_gcode('M25')  # Pausar impressão
        send_gcode('M117 Sem filamento!')  # Mensagem no display
```

## API Endpoints

### GET /api/filament/status

Retorna status atual do sensor:

```json
{
  "success": true,
  "filament": {
    "has_filament": true,
    "sensor_enabled": true,
    "last_check": "2026-01-21T01:30:00"
  }
}
```

### GET /api/printer/status

Inclui informação do filamento:

```json
{
  "success": true,
  "status": {
    "temperature": {...},
    "progress": 45.5,
    "filament": {
      "has_filament": false,
      "sensor_enabled": true,
      "last_check": "2026-01-21T01:30:15"
    }
  }
}
```

## Interface Web

### Dashboard

O status do filamento aparece no card de temperatura:

```
┌──────────────────────────┐
│  Temperaturas            │
├──────────────────────────┤
│  🌡️ Bico: 210°C / 210°C │
│  🔥 Mesa: 60°C / 60°C    │
│  🧵 Filamento: OK        │  ← Verde quando OK
└──────────────────────────┘

┌──────────────────────────┐
│  Temperaturas            │
├──────────────────────────┤
│  🌡️ Bico: 210°C / 210°C │
│  🔥 Mesa: 60°C / 60°C    │
│  ⚠️ Filamento: SEM FILAMENTO! │  ← Vermelho quando falta
└──────────────────────────┘
```

## Tipos de Sensores Compatíveis

### 1. Sensor Mecânico (Switch)

- Tipo: Microswitch com alavanca
- Mais comum e confiável
- Normalmente Aberto (NO)
- Exemplo: Sensor tipo "filament runout detector"

### 2. Sensor Óptico

- Tipo: Infravermelho (IR)
- Detecta presença do filamento
- Alguns têm lógica invertida - verificar datasheet

## Resolução de Problemas

### Sensor sempre mostra "SEM FILAMENTO"

**Possível causa**: Lógica invertida

**Solução**: Inverter a lógica no código:

```python
# Trocar esta linha:
has_filament = bool(gpio_state)

# Por:
has_filament = not bool(gpio_state)
```

### Sensor não detecta mudanças

**Verificar**:
1. Conexões físicas (GPIO17 e GND)
2. Sensor está funcionando (testar continuidade)
3. Pull-up está habilitado

```bash
# Testar manualmente
python3 -c "
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)

for i in range(10):
    print(f'Leitura {i+1}: {GPIO.input(17)}')
    time.sleep(0.5)

GPIO.cleanup()
"
```

### Leituras instáveis (oscilando)

**Causa**: Ruído elétrico ou cabo muito longo

**Soluções**:
1. Aumentar debounce time (padrão: 300ms)
2. Usar cabo blindado
3. Adicionar capacitor de 100nF entre Signal e GND

## Desabilitar Sensor

Se quiser desabilitar temporariamente:

```python
# No app.py, comente a linha:
# setup_filament_sensor()
```

Ou desinstale a biblioteca:
```bash
pip uninstall RPi.GPIO
```

O sistema detectará automaticamente e desabilitará o sensor.

## Expansões Futuras

### Sensor de Movimento do Filamento

Além do sensor de presença, pode-se adicionar sensor de movimento (encoder):
- Detecta se filamento está realmente sendo puxado
- Identifica atolamento ou extrusora patinando
- GPIO adicional (ex: GPIO27)

### Múltiplos Sensores

Para impressoras com múltiplos extrusores:
- GPIO17: Extrusor 1
- GPIO27: Extrusor 2
- etc.
