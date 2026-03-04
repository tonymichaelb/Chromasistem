# Pause/Resume — melhorias a partir do feedback do cliente

Documento de análise do que precisava ser alterado após os testes do cliente. Referências: [pause-resume.md](pause-resume.md), [tasks.md](tasks.md) (seção 3).

---

## 1. Problemas relatados pelo cliente

| # | Problema | Expectativa do cliente |
|---|----------|-------------------------|
| 1 | Ao pausar, o bico fica parado em cima da peça; por estar quente, o material escorre e pinga na peça. | Ao pausar: retrair o bico, recolher (subir Z) e ir para um cantinho (posição de "estacionamento"). Ao retomar: voltar à posição de trabalho e continuar. |
| 2 | Pausa fria pausa mas não baixa a temperatura alvo do bico. | Ao pausar com "Pausa fria": desligar aquecedores (M104 S0 / M140 S0). Ao retomar: reaquecer antes de voltar. |
| 3 | Ao retomar, o bico estava frio; a impressão começou sem esperar o bico esquentar. | Ao retomar: se o bico (e/ou mesa) estiver abaixo da temperatura de impressão, **esperar o reaquecimento** antes de continuar enviando G-code. |

---

## 2. Causa raiz dos problemas

Todo o código de park, cold e DB save estava dentro de um **único try/except**. Se qualquer etapa anterior falhasse (ex: `get_current_position()` timeout, M105 sem resposta, ou erro no INSERT do banco), **tudo era pulado silenciosamente** — incluindo o park e o cold.

Além disso, a ordem estava errada: cold (M104 S0) era enviado ANTES do park, então o bico começava a esfriar em cima da peça.

---

## 3. O que foi implementado — ✅ Tudo resolvido

### 3.1 Park ao pausar (problema 1) — `core/print_engine.py`

Na thread de impressão, ao pausar, agora são **4 etapas independentes** (cada uma em seu try/except):

1. **Capturar posição e temperaturas** (M114 + M105)
2. **Park** — retração + subir Z + mover para canto (ANTES de cold/filament)
3. **Aplicar opção** — cold (M104 S0, M140 S0) ou filament_change (M600) — DEPOIS do park
4. **Salvar estado no banco** (persistência) + fallback em memória (`core/state.py: _pause_mem_state`)

Se uma etapa falha, as outras continuam executando.

### 3.2 Pausa fria funcional (problema 2) — `core/print_engine.py`

Com a separação dos try/excepts, os comandos M104 S0 e M140 S0 são enviados mesmo que etapas anteriores falhem.

### 3.3 Reaquecimento no resume (problema 3) — `routes/printer_api.py`

O endpoint `POST /api/printer/resume` agora:
- Carrega estado do **banco** (fallback: **memória**)
- Se foi pausa fria: **sempre** reaquece (M104+M109, M140+M190) para as temperaturas salvas
- Se foi pausa normal mas temperatura caiu: reaquece se abaixo do alvo (margem `TEMP_REHEAT_MARGIN`)
- Faz **unpark**: volta à posição salva (X,Y -> Z -> desretração)

### 3.4 Configuração — `core/config.py`

| Variável de ambiente | Default | Descrição |
|---|---|---|
| `PAUSE_RETRACT_MM` | 5 | Retração do filamento ao pausar (mm) |
| `PAUSE_Z_LIFT_MM` | 10 | Subida do Z ao pausar (mm) |
| `PAUSE_PARK_X` | 0 | Posição X de estacionamento |
| `PAUSE_PARK_Y` | 0 | Posição Y de estacionamento |
| `TEMP_REHEAT_MARGIN` | 5 | Margem (°C) abaixo do alvo para reaquecer |

---

## 4. Riscos e cuidados

- **Park/Unpark:** Valores de retração e posição de park dependem da impressora e do filamento. Ajustar via variáveis de ambiente sem mexer no código.
- **Ordem dos comandos:** Na pausa: capturar posição -> park -> cold. No resume: reaquecer -> unpark -> continuar. Qualquer inversão pode causar arraste na peça.
- **Compatibilidade:** Desretração usa G91 + G1 E+valor (mesmo valor da retração) para não quebrar o E absoluto do G-code.

---

## 5. Resumo

| Problema | Status | Onde está o código |
|----------|--------|---|
| Bico parado em cima da peça ao pausar | ✅ Resolvido | `core/print_engine.py` (etapa 2: park) |
| Pausa fria não baixa temperatura | ✅ Resolvido | `core/print_engine.py` (etapa 3: cold DEPOIS do park) |
| Retomar sem reaquecer o bico | ✅ Resolvido | `routes/printer_api.py` (printer_resume) |
| Estado de pausa perdido se banco falha | ✅ Resolvido | `core/state.py` (_pause_mem_state como fallback) |
