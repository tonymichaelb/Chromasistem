# Detecção e skip de falhas — guia de implementação

Guia para implementar a **Task 4**: receber erro da impressora, permitir pular peça, resolver problema → problema resolvido → retomar, ou cancelar. Inclui visualização da mesa para escolher qual peça pular quando houver várias.

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

- [x] **Variáveis globais** (em `app.py`, junto às de pause):
  - `print_failure_detected` (bool)
  - `current_failure_message` (str ou None)
  - `current_failure_code` (str ou None, opcional)
- [x] **Quando setar falha:**
  - Ao receber `POST /api/printer/failure` (notificação externa, ex. OctoPrint), ou
  - Ao usuário clicar em “Pular item com defeito” (falha “manual”) — nesse caso pode apenas abrir o fluxo de skip sem mensagem da impressora.
- [x] **Comportamento da thread de impressão:** quando `print_failure_detected` (ou estado “pausado por falha”), a thread **para** de enviar G-code e **espera** (como no pause), até:
  - **Resolver → Resolvido → Retomar**, ou
  - **Skip** (avançar no arquivo até próximo objeto e continuar), ou
  - **Cancelar** (stop).

### 1.2 Endpoints

| Endpoint | Método | Descrição | Checklist |
|----------|--------|-----------|-----------|
| `/api/printer/failure` | POST | Receber notificação de falha. Body: `{ "code": "...", "message": "...", "source": "octoprint" }` (flexível). Se houver impressão ativa: marcar falha e pausar. | [x] |
| `/api/printer/skip-object` | POST | Pular item. Body opcional: `{ "object_id": 1 }`. Sem body = pular “objeto atual”. Avançar no arquivo até próximo objeto (ou heurística) sem enviar linhas; continuar fila. | [x] |
| `/api/printer/failure/resolve` | POST | “Resolver problema” — marcar estado “resolvendo” (para UI/histórico). | [x] |
| `/api/printer/failure/resolved` | POST | “Problema resolvido” — limpar falha e retomar (reutilizar lógica de resume). | [x] |
| Cancelar | — | Reutilizar `POST /api/printer/stop`: parar impressão e limpar estado de falha. | [x] |

- [x] **`GET /api/printer/status`:** incluir quando em falha:
  - `state: "failure"` (ou manter `paused` e adicionar `failure_detected: true`)
  - `failure_message`, `failure_code` (se houver)

### 1.3 Thread de impressão

- [x] Dentro do loop da thread (`print_gcode_file`):
  - Se `print_failure_detected`: entrar em loop de espera (como no `print_paused`), sem enviar mais linhas.
  - Quando receber **skip** (flag/estado): avançar leitura do arquivo até o **próximo objeto** (ver 1.5) ou heurística (próximo `;LAYER` / bloco), **sem enviar** essas linhas; depois continuar enviando.
  - Quando receber **resolved**: mesmo comportamento do resume (continuar de onde parou).
- [x] Registrar em log (e na tabela de falhas) cada skip: “objeto X pulado”, `action: skipped`.

### 1.4 Persistência e log

- [x] **Tabela** `print_failure_log` (ou nome similar):
  - `id`, `print_job_id`, `occurred_at`, `failure_code` (nullable), `failure_message` (nullable), `action` (`skipped` | `resolved` | `cancelled`), `object_index_or_name` (nullable).
- [x] Registrar cada ação: skip, resolve, resolved, cancel.
- [x] **Endpoint** `GET /api/printer/failure-history` (ou dentro do status): listar últimas falhas do job atual / gerais para exibir no front.

### 1.5 Parse do G-code para objetos (visualização da mesa + skip)

- [x] **Marcadores de objeto:** Orca/Prusa com “Label Objects” inserem comentários no G-code (ex.: `; object`, `;OBJECT: nome`). Definir padrões a detectar (ex.: linha começando com `;` contendo `object` ou `OBJECT`).
- [x] **Algoritmo:** percorrer o arquivo; a cada marcador de objeto, abrir novo “objeto”; até o próximo marcador, coletar X,Y de todos os G0/G1 e calcular `min_x`, `min_y`, `max_x`, `max_y` (bounding box em mm).
- [x] **Armazenar:** lista de objetos com `id` (índice), `name` (se houver), `min_x`, `min_y`, `max_x`, `max_y`. Pode ser calculado ao iniciar o job ou sob demanda.
- [x] **Skip por objeto:** dado `object_id`, a thread avança no arquivo até passar todo o bloco daquele objeto (até o próximo marcador de objeto ou fim) sem enviar; depois continua.
- [x] **Endpoint** `GET /api/printer/bed-preview` (ou `/api/print-job/current/bed-objects`):
  - Retornar `bed: { width_mm, depth_mm }` (config impressora ou inferido do G-code),
  - `objects: [ { id, name?, min_x, min_y, max_x, max_y }, ... ]`,
  - opcionalmente `current_object_id` (objeto sendo impresso no momento).
- [x] Se o G-code **não tiver** marcadores de objeto: `objects: []` ou um único objeto “job inteiro”; o front pode mostrar só o botão “Pular item atual”.

---

## 2. Frontend (React — `front-react/`)

### 2.1 Dashboard — estado de falha

- [x] Se `status.state === "failure"` ou `status.failure_detected === true`:
  - Exibir card/barra **“Falha detectada”** com `failure_message` (e `failure_code` se existir).
  - Botões: **Pular item com defeito** | **Resolver problema** | **Problema resolvido** | **Cancelar**.
- [x] **Resolver problema** → `POST /api/printer/failure/resolve` (feedback: “Resolvendo…”).
- [x] **Problema resolvido** → `POST /api/printer/failure/resolved` (backend retoma).
- [x] **Cancelar** → reutilizar fluxo do botão Parar (`POST /api/printer/stop`).
- [x] **Pular item com defeito** → ver 2.2 (pode abrir modal com ou sem visualização da mesa).

### 2.2 Fluxo “Pular item” e visualização da mesa

**Fase 1 (MVP)**

- [x] Botão **“Pular item com defeito”** chama `POST /api/printer/skip-object` **sem** body (backend pula “objeto atual” por marcador ou heurística).
- [x] Modal de confirmação: “Pular o item atual e continuar o resto da impressão?”

**Fase 2 — Visualização da mesa**

- [x] Ao clicar em “Pular item com defeito”, se houver impressão ativa:
  - Chamar `GET /api/printer/bed-preview`.
  - Se `objects.length > 0`: abrir modal **“Escolher peça a pular”**.
- [x] **Vista 2D da mesa:**
  - Retângulo = cama (dimensões `bed.width_mm` x `bed.depth_mm`).
  - Escala: mm → pixels (proporcional para caber no canvas/container).
  - Cada objeto = retângulo em `(min_x, min_y)` com tamanho `(max_x - min_x, max_y - min_y)` em mm, convertido para px.
  - Implementar com **SVG** ou **canvas** (um `<rect>` por objeto).
- [x] **Interação:** clique em um retângulo → seleciona esse objeto (guardar `object_id` no state). Botão “Pular este objeto” → `POST /api/printer/skip-object` com `{ "object_id": id }`.
- [x] Se `objects.length === 0`: não mostrar grade; mostrar apenas “Pular item atual” (Fase 1).

### 2.3 Status e histórico

- [x] No `GET /api/printer/status` (ou resposta do backend): usar `skipped_objects_count`, `failure_detected`, `failure_message`.
- [x] No dashboard: indicador **“Itens pulados nesta impressão: N”** (quando N > 0).
- [x] Botão ou link **“Histórico de falhas”** que abre lista (dados de `GET /api/printer/failure-history` ou equivalente).

### 2.4 Hook e tipos

- [x] No hook do dashboard: adicionar estado e funções para falha (falha ativa, mensagem, ações resolve/resolved/skip/cancel).
- [x] Tipos TypeScript: estender `PrinterStatus` com `failure_detected`, `failure_message`, `failure_code`, `state: "failure"`, `skipped_objects_count`; tipo para resposta de `bed-preview` e para itens do histórico.

---

## 3. Mock e testes (front)

- [x] Em `front-react/src/mock/api.ts`:
  - Resposta de `GET /api/printer/status` com campos de falha; objeto `printerStatusWithFailure` para simular estado de falha (trocar no retorno para testar).
  - Mocks para `POST /api/printer/failure`, `skip-object`, `failure/resolve`, `failure/resolved`.
  - Mock para `GET /api/printer/bed-preview` com `objects` com 3 itens e bbox em mm para testar a grade 2D.
  - Mock para `GET /api/printer/failure-history` com entradas de exemplo.

---

## 4. Ordem sugerida de implementação

Usar os checkboxes acima na ordem abaixo para não se perder.

1. **Backend:** estado de falha + `POST /api/printer/failure` + incluir `failure_detected` e mensagem no `GET /api/printer/status`.
2. **Backend:** `POST /api/printer/skip-object` na thread (parser de `;OBJECT` ou heurística de camada) + tabela `print_failure_log` e registro de skip.
3. **Backend:** `failure/resolve`, `failure/resolved` e integração com resume/stop.
4. **Backend:** parse do G-code para lista de objetos + `GET /api/printer/bed-preview`.
5. **Frontend:** no Dashboard, estado “failure” + botões (Pular item, Resolver, Resolvido, Cancelar) e chamadas às novas APIs.
6. **Frontend:** indicador “Itens pulados: N” e tela/modal de histórico de falhas.
7. **Frontend:** modal “Escolher peça a pular” com grade 2D da mesa (SVG/canvas) e `POST skip-object` com `object_id`.
8. **Mock:** cenários de falha e bed-preview no `api.ts` para testar sem impressora.

---

## 5. Integração OctoPrint (futura)

- O payload de `POST /api/printer/failure` deve ser genérico para que, quando o cliente definir o formato, o OctoPrint (ou script no Pi) chame esse endpoint ao detectar erro na impressora.
- Documentar no código ou em doc de API o contrato esperado (ex.: `code`, `message`, `source`).

---

## 6. Observações

- **Bambu A1 / A1 mini:** não suportam skip de objeto; a funcionalidade pode não ter efeito físico nesses modelos (documentar para o usuário).
- **FlashForge AD5X:** já suporta pular; validar com evidência em vídeo.
- **Visualização da mesa:** prévia da mesa no front a partir de metadados do G-code (objetos + bbox); sem câmera no escopo desta task.

---

## 7. Implementação concluída — resumo

**Status:** Todas as tarefas desta documentação foram implementadas (backend + front React + mock).

**Entregas:**
- Backend: estado de falha, endpoints `failure`, `failure/resolve`, `failure/resolved`, `skip-object`, `failure-history`, `bed-preview`; tabela `print_failure_log`; thread de impressão com espera em falha e skip até próximo objeto/camada.
- Frontend: dashboard com card “Falha detectada”, botões (Pular item, Resolver problema, Problema resolvido, Cancelar), modal “Pular item com defeito” com vista 2D da mesa (SVG) e seleção de objeto, indicador “Itens pulados: N”, modal “Histórico de falhas”.
- Mock: respostas para todos os novos endpoints e status com/sem falha para teste sem impressora.

---

## 8. O que o cliente precisa testar para finalizar a entrega

Para considerar a **Task 4 (Detecção e skip de falhas)** finalizada, o cliente deve validar os pontos abaixo e, de preferência, **gravar um vídeo** como evidência.

### 8.1 Pré-requisitos

- Sistema (front React + backend) rodando e conectado à impressora (ou teste com simulação de falha).
- Um arquivo G-code em impressão (ou pronto para iniciar). Para testar a **visualização da mesa**, o G-code deve ter sido fatiado com **“Label Objects”** ativo (OrcaSlicer/PrusaSlicer), para que apareçam peças no modal.

### 8.2 Cenários de teste

1. **Simular falha durante a impressão**
   - Enquanto uma impressão está em andamento, disparar uma falha:
     - **Opção A:** chamar a API `POST /api/printer/failure` com body `{ "message": "Falha de teste", "code": "TEST" }` (por exemplo via Postman, curl ou script).
     - **Opção B:** quando a integração com OctoPrint estiver disponível, gerar o erro pela impressora/OctoPrint.
   - **Validar:** no dashboard aparece o card **“Falha detectada”** com a mensagem, o estado muda para “Falha detectada” e os botões **Pular item com defeito**, **Resolver problema**, **Problema resolvido — Retomar** e **Cancelar** ficam disponíveis.

2. **Resolver problema e retomar**
   - Com a impressão em estado de falha (passo 1), clicar em **“Resolver problema”** (apenas registra a ação).
   - Em seguida clicar em **“Problema resolvido — Retomar”**.
   - **Validar:** o card de falha some, o estado volta a “Imprimindo” e a impressão continua de onde parou.

3. **Pular item com defeito (sem escolher peça)**
   - Simular falha de novo (passo 1). Clicar em **“Pular item com defeito”**.
   - Se o G-code **não** tiver marcadores de objeto, no modal deve aparecer **“Pular item atual”**; clicar nesse botão.
   - **Validar:** a impressão continua; o contador **“Itens pulados nesta impressão”** aumenta em 1 (quando aplicável).

4. **Pular item com defeito (escolhendo peça na mesa)**
   - Com um G-code que tenha **Label Objects** (várias peças), simular falha e clicar em **“Pular item com defeito”**.
   - **Validar:** abre o modal com a **vista 2D da mesa** (retângulos por peça).
   - Clicar em **uma peça** (retângulo) para selecioná-la e em seguida em **“Pular este objeto”**.
   - **Validar:** a impressão segue sem aquele objeto; o contador de itens pulados atualiza; o modal fecha.

5. **Cancelar impressão em falha**
   - Simular falha e clicar em **“Cancelar impressão”** (e confirmar).
   - **Validar:** a impressão para; o estado volta para “Ocioso” ou “Parado”; o card de falha some.

6. **Histórico de falhas**
   - Após ter ocorrido pelo menos uma falha/skip na sessão (ou em job anterior), clicar em **“Ver histórico de falhas”** (no card de falha) ou em **“Histórico”** (ao lado de “Itens pulados nesta impressão”).
   - **Validar:** abre o modal **“Histórico de falhas”** com lista de entradas (data/hora, ação, mensagem, código, objeto quando houver).

### 8.3 Evidência solicitada

- **Vídeo** mostrando:
  - uma impressão em andamento;
  - a falha sendo detectada (card “Falha detectada” e botões);
  - pelo menos um dos fluxos: **Retomar** (resolver + resolvido) ou **Pular item** (com ou sem escolha de peça na mesa);
  - (opcional) abertura do **Histórico de falhas** com registros visíveis.

### 8.4 Observações para o cliente

- **Bambu A1 / A1 mini:** não suportam skip de objeto no firmware; o sistema permite marcar e pular no G-code, mas o efeito físico pode variar.
- **FlashForge AD5X:** suporta pular; a validação com vídeo nesse modelo é a evidência ideal para a entrega.
- **Label Objects:** para a “visualização da mesa” mostrar várias peças, o arquivo G-code precisa ter sido fatiado com a opção **Label Objects** ativa no OrcaSlicer/PrusaSlicer. Sem isso, o modal ainda permite **“Pular item atual”** (avanço até o próximo marcador de objeto/camada no G-code).

---

*Documento da Task 4 — Detecção e skip de falhas. Implementação concluída; pendente validação do cliente conforme seção 8.*
