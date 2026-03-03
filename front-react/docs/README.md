# Documentação — Croma Frontend React

Documentação para desenvolvedores que vão manter ou estender o frontend do Croma.

## Índice

1. **[Visão geral e arquitetura](./01-arquitetura.md)** — Como o projeto está organizado, rotas, auth e fluxo geral.
2. **[Chamadas de API](./02-api-calls.md)** — Onde cada endpoint é chamado (por tela/hook) e formato das requisições/respostas.
3. **[Lógica por tela](./03-screens-logic.md)** — O que cada página faz, onde está a lógica (hook) e principais estados.
4. **[UI e componentes](./04-ui-components.md)** — Como usar shadcn/ui, adicionar novas páginas e boas práticas de estilo.

## Stack

- **Vite** + **React 19** + **TypeScript**
- **Tailwind CSS 4** + **shadcn/ui**
- **React Router** (SPA)

## Modo MOCK

Para testar o front sem o backend (ex.: deploy em uma URL para UI/UX), use o modo mock:

- Em **`src/config.ts`** defina `MOCK = true`.
- Todas as requisições para `/api/*` passam a receber respostas mockadas (definidas em `src/mock/api.ts`).
- Com `MOCK = false`, as chamadas vão para o backend real (via proxy em dev ou mesma origem em produção).

Veja mais em [01-arquitetura.md](./01-arquitetura.md#modo-mock).
