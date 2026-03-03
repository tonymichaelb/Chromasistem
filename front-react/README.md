# Croma — Frontend React

Frontend do **Croma** (Sistema de Monitoramento de Impressora 3D), reescrito em **Vite + React + TypeScript**, com **Tailwind CSS** e **shadcn/ui**.

## Stack


- **Vite** — build e dev server
- **React 19** + **TypeScript**
- **Tailwind CSS 4** + **shadcn/ui** (componentes)
- **React Router** — rotas SPA

## Desenvolvimento

```bash
npm install
npm run dev
```

Acesse `http://localhost:5173`. Em desenvolvimento, as chamadas para `/api/*` e `/static/*` são proxy para o backend (configurar em `vite.config.ts`; padrão `http://127.0.0.1:80`).

**Requisito (API real):** o backend Flask do Croma deve estar rodando para login, registro e demais APIs. Se quiser testar só o front, use o **modo MOCK** (veja abaixo).

## Modo MOCK (testar sem backend)

Para subir o front em uma URL e testar UI/UX sem o backend:

1. Abra **`src/config.ts`** e defina **`MOCK = true`**.
2. Todas as requisições para `/api/*` passam a receber respostas mockadas (definidas em `src/mock/api.ts`).
3. Faça o build e sirva a pasta `dist/` ou faça deploy; o app funciona sem o Flask.
4. Para voltar a usar a API real, defina **`MOCK = false`** em `src/config.ts`.

## Build

```bash
npm run build
```

Saída em `dist/`. O backend pode servir o `index.html` e os arquivos estáticos dessa pasta para usar o frontend em produção.

## Estrutura do projeto

- **`src/pages/`** — uma pasta por tela. Em cada pasta:
  - **`hook.tsx`** — toda a lógica da página (estado, handlers, chamadas de API). Exporta um hook (ex.: `useLogin`, `useDashboard`) que retorna variáveis e funções para a view.
  - **`NomeDaPagina.tsx`** — apenas a view: importa o hook, consome o retorno e renderiza com componentes shadcn. Sem lógica de negócio aqui.
- **`src/components/ui/`** — componentes shadcn (Button, Card, Input, AlertDialog, etc.)
- **`src/components/AppHeader.tsx`** — header compartilhado (nav, tema, logout)
- **`src/contexts/AuthContext.tsx`** — estado global de autenticação (username); chama `/api/me` nas rotas autenticadas
- **`src/config.ts`** — constante `MOCK` (true/false)
- **`src/mock/`** — quando MOCK=true, substitui respostas de `/api/*` por dados mockados
- **`src/lib/utils.ts`** — utilitários (ex.: `cn`)

## Documentação para desenvolvedores

Na pasta **`docs/`** há guias para quem for mexer no projeto:

- **[docs/README.md](docs/README.md)** — índice da documentação
- **[docs/01-arquitetura.md](docs/01-arquitetura.md)** — visão geral, rotas, auth, modo MOCK, proxy
- **[docs/02-api-calls.md](docs/02-api-calls.md)** — onde cada endpoint é chamado (por tela/hook)
- **[docs/03-screens-logic.md](docs/03-screens-logic.md)** — lógica de cada tela (hook + view)
- **[docs/04-ui-components.md](docs/04-ui-components.md)** — como usar shadcn, adicionar novas páginas, responsivo e tema

## Referência

As telas e fluxos seguem o frontend legado em **`../static`** e nos **templates** do backend (login, register, dashboard, arquivos, terminal, colorir, mistura, wifi). A migração foi feita tela a tela, mantendo as mesmas APIs e fluxos, com nova UI em React + shadcn.

## Assets

- Logo: coloque `logo-branca.png` em **`public/images/`** (ou copie de `../static/images/`). A tela de login/registro e o header usam `/images/logo-branca.png`.
