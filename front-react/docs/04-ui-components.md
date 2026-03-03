# UI e componentes

## Uso do shadcn/ui

- Os componentes de UI ficam em **`src/components/ui/`** (Button, Card, Input, AlertDialog, etc.). Não crie componentes visuais “na mão” para coisas que o shadcn já cobre; use e customize via `className` e variantes.
- Estilo é feito com **Tailwind CSS** e variáveis de tema em **`src/index.css`** (`:root` e `.dark`). Cores semânticas: `background`, `foreground`, `primary`, `secondary`, `muted`, `destructive`, `border`, etc.
- Ícones: **@hugeicons/react** + **@hugeicons/core-free-icons**. Exemplo: `import { HugeiconsIcon } from "@hugeicons/react"; import { RefreshIcon } from "@hugeicons/core-free-icons";` e usar `<HugeiconsIcon icon={RefreshIcon} className="size-4" />`.

## Como adicionar uma nova página

1. **Criar a pasta** em `src/pages/`: por exemplo `src/pages/minha-tela/`.
2. **Criar o hook** `hook.tsx` com toda a lógica:
   - Estado (useState), efeitos (useEffect), callbacks (useCallback).
   - Chamadas de API (fetch com `credentials: "include"` e tratamento de 401 se for rota autenticada).
   - Retornar um objeto com tudo que a view precisar (estado + funções).
3. **Criar a view** `MinhaTela.tsx`:
   - Importar o hook da mesma pasta: `import { useMinhaTela } from "./hook"`.
   - Usar apenas o que o hook retorna; não fazer fetch nem lógica de negócio aqui.
   - Usar componentes de `@/components/ui` e, se for tela autenticada, `<AppHeader />` no topo.
4. **Registrar a rota** em `App.tsx`: `<Route path="/minha-tela" element={<MinhaTela />} />`.
5. **Se for rota autenticada**, adicionar o path em `AUTH_ROUTES` em `src/contexts/AuthContext.tsx`.
6. **Adicionar o link no header** em `src/components/AppHeader.tsx`: incluir `{ to: "/minha-tela", label: "Minha Tela", icon: AlgumIcon }` no array `navLinks`.
7. **Se estiver usando MOCK**, adicionar as respostas mockadas em `src/mock/api.ts` para os endpoints que a nova tela usar.

## Estrutura da view

- Páginas autenticadas: layout comum com `min-h-screen bg-muted/30`, `<AppHeader />` e `<main className="container mx-auto max-w-... space-y-6 px-3 py-4 ...">`.
- Use **Card** para blocos (CardHeader, CardTitle, CardDescription, CardContent).
- Use **Button** com variantes `default`, `secondary`, `destructive`, `outline`, `ghost` e tamanhos `sm`, `default`, `lg` conforme o design.
- Confirmações e avisos: **AlertDialog** (AlertDialogContent, AlertDialogHeader, AlertDialogTitle, AlertDialogDescription, AlertDialogFooter, AlertDialogCancel, AlertDialogAction). Não use `window.confirm` nem `window.alert`.
- Formulários: **Field**, **FieldLabel**, **FieldDescription**, **Input**; para agrupar input + botão (ex.: senha com “mostrar”), use **InputGroup** quando existir.

## Responsivo e acessibilidade

- Use breakpoints Tailwind: `sm:`, `md:`, `lg:` para esconder/mostrar ou mudar layout (ex.: header com menu hamburger em `md:hidden` e nav em `hidden md:flex`).
- Evite overflow horizontal: `min-w-0` em flex/grid quando o conteúdo pode ser longo; `overflow-x-hidden` já está no body em `index.css`.
- Botões importantes: `min-h-10` e `touch-manipulation` para toque em mobile.
- Sempre que fizer sentido: `aria-label` em botões de ícone, `role="alert"` em mensagens de erro/sucesso.

## Tema (claro/escuro)

- O header tem um botão que alterna entre claro e escuro; o tema é salvo em `localStorage` (`croma-theme`) e aplicado na classe `dark` em `document.documentElement`. Os componentes usam as variáveis CSS do tema (`background`, `foreground`, etc.), então não é preciso estilizar manualmente para dark.
