# Detecção e skip de falhas — guia de implementação

Guia para a **Task 4**: o sistema detecta erros da impressora automaticamente pela serial (ou recebe via endpoint externo), permite pular peça, resolver problema → problema resolvido → retomar, ou cancelar. Inclui visualização da mesa para escolher qual peça pular quando houver várias.

**Referências:** [tasks.md](tasks.md) (seção 4), [duvidas-respostas.md](duvidas-respostas.md) (seção 5), [pause-resume.md](pause-resume.md).

---

## Critério de aceite (evidência)

- Fluxo em que o erro chega ao sistema, o usuário escolhe **pular** / **resolver → resolvido → retomar** / **cancelar**.
- Quando for pular, o usuário consegue **ver a mesa** e **escolher a peça** (quando o G-code tiver marcadores de objeto).
- Evidência em **vídeo**.

---

## Decisões de produto (da dúvida no doc)

| Dúvida | Decisão |
|--------|--------|
| Pular peça atual? | Sim — pular apenas o objeto em falha (ou o escolhido na mesa). |
| Continuar fila? | Sim — seguir enviando o resto do G-code após o skip. |
| Consumir filamento na peça pulada? | Não — ao pular, não enviamos o G-code daquele objeto (não extrudamos para ele). |

---

## 1. Backend

### 1.1 Estado de falha

- [x] **Variáveis globais** (em `core/state.py`):
  - `print_failure_detected` (bool)
  - `current_failure_message` (str ou None)
  - `current_failure_code` (str ou None, opcional)
  - `skip_requested` (bool)
  - `skip_object_id` (int ou None)
  - `_consecutive_cmd_failures` (int, contador interno)
  - `CONSECUTIVE_FAILURES_THRESHOLD` (int, padrão 3)
- [x] **Quando setar falha:**
  - **Automaticamente pela serial:** `_maybe_mark_failure_from_printer_line()` detecta erros do firmware (ver seção 7).
  - **Por comunicação perdida:** 3+ comandos consecutivos sem resposta (ver seção 7.3).
  - Via `POST /api/printer/failure` (notificação externa, ex. OctoPrint/script).
- [x] **Comportamento da thread de impressão:** quando `print_failure_detected`, a thread **para** de enviar G-code, o bico **sobe e vai para o canto** (park, mesma lógica da pausa) e **espera** até:
  - **Resolver → Resolvido → Retomar**, ou
  - **Skip** (avançar no arquivo até próximo objeto e continuar), ou
  - **Cancelar** (stop).

### 1.2 Endpoints

| Endpoint | Método | Descrição | Checklist |
|----------|--------|-----------|-----------|
| `/api/printer/failure` | POST | Receber notificação de falha. Body: `{ "code": "...", "message": "...", "source": "octoprint" }` (flexível). Se houver impressão ativa: marcar falha e pausar. Também pode ser disparado automaticamente pela detecção serial. | [x] |
| `/api/printer/skip-object` | POST | Pular item. Body opcional: `{ "object_id": 1 }`. Sem body = pular "objeto atual". A thread usa o `object_id` para pular apenas aquele objeto específico (ver seção 8.2). | [x] |
| `/api/printer/failure/resolve` | POST | "Estou resolvendo" — registra `action: "resolving"` no log. **Não retoma a impressão.** | [x] |
| `/api/printer/failure/resolved` | POST | "Problema resolvido — Retomar" — limpar falha e retomar (reutilizar lógica de resume). | [x] |
| Cancelar | — | Reutilizar `POST /api/printer/stop`: parar impressão e limpar estado de falha. | [x] |

- [x] **`GET /api/printer/status`:** incluir quando em falha:
  - `state: "failure"` (ou manter `paused` e adicionar `failure_detected: true`)
  - `failure_message`, `failure_code` (se houver)

### 1.3 Thread de impressão

- [x] Dentro do loop da thread (`run_print_job`):
  - Se `print_failure_detected`: entrar em loop de espera (como no `print_paused`), sem enviar mais linhas. O bico faz park (sobe Z, vai para o canto).
  - Quando receber **skip** (flag/estado): lógica baseada em `object_counter` (ver seção 8.2):
    - Com `object_id`: pula apenas as linhas do objeto especificado.
    - Sem `object_id`: avança até o próximo comentário `object` ou `layer`.
  - Quando receber **resolved**: mesmo comportamento do resume (continuar de onde parou, com reaquecimento se necessário).
- [x] Registrar em log (tabela `print_failure_log`) cada ação.

### 1.4 Persistência e log

- [x] **Tabela** `print_failure_log`:
  - `id`, `print_job_id`, `occurred_at`, `failure_code` (nullable), `failure_message` (nullable), `action` (`detected` | `skipped` | `resolving` | `resolved` | `cancelled`), `object_index_or_name` (nullable).
- [x] Registrar cada ação: detected, skip, resolving, resolved, cancel.
- [x] **Endpoint** `GET /api/printer/failure-history`: listar últimas falhas do job atual / gerais para exibir no front.

### 1.5 Parse do G-code para objetos (visualização da mesa + skip)

- [x] **Marcadores de objeto:** Orca/Prusa com "Label Objects" inserem comentários:
  - `; printing object <nome>` → início de um novo objeto
  - `; stop printing object <nome>` → fim do objeto atual
- [x] **Marcadores ignorados:** `;LAYER`, `;LAYER_CHANGE`, `;LAYER:` — esses **não** criam objetos na visualização (evita criar centenas de "objetos" falsos).
- [x] **Algoritmo:** percorrer o arquivo; a cada `; printing object`, abrir novo objeto; coletar X,Y de todos os G0/G1 até o `; stop printing object` e calcular `min_x`, `min_y`, `max_x`, `max_y` (bounding box em mm).
- [x] **Armazenar:** lista de objetos com `id` (índice base 0), `name` (se houver), `min_x`, `min_y`, `max_x`, `max_y`.
- [x] **Skip por objeto:** dado `object_id`, a thread rastreia qual objeto está sendo impresso via `object_counter` e pula apenas as linhas do objeto correspondente (ver seção 8.2).
- [x] **Endpoint** `GET /api/printer/bed-preview`:
  - Retornar `bed: { width_mm, depth_mm }`,
  - `objects: [ { id, name?, min_x, min_y, max_x, max_y }, ... ]`,
  - opcionalmente `current_object_id`.
- [x] Se o G-code **não tiver** marcadores de objeto: `objects: []`; o front mostra só "Pular item atual".

---

## 2. Frontend (React — `front-react/`)

### 2.1 Dashboard — estado de falha

- [x] Se `status.failure_detected === true`:
  - Exibir card **"Falha detectada"** com `failure_message` (e `failure_code` se existir).
  - Texto explicativo abaixo dos botões: *"Resolver: clique em 'Estou resolvendo' se for mexer na impressora; quando terminar, clique em 'Problema resolvido — Retomar' para a impressão continuar."*
  - Botões: **Pular item com defeito** | **Estou resolvendo** | **Problema resolvido — Retomar** | **Cancelar**.
- [x] **Estou resolvendo** → `POST /api/printer/failure/resolve` (registra no log; **não** retoma).
- [x] **Problema resolvido — Retomar** → `POST /api/printer/failure/resolved` (backend retoma a impressão).
- [x] **Cancelar** → reutilizar fluxo do botão Parar (`POST /api/printer/stop`).
- [x] **Pular item com defeito** → ver 2.2.

### 2.2 Fluxo "Pular item" e visualização da mesa

- [x] Ao clicar em "Pular item com defeito", se houver impressão ativa:
  - Chamar `GET /api/printer/bed-preview`.
  - Se `objects.length > 0`: abrir modal **"Escolher peça a pular"** com vista 2D.
  - Se `objects.length === 0`: mostrar apenas botão **"Pular item atual"**.
- [x] **Vista 2D da mesa (SVG):**
  - Retângulo = cama (`bed.width_mm` x `bed.depth_mm`).
  - Escala: mm → pixels (proporcional ao container).
  - Cada objeto = retângulo com bounding box em mm.
  - **Eixo Y invertido:** `svgY = depth_mm - maxY` (para corresponder à orientação real da mesa).
  - Clique em retângulo → seleciona objeto → botão **"Pular este objeto"** → `POST /api/printer/skip-object` com `{ "object_id": id }`.

### 2.3 Status e histórico

- [x] No dashboard: indicador **"Itens pulados nesta impressão: N"** (quando N > 0).
- [x] Botão **"Ver histórico de falhas"** que abre modal com lista de entradas (data/hora, ação, mensagem, código, objeto).

### 2.4 Hook e tipos

- [x] No hook do dashboard: estado e funções para falha.
- [x] Tipos TypeScript: `PrinterStatus` estendido com `failure_detected`, `failure_message`, `failure_code`, `skipped_objects_count`; tipo para resposta de `bed-preview` e histórico.

---

## 3. Mock e testes (front)

- [x] Em `front-react/src/mock/api.ts`:
  - Mocks para todos os endpoints de falha, skip, resolve, resolved, bed-preview, failure-history.
  - Mock de `bed-preview` com 3 objetos e bbox em mm para testar a grade 2D.

---

## 4. Ordem sugerida de implementação

1. **Backend:** estado de falha + detecção automática na serial + incluir no status.
2. **Backend:** `POST /api/printer/skip-object` com lógica de object_counter + tabela `print_failure_log`.
3. **Backend:** `failure/resolve` (registra no log), `failure/resolved` (retoma) e integração com resume/stop.
4. **Backend:** parse do G-code (apenas marcadores de objeto, não LAYER) + `GET /api/printer/bed-preview`.
5. **Frontend:** card "Falha detectada" + botões ("Estou resolvendo", "Problema resolvido — Retomar", etc.).
6. **Frontend:** modal "Escolher peça a pular" com grade 2D (SVG, Y invertido) e skip com object_id.
7. **Frontend:** indicador "Itens pulados: N" e modal "Histórico de falhas".
8. **Mock:** cenários de falha e bed-preview para teste sem impressora.

---

## 5. Integração OctoPrint (futura)

- O payload de `POST /api/printer/failure` é genérico para que scripts ou OctoPrint chamem esse endpoint ao detectar erro.
- Com a detecção automática pela serial, OctoPrint **não é obrigatório** — é apenas uma fonte adicional.

---

## 6. Observações

- **Bambu A1 / A1 mini:** não suportam skip de objeto no firmware; o sistema pula no G-code mas o efeito físico pode variar.
- **FlashForge AD5X:** já suporta pular; validar com evidência em vídeo.
- **Visualização da mesa:** prévia 2D a partir de metadados do G-code (objetos + bbox, com Y invertido); sem câmera no escopo desta task.

---

## 7. Detecção automática de erros (serial)

**Implementado em:** `core/printer.py` (função `_maybe_mark_failure_from_printer_line`).

O sistema detecta automaticamente erros críticos da impressora ao ler cada linha da comunicação serial, **sem depender de chamadas externas** (curl/OctoPrint). A função é chamada dentro de `send_gcode()` a cada resposta recebida.

### 7.1 Erros detectados

| Padrão na serial | Código atribuído | Exemplo |
|---|---|---|
| `Error:` (genérico) | `FIRMWARE` | `Error:Printer halted` |
| `Thermal Runaway` | `THERMAL_RUNAWAY` | Superaquecimento descontrolado |
| `MINTEMP triggered` | `MINTEMP` | Temperatura abaixo do mínimo |
| `MAXTEMP triggered` | `MAXTEMP` | Temperatura acima do máximo |
| `Heating failed` | `HEATING_FAILED` | Aquecedor não atingiu temperatura |
| `Printer halted` / `kill()` | `HALTED` | Impressora parou por erro fatal |
| `Homing failed` | `HOMING_FAILED` | Falha no homing |
| `Probing failed` | `PROBING_FAILED` | Falha no nivelamento |
| `Emergency stop` / `stop called` | `EMERGENCY_STOP` | Parada de emergência |

### 7.2 Falsos positivos ignorados

Erros de comunicação serial comuns que o Marlin corrige sozinho **não disparam falha**:

- `Error:checksum`, `Error:line number`, `Error:no line number`, `Error:no checksum`, `format error`

### 7.3 Falha por comunicação perdida

Se a impressora **não responder a 3 comandos consecutivos** (timeout em `send_gcode()`), o sistema dispara falha com código `COMM_FAILURE`. Um comando falho isolado é tolerado; 3 seguidos indica problema real. Configurável via `st.CONSECUTIVE_FAILURES_THRESHOLD`.

### 7.4 Comportamento ao detectar falha

1. `print_failure_detected = True`, `print_paused = True`
2. A thread de impressão entra no loop de pausa — **o bico sobe e vai para o canto** (park), igual à pausa manual.
3. O Dashboard mostra o card **"Falha detectada"** com a mensagem real da impressora.
4. A falha é registrada automaticamente na tabela `print_failure_log`.

O endpoint `POST /api/printer/failure` continua disponível para uso externo (scripts, OctoPrint futuro), mas não é mais a única forma de disparar falha.

---

## 8. Regras de negócio — fluxo de botões e skip

### 8.1 Botões do card "Falha detectada"

| Botão no front | Endpoint | O que acontece | Quando usar |
|---|---|---|---|
| **Pular item com defeito** | Abre modal de visualização da mesa | Permite escolher qual peça pular (se o G-code tiver Label Objects) ou pular o item atual | A peça deu defeito e o usuário quer continuar sem ela |
| **Estou resolvendo** | `POST /api/printer/failure/resolve` | Registra `action: "resolving"` no log. **Não retoma a impressão.** | O usuário vai mexer fisicamente na impressora |
| **Problema resolvido — Retomar** | `POST /api/printer/failure/resolved` | Limpa a falha, retoma a impressão de onde parou (com reaquecimento se necessário). | O usuário terminou de resolver e quer continuar |
| **Cancelar impressão** | `POST /api/printer/stop` | Para a impressão e limpa o estado de falha | O usuário desistiu da impressão |

**Fluxo típico "resolver":** Falha detectada → "Estou resolvendo" (mexe na impressora) → "Problema resolvido — Retomar" (impressão continua).

### 8.2 Regras do skip de objetos

#### Parser do G-code (`parse_gcode_objects_for_bed`)

Identifica objetos **apenas** por marcadores do OrcaSlicer/PrusaSlicer com **Label Objects** ativo:

- **`; printing object <nome>`** → início de um novo objeto
- **`; stop printing object <nome>`** → fim do objeto atual

**Marcadores de camada** (`;LAYER`, `;LAYER_CHANGE`, etc.) **são ignorados** para efeito de visualização da mesa. Um G-code com 2 peças e 100 camadas gera apenas 2 objetos, não 200+.

#### Visualização da mesa (SVG)

- Eixo **Y invertido**: no G-code Y=0 é a frente da mesa (embaixo), mas no SVG Y=0 é o topo. O front calcula `svgY = depth_mm - maxY` para que a posição visual corresponda à posição real no OrcaSlicer.
- Cada objeto é um retângulo com bounding box (min_x, min_y, max_x, max_y) em mm.

#### Skip com `object_id` selecionado

Quando o usuário escolhe um objeto específico na mesa:

1. O front envia `POST /api/printer/skip-object` com `{ "object_id": N }` (índice base 0).
2. A thread de impressão rastreia o objeto atual via `object_counter` (incrementado a cada `; printing object`).
3. **Se `object_counter - 1 == skip_id`:** todas as linhas daquele objeto são puladas (não enviadas).
4. **Quando `object_counter - 1 > skip_id`:** o skip termina e a impressão continua normalmente no próximo objeto.
5. O restante dos objetos continua sendo impresso.

#### Skip sem `object_id` (sem Label Objects)

Quando o G-code não tem marcadores de objeto (`objects: []`), o front mostra "Pular item atual":

1. `POST /api/printer/skip-object` sem body (`object_id = None`).
2. A thread pula linhas até encontrar o próximo comentário com `object` ou `layer`, depois continua.

### 8.3 Label Objects — como ativar no OrcaSlicer

No OrcaSlicer: **Print settings** (Configurações de impressão) → seção **"Output options"** ou **"Opções de saída"** → ativar **"Label objects"**. Também pode ser encontrado buscando "label" na barra de pesquisa.

---

## 9. Implementação concluída — resumo

**Status:** Todas as tarefas desta documentação foram implementadas (backend + front React + mock + detecção automática serial).

**Entregas:**
- Backend: detecção automática de erros na serial (firmware + comunicação perdida), endpoints completos, tabela `print_failure_log`, thread com park na falha e skip por objeto específico.
- Frontend: card "Falha detectada" com texto explicativo, botões renomeados ("Estou resolvendo" + "Problema resolvido — Retomar"), modal com vista 2D da mesa (SVG, eixo Y invertido), seleção de objeto, indicador "Itens pulados: N", modal "Histórico de falhas".
- Parser: usa apenas marcadores "; printing object" / "; stop printing object" (ignora "; LAYER").
- Mock: respostas para todos os novos endpoints e status com/sem falha.

---

## 10. O que o cliente precisa testar para finalizar a entrega

### 10.1 Pré-requisitos

- Sistema (front React + backend) rodando e conectado à impressora.
- Um arquivo G-code em impressão. Para testar a **visualização da mesa**, o G-code deve ter sido fatiado com **"Label Objects"** ativo no OrcaSlicer (Print settings → Output options → Label objects).

### 10.2 Cenários de teste

1. **Simular falha durante a impressão**
   - Enquanto uma impressão está em andamento, disparar uma falha:
     - **Opção A (curl):** `POST /api/printer/failure` com body `{ "message": "Falha de teste", "code": "TEST" }`.
     - **Opção B (automática):** em produção, a impressora envia erros pela serial e o sistema detecta sozinho.
   - **Validar:** card **"Falha detectada"** aparece; bico sobe e vai para o canto (park); botões ficam disponíveis.

2. **Resolver problema e retomar**
   - Clicar em **"Estou resolvendo"** (registra no histórico).
   - Resolver o problema fisicamente.
   - Clicar em **"Problema resolvido — Retomar"**.
   - **Validar:** card some, bico volta, impressão continua de onde parou.

3. **Pular item com defeito (sem escolher peça)**
   - Simular falha. Clicar em **"Pular item com defeito"**.
   - Se o G-code não tiver Label Objects → **"Pular item atual"**.
   - **Validar:** impressão continua; contador de itens pulados aumenta.

4. **Pular item com defeito (escolhendo peça na mesa)**
   - G-code com **Label Objects** (várias peças). Simular falha → **"Pular item com defeito"**.
   - **Validar:** modal com vista 2D da mesa (posições como no OrcaSlicer).
   - Selecionar peça → **"Pular este objeto"**.
   - **Validar:** apenas aquele objeto é pulado; o restante continua.

5. **Cancelar impressão em falha**
   - Simular falha → **"Cancelar impressão"**.
   - **Validar:** impressão para; estado volta para "Ocioso".

6. **Histórico de falhas**
   - Após falha/skip → **"Ver histórico de falhas"**.
   - **Validar:** modal com lista de entradas (data/hora, ação, mensagem, código, objeto).

### 10.3 Evidência solicitada

- **Vídeo** mostrando: impressão → falha detectada (card + park) → pelo menos um fluxo (retomar ou pular com escolha) → (opcional) histórico.

### 10.4 Observações

- **Detecção automática:** o sistema detecta erros do firmware automaticamente (thermal runaway, heating failed, etc.). O curl é apenas para testes controlados.
- **Bambu A1 / A1 mini:** não suportam skip no firmware; o sistema pula no G-code mas o efeito pode variar.
- **FlashForge AD5X:** suporta pular; validação com vídeo é a evidência ideal.
- **Label Objects:** necessário para visualização da mesa com várias peças. Sem isso, o modal mostra apenas "Pular item atual".

---

*Documento da Task 4 — Detecção e skip de falhas. Implementação concluída; pendente validação do cliente conforme seção 10.*
