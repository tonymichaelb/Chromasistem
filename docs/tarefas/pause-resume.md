# Pause / Resume — resumo da implementação

Resumo do que foi feito na **Task 3**: pausar a impressão no meio, salvar estado (posição, temperatura, ponto do G-code) e retomar de onde parou. O backend usa a mesma via serial já usada pelo Chromasistem; o frontend ganhou opções ao pausar e exibição clara do estado.

---

## 1. Visão geral

- **Pausar:** o usuário clica em Pausar no dashboard → abre um modal com 3 opções → ao confirmar, a thread de impressão para de enviar linhas, salva o estado atual e (conforme a opção) mantém ou desliga temperaturas.
- **Retomar:** o usuário clica em Retomar →, se a pausa foi “fria”, o backend reaquece bico e mesa e em seguida a thread continua enviando o G-code do ponto salvo.

Tudo pela mesma comunicação serial (Python → impressora); não é necessário reiniciar o servidor para retomar.

---

## 2. Backend

### 2.1 Persistência do estado

- Tabela **`print_pause_state`**: guarda, por pausa, `print_job_id`, nome do arquivo G-code, **offset no arquivo** (`file_offset`), posição **X, Y, Z, E** (via M114), temperaturas alvo do bico e da mesa (via M105) e a **opção** escolhida (`keep_temp`, `cold`, `filament_change`).
- A **thread** que envia o G-code, ao entrar em pausa, chama M114 e M105, lê `f.tell()` do arquivo e grava uma linha nessa tabela. Assim, retomar é continuar a leitura do arquivo a partir desse offset (o arquivo segue aberto na thread).

### 2.2 Opções de pausa

| Opção               | Comportamento |
|---------------------|----------------|
| **Manter temperatura** | Nenhum comando extra; bico e mesa seguem na temperatura de impressão. |
| **Pausa fria**      | Envia M104 S0 e M140 S0 (desliga aquecedores). Ao retomar, reaquece com M109/M190 usando os alvos salvos. |
| **Troca de filamento** | Envia M600 (se a impressora suportar). |

### 2.3 APIs

- **`POST /api/printer/pause`** — Body opcional: `{ "option": "keep_temp" | "cold" | "filament_change" }`. Seta a opção e a flag de pausa; a thread é quem salva o estado e aplica cold/M600.
- **`POST /api/printer/resume`** — Limpa a pausa; se o último estado salvo for pausa fria, reaquece (M140/M190 e M104/M109) e depois a thread continua.
- **`GET /api/printer/status`** — Inclui `state: "paused"` quando há impressão em andamento e a flag de pausa está ativa.

---

## 3. Frontend (dashboard)

- **Estado:** exibe **Imprimindo**, **Pausado** ou **Ocioso** conforme o `state` retornado pela API de status.
- **Pausar:** ao clicar, abre um **modal** com as 3 opções (manter temperatura, pausa fria, troca de filamento). Só ao clicar em “Pausar” no modal é enviado o POST com o `option` escolhido.
- **Retomar:** um clique envia POST para `/api/printer/resume`.
- **Botões:** Pausar habilitado só quando está imprimindo; Retomar, só quando está pausado; Parar, quando imprimindo ou pausado (evita cliques sem efeito).

---

## 4. Resumo

- Estado de pausa salvo em **`print_pause_state`** (offset no G-code, posição XYZE, temperaturas alvo, opção).
- **Três opções de pausa:** manter temperatura (padrão), pausa fria (desliga e reaquece ao retomar), troca de filamento (M600).
- **Retomar** = continuar o envio do arquivo a partir do offset salvo (e reaquecer antes, se foi pausa fria).
- **Frontend:** modal ao pausar, estado “Pausado”/“Imprimindo”/“Ocioso” e botões habilitados conforme o estado.

Referência da tarefa: [tasks.md](tasks.md) (seção 3).

---

## 5. Tabelas (banco de dados)

Foi criada **uma nova tabela**; nenhuma tabela existente foi alterada.

### `print_pause_state` (nova)

Registro do estado a cada pausa (uma linha por pausa).

| Coluna           | Tipo    | Descrição |
|------------------|---------|-----------|
| `id`             | INTEGER | Chave primária, autoincremento. |
| `print_job_id`   | INTEGER | FK para `print_jobs.id`. |
| `gcode_filename` | TEXT    | Nome do arquivo G-code (ex.: nome original). |
| `file_offset`    | INTEGER | Posição no arquivo (`f.tell()`) para retomar. |
| `pos_x`          | REAL    | Posição X (M114), opcional. |
| `pos_y`          | REAL    | Posição Y (M114), opcional. |
| `pos_z`          | REAL    | Posição Z (M114), opcional. |
| `pos_e`          | REAL    | Posição E (M114), opcional. |
| `target_nozzle`  | REAL    | Temperatura alvo do bico (M105), para reaquecer na retomada. |
| `target_bed`     | REAL    | Temperatura alvo da mesa (M105), para reaquecer na retomada. |
| `pause_option`   | TEXT    | `keep_temp`, `cold` ou `filament_change`. Default: `keep_temp`. |
| `created_at`     | TIMESTAMP | Data/hora da pausa (default: CURRENT_TIMESTAMP). |
