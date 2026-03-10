# Fatiador integrado — guia de uso e teste

Guia para o cliente utilizar e validar a **Task 5**: enviar um modelo 3D (.stl ou .obj) pela interface do Croma, gerar o G-code com o OrcaSlicer e enviar para impressão (ou só salvar em Arquivos).

**Referências:** [tasks.md](tasks.md) (seção 5), [duvidas-respostas.md](duvidas-respostas.md) (integração do fatiador).

---

## 1. O que é

- Na tela **Fatiador** do Croma você envia um arquivo **.stl** ou **.obj**.
- O servidor (backend) chama o **OrcaSlicer** em modo linha de comando, gera o **G-code** e grava na lista de arquivos do sistema.
- Você pode então **enviar para impressão** direto da tela ou ir em **Arquivos** e imprimir de lá.
- O OrcaSlicer **não abre janela** — tudo roda em segundo plano no servidor.

---

## 2. Pré-requisitos

### OrcaSlicer instalado

O OrcaSlicer precisa estar instalado no **mesmo computador** onde roda o backend do Croma (ou no servidor que hospeda a API).

| Plataforma | Caminho padrão detectado automaticamente | Notas |
|---|---|---|
| **macOS** | `/Applications/OrcaSlicer.app` (o sistema resolve para `Contents/MacOS/OrcaSlicer` automaticamente) | **Padrão atual do projeto.** Basta instalar o OrcaSlicer pela DMG e deixar em `/Applications/`. |
| **Windows** | `C:\Program Files\OrcaSlicer\orca-slicer.exe` | Instalação padrão. Se instalou em outro disco/pasta, configure `ORCA_SLICER_PATH`. |
| **Linux** | `orca-slicer` (precisa estar no `PATH`) | Instale o OrcaSlicer e garanta que o binário esteja acessível. |

O sistema detecta automaticamente a plataforma:
- **macOS (`sys.platform == 'darwin'`)**: usa `/Applications/OrcaSlicer.app/Contents/MacOS/OrcaSlicer`.
- **Outros**: usa `orca-slicer` (esperado no `PATH`) ou o valor de `ORCA_SLICER_PATH`.

Se o sistema receber um caminho terminando em `.app` (macOS), ele resolve automaticamente para o executável dentro do bundle (`Contents/MacOS/<nome>`).

### Backend e frontend rodando

- Backend (Flask) em execução.
- Frontend acessível no navegador (ex.: `http://localhost:5173` ou o endereço do seu ambiente).
- Usuário **logado** no Croma.

---

## 3. Como usar (passo a passo)

1. **Acesse o Croma** no navegador e faça login.
2. No menu, clique em **Fatiador**.
3. **Selecione o arquivo 3D**
   - Clique em **"Selecionar arquivo"** e escolha um arquivo **.stl** ou **.obj**.
   - O nome do arquivo selecionado aparece no campo ao lado.
4. **Ajuste as opções (opcional)**
   - **Qualidade (altura de camada):** Rápido (0,28 mm), Normal (0,20 mm) ou Fininho (0,12 mm).
   - **Preenchimento (%):** ex.: 15, 20, 25.
5. Clique em **Fatiar**.
6. Aguarde o processamento (pode levar alguns segundos ou minutos, conforme o modelo).
7. Quando aparecer o card **"G-code gerado"**:
   - **Enviar para impressão** — inicia a impressão do G-code gerado (impressora precisa estar conectada).
   - **Ver em Arquivos** — abre a tela Arquivos; o novo G-code estará na lista e poderá ser impresso depois.

---

## 4. Configuração opcional

Se o OrcaSlicer estiver instalado em um caminho não padrão, defina a variável de ambiente **`ORCA_SLICER_PATH`** antes de subir o backend:

- **macOS:**
  `export ORCA_SLICER_PATH=/Applications/OrcaSlicer.app`
  (ou diretamente o binário: `export ORCA_SLICER_PATH=/Applications/OrcaSlicer.app/Contents/MacOS/OrcaSlicer`)
  O sistema aceita ambos os formatos — se receber `.app`, resolve automaticamente para o executável.

- **Windows:**
  `set ORCA_SLICER_PATH=D:\OrcaSlicer\orca-slicer.exe`
  (ou no painel "Variáveis de ambiente" do sistema.)

- **Linux:**
  `export ORCA_SLICER_PATH=/caminho/para/orca-slicer`

Opcionalmente, **`ORCA_DATADIR`** pode apontar para uma pasta com perfis do Orca (printer, processo, filamento em arquivos .json) para usar nas fatiagens.

---

## 5. Como testar e validar a entrega

### 5.1 Teste mínimo (sem impressora)

1. Fazer login no Croma.
2. Ir em **Fatiador**.
3. Selecionar um arquivo **.stl** (ex.: um cubo de teste).
4. Clicar em **Fatiar** e aguardar.
5. **Validar:** aparece o card **"G-code gerado"** com o nome do arquivo.
6. Clicar em **"Ver em Arquivos"**.
7. **Validar:** o G-code gerado aparece na lista em **Arquivos** (com nome, tamanho, etc.).

**Critério:** Upload .stl → G-code gerado e visível em Arquivos = fluxo do fatiador integrado funcionando.

### 5.2 Teste completo (com impressora)

1. Repetir os passos 5.1.1 a 5.1.5.
2. Clicar em **"Enviar para impressão"**.
3. **Validar:** a impressão inicia (estado "Imprimindo" no dashboard).
4. **Validar:** a impressão conclui com sucesso (peça impressa conforme esperado).

**Critério:** Upload .stl → G-code gerado → impressão concluída = entrega completa conforme [tasks.md](tasks.md).

### 5.3 Se aparecer erro

- **"OrcaSlicer não encontrado"**
  Instale o OrcaSlicer ou configure `ORCA_SLICER_PATH` (seção 4).

- **"Arquivo chegou vazio"**
  O arquivo não foi enviado corretamente. Selecione de novo o .stl/.obj e tente novamente; confira se o backend está na porta correta (ex.: proxy do Vite apontando para o Flask).

- **Outros códigos de saída**
  A mensagem de erro pode trazer um trecho da saída do Orca. Verifique se o modelo está válido e se o Orca está instalado corretamente.

---

## 6. Evidência para entrega

Conforme [tasks.md](tasks.md), a evidência do fatiador integrado é:

- **Log + impressão OK:** fluxo em que o .stl é enviado, o G-code é gerado e a impressão é concluída pelo sistema.

Sugestão de registro:

1. **Screenshot** da tela Fatiador com o card "G-code gerado" após fatiar um modelo.
2. **Screenshot** da tela Arquivos mostrando o G-code gerado na lista.
3. **(Opcional)** Foto ou vídeo curto da peça impressa, quando houver impressora.

---

## 7. Regras técnicas do fatiador

### 7.1 Resolução de caminho (`.app` no macOS)

A função `_resolve_orca_path()` em `core/gcode.py` converte automaticamente caminhos `.app` para o executável interno:

- Input: `/Applications/OrcaSlicer.app`
- Output: `/Applications/OrcaSlicer.app/Contents/MacOS/OrcaSlicer`

Isso garante que a variável `ORCA_SLICER_PATH` pode receber tanto o bundle `.app` quanto o executável direto.

### 7.2 Detecção automática por plataforma

Configurado em `core/config.py`:

- `sys.platform == 'darwin'` (macOS): usa `/Applications/OrcaSlicer.app/Contents/MacOS/OrcaSlicer` como padrão.
- Outros: usa `orca-slicer` (esperado no PATH).
- A variável de ambiente `ORCA_SLICER_PATH` sobrescreve qualquer padrão.

### 7.3 Processo de fatiamento

1. Frontend envia arquivo 3D via `POST /api/slicer/slice`.
2. Backend salva o arquivo temporariamente.
3. `run_orca_slice()` chama o OrcaSlicer via `subprocess` com os parâmetros (qualidade, preenchimento).
4. G-code resultante é salvo em `gcode_files/` e inserido no banco de dados.
5. Frontend recebe o ID do arquivo e pode enviar para impressão ou visualizar em Arquivos.

---

## 8. Resumo

| Item | Descrição |
|------|-----------|
| Onde usar | Menu **Fatiador** no Croma |
| Formatos | .stl, .obj |
| Opções | Qualidade (altura de camada), Preenchimento (%) |
| Resultado | G-code na lista de Arquivos; opção de enviar direto para impressão |
| macOS (padrão) | Detecta automaticamente `/Applications/OrcaSlicer.app`; resolve bundle `.app` |
| Windows | Detecta automaticamente `C:\Program Files\OrcaSlicer\`; ou configurar `ORCA_SLICER_PATH` |
| Linux | Precisa do binário no PATH ou `ORCA_SLICER_PATH` configurado |

---

*Documento da Task 5 — Fatiador integrado. Uso, teste e regras técnicas.*
