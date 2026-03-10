## Fluxo de Pausa / Retomada — Front + Backend

### 1. Visão geral

- **Frontend (React)**: expõe botões `Pausar` e `Retomar` na página `Dashboard`.
- **Backend (Flask)**: implementa os endpoints:
  - `POST /api/printer/pause`
  - `POST /api/printer/resume`
- **Thread de impressão** (`core/print_engine.run_print_job`): é quem de fato envia G-code, salva estado da pausa e executa os movimentos de park/unpark (incluindo lift de Z).

---

### 2. Frontend

**Arquivos principais**

- `front-react/src/pages/dashboard/Dashboard.tsx`
- `front-react/src/pages/dashboard/hook.tsx`

**Pausar**

- Botão **Pausar** (`Dashboard.tsx`):
  - Chama `openPauseModal()` → abre modal de opções de pausa.
  - Modal permite escolher uma `PauseOption`:
    - `"keep_temp"` — manter temperaturas.
    - `"cold"` — pausa fria (desliga aquecedores).
    - `"filament_change"` — troca de filamento (M600).
  - Ao confirmar, chama `confirmPause()` (em `hook.tsx`), que:
    - Faz `POST /api/printer/pause` com body:
      - `{ "option": "keep_temp" | "cold" | "filament_change" }`.
    - Em seguida chama `fetchStatus()` para atualizar o estado no dashboard.

**Retomar**

- Botão **Retomar** (`Dashboard.tsx`):
  - Chama `resume()` (em `hook.tsx`), que:
    - Faz `POST /api/printer/resume` (sem body).
    - Em seguida chama `fetchStatus()`.

**Observações**

- O frontend **não envia G-code diretamente**, apenas dispara as rotas HTTP acima.
- Toda a lógica de movimentação (eixo Z, XY), park/unpark e reaquecimento é responsabilidade do backend/firmware.

---

### 3. Backend — `/api/printer/pause`

**Arquivo**: `routes/printer_api.py`

- Endpoint:
  - Valida sessão (`user_id`).
  - Lê o JSON opcional do body:
    - Campo `option` ∈ `{ "keep_temp", "cold", "filament_change" }`.
  - Atualiza estados globais em `core.state`:
    - `st.pause_option_requested = option`
    - `st.print_paused = True`
    - `st.print_paused_by_filament = False`
  - Não envia G-code diretamente; apenas marca que a impressão deve pausar na thread.

**Ponto importante**

- Quem **de fato executa** o lift de Z e move o bico para o canto (park) é a thread de impressão (`run_print_job`), ao perceber `st.print_paused = True`.

---

### 4. Backend — comportamento ao PAUSAR (thread de impressão)

**Arquivo**: `core/print_engine.py`, função `run_print_job`.

Quando `st.print_paused == True`, dentro do loop principal de envio de G-code:

1. **Salvar estado atual da impressão**:
   - Obtém posição atual via `get_current_position()`:
     - `pos_x`, `pos_y`, `pos_z`, `pos_e`.
   - Lê temperaturas alvo via `M105`:
     - `target_nozzle`, `target_bed`.
   - Determina a opção de pausa:
     - `option = st.pause_option_requested` (ou `"keep_temp"` se for pausa por falta de filamento).
   - Salva em memória (`st._pause_mem_state`):
     - Posição, temperaturas alvo e `option`.
   - Lê `file_offset = f.tell()` e salva tudo em banco (tabela `print_pause_state`), incluindo:
     - `print_job_id`, `gcode_filename`, `file_offset`, `pos_x`, `pos_y`, `pos_z`, `pos_e`, `target_nozzle`, `target_bed`, `pause_option`.

2. **Executar park (estacionar o bico)**:
   - Comandos enviados:
     - `G91` — modo relativo.
     - `G1 E-PAUSE_RETRACT_MM F300` — recuo de filamento.
     - `G1 ZPAUSE_Z_LIFT_MM F300` — **sobe o eixo Z em uma altura configurável** (`PAUSE_Z_LIFT_MM`), para afastar o bico da peça.
     - `G90` — volta para coordenadas absolutas.
     - `G0 XPAUSE_PARK_X YPAUSE_PARK_Y F3000` — **move XY para o canto da mesa** (posição de estacionamento).

3. **Aplicar efeito da opção de pausa**:
   - `"keep_temp"`:
     - Não desliga aquecedores; tudo continua na temperatura de impressão.
   - `"cold"`:
     - Envia `M104 S0` (desliga bico) e `M140 S0` (desliga mesa).
   - `"filament_change"`:
     - Envia `M600` (macro de troca de filamento), se suportada pelo firmware.

4. **Laço de espera**:
   - Enquanto `st.print_paused` permanecer `True`, a thread fica em loop de “pausado”, sem enviar novas linhas de G-code, até que o usuário peça retomada.

**Resumo visual — PAUSE**

- Front:
  - `POST /api/printer/pause { option }`.
- Back (thread):
  - Salva estado (posição, temps, offset de arquivo, opção).
  - Recuo de filamento (`E-PAUSE_RETRACT_MM`).
  - **Sobe Z em `PAUSE_Z_LIFT_MM`**.
  - Vai para canto (`PAUSE_PARK_X`, `PAUSE_PARK_Y`).
  - Se necessário, desliga aquecedores ou envia `M600`.

---

### 5. Backend — `/api/printer/resume`

**Arquivo**: `routes/printer_api.py`

- Endpoint:
  - Valida sessão.
  - Limpa flags de falha:
    - `st.print_failure_detected = False`
    - `st.current_failure_message = None`
    - `st.current_failure_code = None`
  - Carrega estado de pausa:
    1. Primeiro tenta no banco (`print_pause_state`) usando `st.current_pause_state_job_id`.
    2. Se não encontrar, tenta `st._pause_mem_state`.
  - Do estado carregado obtém:
    - `target_nozzle`, `target_bed`, `pause_option`, `pos_x`, `pos_y`, `pos_z`.

**Reaquecimento na retomada**

- Se existirem alvos de temperatura (`target_nozzle`/`target_bed` > 0), o backend:
  - Lê temperatura atual com `M105`.
  - Define se precisa reaquecer:
    - Opção `"cold"`:
      - Sempre reaquece até os alvos.
    - Opções não frias (`keep_temp`, `filament_change`):
      - Só reaquece se temperatura atual estiver abaixo do alvo menos `TEMP_REHEAT_MARGIN`.
  - Envia `M190`/`M140` para mesa e `M109`/`M104` para bico conforme necessário.

**Unpark (retornar à posição de impressão)**

- Se `pos_x`, `pos_y` e `pos_z` estiverem definidos:
  - Envia sequência:
    - `G90`
    - `G0 Xpos_x Ypos_y F3000` — **traz o bico de volta para XY da posição da pausa**.
    - `G0 Zpos_z F300` — **retorna Z para a altura exata em que a impressão estava no momento da pausa**.
    - `G91`
    - `G1 E+PAUSE_RETRACT_MM F300` — repondo o filamento que foi retraído ao pausar.
    - `G90`
  - Marca:
    - `st._pause_mem_state['valid'] = False`
    - `st.print_paused = False`
    - `st.print_paused_by_filament = False`
    - `st.current_pause_state_job_id = None`

**Resumo visual — RESUME**

- Front:
  - `POST /api/printer/resume`.
- Back:
  - Carrega estado de pausa (banco ou memória).
  - Reaquece bico/mesa se necessário.
  - **Volta XY para a posição salva da pausa**.
  - **Volta Z para a altura salva da pausa**.
  - Reverte o recuo de filamento (`E+PAUSE_RETRACT_MM`).
  - Libera a thread de impressão para continuar enviando G-code a partir do `file_offset` salvo.

---

### 6. Relação com o comportamento observado

- **Na pausa**:
  - O bico sobe um pouco (lift de Z) e vai para o canto da mesa.
  - Isso é realizado pela combinação de:
    - `G1 ZPAUSE_Z_LIFT_MM` (lift) + `G0 XPAUSE_PARK_X YPAUSE_PARK_Y` (park).
- **Na retomada**:
  - O backend não envia nenhum comando de “super lift” adicional de Z; ele apenas:
    - Volta XY para a posição da pausa.
    - Define Z para o valor absoluto `pos_z` que foi salvo em `M114`.
  - Qualquer comportamento extra de levantar Z de forma “brutal” na volta (por exemplo Z-hop adicional ou macros do firmware) vem de:
    - Configurações do G-code/fatiador (Z hop on travel).
    - Macros/recursos específicos do firmware Marlin.

---

### 7. Resumo da regra front/back

- **Front**:
  - Escolhe a opção de pausa e chama:
    - `POST /api/printer/pause { option }` → sinaliza pausa.
    - `POST /api/printer/resume` → sinaliza retomada.
  - Não mexe em Z, XY ou temperaturas diretamente.

- **Backend**:
  - `pause`:
    - Salva estado (posição, temps, offset).
    - Faz recuo de filamento.
    - **Sobe Z em `PAUSE_Z_LIFT_MM` e estaciona XY no canto configurado.**
    - Opcionalmente desliga aquecedores ou envia `M600`.
  - `resume`:
    - Carrega estado salvo.
    - Reaquece se necessário.
    - **Volta XY e Z para exatamente a posição de impressão em que a pausa ocorreu.**
    - Devolve o filamento retraído.
    - Libera a thread para continuar a impressão do ponto salvo.

