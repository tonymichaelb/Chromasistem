# Lógica por tela

Cada tela segue o padrão: **hook** (toda a lógica + estado + chamadas de API) e **componente de view** (apenas UI que consome o hook). A lógica fica no hook; a view não faz fetch nem regras de negócio.

---

## Login (`pages/login/`)

- **Hook:** `useLogin()` — estado: username, password, showPassword, message, loading, version. Busca `/api/version` no mount. `handleSubmit` envia POST `/api/login`; em sucesso redireciona para `/dashboard` após 1s.
- **View:** `Login.tsx` — formulário com inputs, toggle de senha, botão Entrar e link para Registrar. Exibe mensagem de erro/sucesso e versão.

## Register (`pages/register/`)

- **Hook:** `useRegister()` — estado: username, password, confirmPassword, showPassword, showConfirmPassword, message, loading. `handleSubmit` envia POST `/api/register` e trata sucesso/erro.
- **View:** `Register.tsx` — formulário com validação de senhas iguais e link para Login.

## Dashboard (`pages/dashboard/`)

- **Hook:** `useDashboard()` — usa `useAuth()` para username. Estado: status da impressora, recentFiles, notificações, modais (pausa, desconectar, parar, imprimir), connectLoading, etc. Polling de `/api/printer/status` a cada 15s; em 401 consecutivos para o polling e redireciona. Funções: connect, disconnect, startPrint, openPauseModal, confirmPause, resume, openStopConfirm, confirmStop, openPrintConfirm, confirmPrint; fetchRecentFiles e fetchStatus.
- **View:** `Dashboard.tsx` — cards (Status da Impressora, Temperatura, Progresso, Controles, Arquivos recentes) e AlertDialogs para confirmações. Usa `AppHeader`.

## Arquivos (`pages/files/`)

- **Hook:** `useFiles()` — estado: files, loading, searchTerm, uploading, notification, deleteConfirmOpen, fileToDeleteId, printConfirm. Carrega lista com `/api/files/list` no mount. Funções: uploadFile (drag-and-drop e input), openDeleteConfirm, confirmDelete, openPrintConfirm, confirmPrint, downloadFile, copyUploadUrl, loadFiles. Filtro de busca no array em memória.
- **View:** `Files.tsx` — área de upload (drag-and-drop), lista de arquivos (FileCard por item com Imprimir/Baixar/Excluir), card OrcaSlicer e AlertDialogs de excluir/imprimir. Usa `AppHeader`.

## Terminal (`pages/terminal/`)

- **Hook:** `useTerminal()` — estado: nozzle/bed inputs e valores atuais/target, tempHistory (últimas leituras), jogDistance, terminalLines, notification, mixtureModalOpen, editingTintaIndex, modalSliders, etc. Polling: `/api/printer/status` (5s) e `/api/printer/commands-history` (1s). Funções: setNozzleTemp, setBedTemp, setPreset, jogAxis, homeAxis, homeAll, extrudeFilament, preheatExtruder, sendGcode, clearTerminal, quickCommand; sendGcodeCommand centraliza o POST para `/api/printer/gcode` e atualiza terminalLines. syncHistoryCount evita duplicar linhas ao enviar comando.
- **View:** `Terminal.tsx` — cards: Controle de Temperatura, Temperatura em tempo real (tabela), Controle de Movimento (eixos X/Y/Z, extrusora), Terminal G-code (log + input + comandos rápidos). Usa `AppHeader`.

## Colorir (`pages/colorir/`)

- **Hook:** `useColorir()` — estado: currentBrushIndex, brushCustomColors, tintaCustomColors, brushMixtures (Ciano/Magenta/Amarelo por índice), notificações, modais (mistura, ajuda), cor personalizada (hex + CMY). Persiste no localStorage (brushCustomColors, tintaCustomColors, brushMixtures). Carrega `/api/printer/current-brush` e `/api/printer/load-brush-mixtures` no mount. Funções: selectBrush, applyTintaToBrush, openMixtureModal, updateModalSlider (distribuição 100%), saveMixtureModal, updateCustomColorFromHex, applyCustomColorToBrush; sendMixtureForBrush e saveToServer. Conversões RGB/CMY em hexToRgb, rgbToCmyPercent.
- **View:** `Colorir.tsx` — card “Pincel selecionado”, grid de 19 pincéis, grid de 19 tintas (com botão engrenagem para mistura), card Cor personalizada (color picker + aplicar), botão flutuante de ajuda, AlertDialogs (mistura com 3 sliders + cor personalizada, ajuda). Usa `AppHeader`.

## Mistura (`pages/mistura/`)

- **Hook:** `useMistura()` — estado: mix (a, b, c em %), suggestColorHex, notification, sending. Sliders com distribuição para total 100% (distributePercentages). applySuggestColor preenche mix a partir de RGB→CMY. sendMixture envia POST `/api/printer/send-mixture` com comando M182.
- **View:** `Mistura.tsx` — card de informação do comando, card “Sugerir mistura” (color picker), 3 cards de filamento (sliders), card Total, preview do comando, botão Enviar. Usa `AppHeader`.

## Wi-Fi (`pages/wifi/`)

- **Hook:** `useWifi()` — estado: status, savedNetworks, availableNetworks, loadingStatus, loadingSaved, scanning, notificações, modais (conectar, esquecer), connectSSID/connectPassword/showConnectPassword, connectLoading. Polling de `/api/wifi/status` a cada 10s. Funções: loadWifiStatus, loadSavedNetworks, scanNetworks, openConnectModal, closeConnectModal, connectToNetwork, openForgetConfirm, closeForgetConfirm, forgetNetwork. Usa um helper `api()` que faz fetch e trata 401.
- **View:** `Wifi.tsx` — card Status da conexão (gradiente por estado), card Redes salvas (lista + Esquecer), card Redes disponíveis (botão Atualizar + lista com Conectar), AlertDialogs (conectar com senha, esquecer rede). Usa `AppHeader`.

---

Em todas as telas autenticadas, o header é o `AppHeader`, que usa `useAuth()` e exibe o nome do usuário e o botão Sair.
