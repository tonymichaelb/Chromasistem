# Chamadas de API

Referência de **onde** cada endpoint é chamado e **como** (método, body, uso da resposta). Os mocks em `src/mock/api.ts` replicam essas respostas quando `MOCK = true`.

## Autenticação e usuário

| Endpoint       | Método | Onde é chamado | Body / Resposta |
|----------------|--------|----------------|-----------------|
| `/api/version` | GET    | `pages/login/hook.tsx` (useEffect) | Resposta: `{ version?: string }`. Exibido no rodapé do login. |
| `/api/login`   | POST   | `pages/login/hook.tsx` (handleSubmit) | Body: `{ username, password }`. Resposta: `{ success, message? }`. Em sucesso, redireciona para `/dashboard`. |
| `/api/register`| POST   | `pages/register/hook.tsx` | Body: `{ username, password }`. Resposta: `{ success, message? }`. |
| `/api/me`      | GET    | `contexts/AuthContext.tsx` (useEffect em rotas autenticadas) | Resposta: `{ success, username? }`. Preenche o nome no header. |
| `/api/logout`  | POST   | `components/AppHeader.tsx` (onLogout) e `pages/dashboard/hook.tsx` (confirmDisconnect) | Sem body. Após sucesso, redireciona para `/login`. |

## Impressora (status e controle)

| Endpoint | Método | Onde é chamado | Observação |
|----------|--------|----------------|------------|
| `/api/printer/status` | GET | `pages/dashboard/hook.tsx` (fetchStatus, polling 15s), `pages/terminal/hook.tsx` (fetchStatus, polling 5s) | Resposta: `{ success, status }` com connected, state, temperature, filename, progress, time_elapsed, time_remaining, filament. |
| `/api/printer/connect` | POST | `pages/dashboard/hook.tsx` (connect) | Resposta: `{ success }`. |
| `/api/printer/disconnect` | POST | `pages/dashboard/hook.tsx` (confirmDisconnect) | Resposta: `{ success }`. |
| `/api/printer/start` | POST | `pages/dashboard/hook.tsx` (startPrint) | Body: `{ file_id? }`. Resposta: `{ success }`. |
| `/api/printer/pause` | POST | `pages/dashboard/hook.tsx` (confirmPause) | Body: `{ option: "keep_temp" \| "cold" \| "filament_change" }`. Resposta: `{ success }`. |
| `/api/printer/resume` | POST | `pages/dashboard/hook.tsx` (resume) | Resposta: `{ success }`. |
| `/api/printer/stop` | POST | `pages/dashboard/hook.tsx` (confirmStop) | Resposta: `{ success }`. |

## Arquivos G-Code

| Endpoint | Método | Onde é chamado | Observação |
|----------|--------|----------------|------------|
| `/api/files/list` | GET | `pages/dashboard/hook.tsx` (fetchRecentFiles), `pages/files/hook.tsx` (loadFiles) | Resposta: `{ success, files[] }`. Dashboard usa só os 5 primeiros. |
| `/api/files/upload` | POST | `pages/files/hook.tsx` (uploadFile) | Body: FormData com campo `file`. Resposta: `{ success, message? }`. |
| `/api/files/delete/:id` | DELETE | `pages/files/hook.tsx` (confirmDelete) | Resposta: `{ success, message? }`. |
| `/api/files/print/:id` | POST | `pages/dashboard/hook.tsx` (confirmPrint), `pages/files/hook.tsx` (confirmPrint) | Resposta: `{ success, message? }`. |
| `/api/files/download/:id` | GET | `pages/files/hook.tsx` (downloadFile) — `window.open(...)` | Não é fetch; em mock o link pode abrir em branco. |

## Terminal G-Code

| Endpoint | Método | Onde é chamado | Observação |
|----------|--------|----------------|------------|
| `/api/printer/gcode` | POST | `pages/terminal/hook.tsx` (sendGcodeCommand) | Body: `{ command: string }`. Resposta: `{ success, response? }`. |
| `/api/printer/commands-history` | GET | `pages/terminal/hook.tsx` (fetchCommandsHistory, polling 1s) | Resposta: `{ success, history[], count }`. history: `{ timestamp, command, type }`. |

## Colorir (pincéis e mistura)

| Endpoint | Método | Onde é chamado | Observação |
|----------|--------|----------------|------------|
| `/api/printer/current-brush` | GET | `pages/colorir/hook.tsx` (loadCurrentBrush) | Resposta: `{ success, brush?: number }`. |
| `/api/printer/load-brush-mixtures` | GET | `pages/colorir/hook.tsx` (loadBrushMixtures) | Resposta: `{ success, mixtures?, colors?, tintaColors? }`. |
| `/api/printer/select-brush` | POST | `pages/colorir/hook.tsx` (selectBrush) | Body: `{ brush: number }`. Resposta: `{ success }`. |
| `/api/printer/send-mixture` | POST | `pages/colorir/hook.tsx` (sendMixtureForBrush), `pages/mistura/hook.tsx` (sendMixture) | Body: `{ command: "M182 A... B... C..." }`. Resposta: `{ success }`. |
| `/api/printer/save-brush-mixtures` | POST | `pages/colorir/hook.tsx` (saveToServer, após aplicar tinta/mistura/cor personalizada) | Body: `{ mixtures, colors, tintaColors }` (chaves string). Resposta: `{ success }`. |

## Mistura

- Único endpoint usado na tela Mistura: **POST `/api/printer/send-mixture`** (mesmo do Colorir), em `pages/mistura/hook.tsx` (sendMixture).

## Wi-Fi

| Endpoint | Método | Onde é chamado | Observação |
|----------|--------|----------------|------------|
| `/api/wifi/status` | GET | `pages/wifi/hook.tsx` (loadWifiStatus, polling 10s) | Resposta: `{ success, status: { connected, ssid?, ip?, is_hotspot? } }`. |
| `/api/wifi/saved` | GET | `pages/wifi/hook.tsx` (loadSavedNetworks) | Resposta: `{ success, networks: string[] }`. |
| `/api/wifi/scan` | GET | `pages/wifi/hook.tsx` (scanNetworks) | Resposta: `{ success, networks: { ssid, signal, security }[] }`. |
| `/api/wifi/connect` | POST | `pages/wifi/hook.tsx` (connectToNetwork) | Body: `{ ssid, password }`. Resposta: `{ success, message? }`. |
| `/api/wifi/forget` | POST | `pages/wifi/hook.tsx` (forgetNetwork) | Body: `{ ssid }`. Resposta: `{ success, message? }`. |

---

Todas as chamadas que precisam de sessão usam `credentials: "include"`. Em 401, os hooks de páginas autenticadas redirecionam para `/login`.
