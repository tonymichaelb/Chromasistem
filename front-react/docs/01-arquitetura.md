# Visão geral e arquitetura

## Estrutura de pastas

```
src/
├── config.ts              # MOCK = true/false (dados mockados ou API real)
├── main.tsx               # Entrada; aplica setup do mock se MOCK=true
├── App.tsx                # Rotas e AuthProvider
├── index.css              # Estilos globais e tema (Tailwind + variáveis CSS)
├── lib/
│   └── utils.ts           # Utilitários (cn, etc.)
├── contexts/
│   └── AuthContext.tsx    # Estado global: username e setUsername; busca /api/me nas rotas autenticadas
├── components/
│   ├── AppHeader.tsx      # Header compartilhado (nav, tema, logout)
│   └── ui/                # Componentes shadcn (button, card, input, alert-dialog, etc.)
├── mock/
│   ├── setup.ts           # Substitui fetch quando MOCK=true
│   └── api.ts             # Respostas mockadas por endpoint
└── pages/
    ├── login/             # Login.tsx + hook.tsx
    ├── register/
    ├── dashboard/
    ├── files/
    ├── terminal/
    ├── colorir/
    ├── mistura/
    ├── wifi/
    └── placeholders.tsx   # Placeholder genérico (não usado nas rotas atuais)
```

## Rotas (App.tsx)

| Rota       | Componente | Autenticada |
|-----------|------------|-------------|
| `/`       | Redirect → `/login` | — |
| `/login`  | Login      | Não |
| `/register` | Register | Não |
| `/dashboard` | Dashboard | Sim |
| `/files`  | Files      | Sim |
| `/terminal` | Terminal | Sim |
| `/colorir` | Colorir   | Sim |
| `/mistura` | Mistura  | Sim |
| `/wifi`   | Wifi       | Sim |
| `*`       | Redirect → `/login` | — |

Todas as rotas autenticadas estão listadas em `AUTH_ROUTES` em `AuthContext.tsx`. Ao entrar em uma delas, o contexto chama `/api/me` (uma vez por rota) para preencher o `username` no header.

## Autenticação

- **Login/Register:** enviam POST para `/api/login` e `/api/register`; em sucesso, o login redireciona para `/dashboard`.
- **Header:** usa `useAuth()` para exibir o usuário e o botão Sair; ao sair, chama `/api/logout` e redireciona para `/login`.
- **Rotas protegidas:** se alguma chamada retornar 401, o hook correspondente redireciona para `/login` (e, no dashboard, o polling é interrompido após N 401s).

As requisições usam `credentials: "include"` para enviar o cookie de sessão.

## Modo MOCK

- **Arquivo:** `src/config.ts` — constante `MOCK` (true/false).
- **Quando `MOCK = true`:**
  - Em `main.tsx` é chamado `setupMockFetch()` (em `src/mock/setup.ts`).
  - `window.fetch` é substituído: se a URL for `/api/*` e existir mock em `src/mock/api.ts`, a resposta mockada é retornada; caso contrário, a requisição segue para o `fetch` original.
- **Uso:** subir apenas o front (ex.: `npm run build` + servir `dist/` ou deploy em uma URL) para testes de UI/UX sem backend. Para usar a API real, defina `MOCK = false` e garanta que o backend esteja acessível (proxy em dev em `vite.config.ts`).

## Proxy em desenvolvimento

No `vite.config.ts`, `/api` e `/static` são proxy para o backend (ex.: `http://127.0.0.1:80`). Assim, em dev o front roda em `localhost:5173` e as chamadas a `/api/*` são encaminhadas ao Flask.
