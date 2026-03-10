# Pause / Resume — Bug da Extrusora e Correções Críticas

Documento de referência para **nunca mais** introduzir regressões no fluxo de pausa/retomada. Explica o bug, a causa raiz, a solução e as regras que todo agente deve seguir ao mexer nesse código.

---

## 1. Contexto do bug

Após pausar e retomar a impressão, a extrusora:

1. **Ficava indo para trás e para frente** sem empurrar o filamento de forma contínua.
2. **Não extrudava** na retomada — a impressão continuava os movimentos XY/Z mas sem filamento saindo do bico.
3. **O eixo Z subia exageradamente** antes de voltar à posição de impressão.

Além disso, quando a conexão serial morria (I/O error), o sistema entrava em **loop infinito** tentando M105/M27 sem parar.

---

## 2. Causa raiz: modo de extrusão (M82 vs M83)

### O problema central

O G-code gerado pelo fatiador (OrcaSlicer) usa **M83 — extrusão relativa**. Isso significa que cada comando `G1 ... E0.87` quer dizer "extruda 0.87mm de filamento **neste movimento**" (delta), e **não** "vá para a posição E absoluta 0.87".

No Marlin, dependendo da configuração `COMPATIBILITY_G90_G91`:

| Configuração | Comportamento de `G90` |
|---|---|
| `COMPATIBILITY_G90_G91 = true` | `G90` **não** afeta o eixo E — M82/M83 são independentes. |
| `COMPATIBILITY_G90_G91 = false` (muitos firmwares) | `G90` **sobrescreve M83** e volta para extrusão absoluta (M82). |

O código de resume mandava `G90` para posicionamento absoluto (correto para XY/Z), mas isso **destruía o modo M83** do fatiador. Resultado:

- O firmware recebia `G1 ... E0.87` e interpretava como "vá para posição E absoluta 0.87".
- Como E já estava próximo desse valor, o motor da extrusora **não se movia** (ou se movia pouquíssimo).
- Visualmente: o bico voltava ao lugar, mas nenhum filamento saía.

### Por que o retract/unretract parecia "ir e voltar"

O retract (`G1 E-5`) e unretract (`G1 E+5`) usavam `G91` (relativo) e funcionavam corretamente por si só. Mas logo após o unretract, o `G90` final sobrescrevia M83, e a extrusão do G-code parava de funcionar. O usuário via: retract (pra trás) → unretract (pra frente) → nada (sem extrusão contínua).

---

## 3. Solução implementada

### 3.1 Tracking do modo de extrusão

**Arquivo:** `core/state.py`

```python
last_extrusion_mode = 'M82'  # Rastreia o último M82/M83 visto no G-code
```

**Arquivo:** `core/print_engine.py` — no loop principal, antes de enviar cada linha:

```python
if cmd_upper.startswith('M83'):
    st.last_extrusion_mode = 'M83'
elif cmd_upper.startswith('M82'):
    st.last_extrusion_mode = 'M82'
```

Isso garante que o sistema sempre sabe qual modo de extrusão o G-code está usando.

### 3.2 Sequência de PAUSE (park) — `core/print_engine.py`

Quando `st.print_paused == True`, a thread executa:

```
1. Captura posição via M114 → salva pos_x, pos_y, pos_z, pos_e
2. Captura temperaturas via M105 → salva target_nozzle, target_bed
3. G91                          → modo relativo (XYZ + E)
4. G1 E-{RETRACT_MM} F300      → retract de filamento (evita oozing)
5. G1 Z{LIFT_MM} F300          → sobe Z para afastar o bico da peça
6. G90                          → volta para absoluto (para o park XY)
7. G0 X{PARK_X} Y{PARK_Y}     → estaciona o bico no canto
8. Salva tudo no banco (print_pause_state) e na memória (_pause_mem_state)
```

**Importante:** a posição E é capturada **antes** do retract.

### 3.3 Sequência de RESUME (unpark) — `routes/printer_api.py`

```
 1. Carrega estado do banco ou memória (incluindo pos_e)
 2. Reaquece bico/mesa se necessário (pausa fria ou temperatura caiu)
 3. G90                                → absoluto para reposicionar
 4. G0 X{pos_x} Y{pos_y} F3000        → volta XY para posição da pausa
 5. G0 Z{pos_z} F300                   → volta Z para altura da pausa
 6. G91                                → relativo para unretract
 7. G1 E{RETRACT_MM} F300              → unretract (repõe pressão no bico)
 8. G90                                → absoluto de novo
 9. M83 (ou M82)                       → RESTAURA o modo de extrusão ← CRÍTICO!
10. G92 E{pos_e}                       → restaura contador E exato ← CRÍTICO!
11. st.print_paused = False            → libera thread para continuar
```

**Os passos 9 e 10 são a correção central.** Sem eles, o G90 do passo 8 sobrescreve M83, e a extrusão para de funcionar.

### 3.4 Correção do loop de I/O errors — `core/printer.py`

Quando ocorre `OSError` ou `serial.SerialException` no `send_gcode`:

```python
except (OSError, serial.SerialException) as e:
    print(f"Erro ao enviar comando '{command.strip()}': {e}")
    try:
        if st.printer_serial:
            st.printer_serial.close()
    except Exception:
        pass
    st.printer_serial = None
    return None
```

Isso **fecha a conexão serial imediatamente** e seta `printer_serial = None`, de modo que:
- As próximas chamadas de status veem `connected = False`.
- O polling para de tentar M105/M27 em loop.
- O usuário pode reconectar manualmente.

---

## 4. Regras para futuros agentes

### NUNCA faça isso:

| Ação proibida | Por quê |
|---|---|
| Remover o retract (`G1 E-{RETRACT}`) da pausa | O bico vai escorrer filamento durante toda a pausa, grudando na peça. |
| Remover o unretract (`G1 E+{RETRACT}`) do resume | O bico não terá pressão e não vai extrudar nas primeiras linhas (ou mais). |
| Mandar `G90` sem restaurar `M83`/`M82` depois | O modo de extrusão é corrompido; o G-code para de funcionar. |
| Ignorar `pos_e` no resume | O contador E do firmware fica dessincronizado do que o G-code espera; extrusão fica errada. |
| Ignorar I/O errors no `send_gcode` | O sistema entra em loop infinito de erros, congestionando o servidor. |

### SEMPRE faça isso:

1. **Rastreie M82/M83**: o `print_engine` atualiza `st.last_extrusion_mode` conforme processa o G-code.
2. **Restaure o modo E após qualquer G90**: sempre que o resume (ou qualquer outro código) mandar `G90`, envie `st.last_extrusion_mode` logo depois.
3. **Restaure pos_e com `G92 E{pos_e}`**: após o unretract e a restauração do modo E, sincronize o contador.
4. **Retract e unretract são simétricos**: o retract puxa o filamento na pausa; o unretract empurra de volta no resume. A quantidade deve ser a mesma (`PAUSE_RETRACT_MM`).
5. **Capture a posição ANTES do retract/lift**: `get_current_position()` (M114) deve ser chamado antes de qualquer G91/G1 de park.

---

## 5. Variáveis de configuração envolvidas

| Variável | Arquivo | Default | Descrição |
|---|---|---|---|
| `PAUSE_RETRACT_MM` | `core/config.py` | `5` | Quantidade de filamento a retrair/repor (mm). |
| `PAUSE_Z_LIFT_MM` | `core/config.py` | `10` | Quanto subir Z ao pausar (mm). |
| `PAUSE_PARK_X` | `core/config.py` | `0` | Posição X de estacionamento. |
| `PAUSE_PARK_Y` | `core/config.py` | `0` | Posição Y de estacionamento. |
| `TEMP_REHEAT_MARGIN` | `core/config.py` | `5` | Margem (°C) para decidir se precisa reaquecer. |
| `last_extrusion_mode` | `core/state.py` | `'M82'` | Último modo E visto no G-code (`'M82'` ou `'M83'`). |

---

## 6. Arquivos envolvidos

| Arquivo | Responsabilidade no fluxo pause/resume |
|---|---|
| `core/state.py` | Estado compartilhado: `print_paused`, `_pause_mem_state`, `last_extrusion_mode`, etc. |
| `core/print_engine.py` | Thread que envia G-code: detecta pausa, salva estado, executa park, rastreia M82/M83. |
| `routes/printer_api.py` | Endpoints `/api/printer/pause` e `/api/printer/resume`: sinaliza pausa, executa reaquecimento + unpark + restauração E. |
| `core/printer.py` | `send_gcode()`: comunicação serial, detecção de I/O errors, desconexão automática. |
| `core/config.py` | Constantes de retract, lift, park, reheat margin. |

---

## 7. Diagrama resumido

```
PAUSE (print_engine.py thread)              RESUME (printer_api.py endpoint)
──────────────────────────────              ────────────────────────────────
1. M114 → salva X,Y,Z,E                    1. Carrega estado (banco/memória)
2. M105 → salva temps alvo                 2. Reaquece se necessário
3. G91                                     3. G90
4. G1 E-{RETRACT} F300  ← retract         4. G0 X{x} Y{y} F3000
5. G1 Z{LIFT} F300      ← sobe Z          5. G0 Z{z} F300
6. G90                                     6. G91
7. G0 X{PARK} Y{PARK}   ← estaciona       7. G1 E{RETRACT} F300  ← unretract
8. Salva no banco + memória                8. G90
9. Loop de espera                          9. M83 (ou M82)        ← RESTAURA E MODE!
                                          10. G92 E{pos_e}        ← RESTAURA E POS!
                                          11. print_paused = False ← libera thread
```

---

## 8. Como testar

1. Inicie uma impressão (qualquer G-code com M83).
2. Pause com opção "manter temperatura".
3. Observe nos logs:
   - `🏁 Executando park: retract=5.00mm, lift_z=10.00mm, park=(0.00,0.00), E_mode=M83`
4. Retome.
5. Observe nos logs:
   - `🚚 Executando unpark para pos=(...), retract_restore=5.00mm, E_mode=M83`
   - `📐 E restaurado: modo=M83, G92 E{valor}`
6. A impressão deve continuar extrudando normalmente, sem falhas.
