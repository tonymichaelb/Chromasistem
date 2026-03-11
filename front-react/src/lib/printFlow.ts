export const PRINT_FLOW_STEPS = [
  { step: 1, label: "Conectar na impressora (Monitor)", path: "/dashboard" },
  { step: 2, label: "Arquivos", path: "/files" },
  { step: 3, label: "Terminal", path: "/terminal" },
  { step: 4, label: "Cores (Color/Mistura)", path: "/colorir" },
  { step: 5, label: "Revisão", path: "/revisao" },
  { step: 6, label: "Imprimir", path: "/dashboard" },
] as const

export function getCurrentStep(
  pathname: string,
  connected: boolean,
  state: string | null
): number {
  console.log('connected', connected)
  if (pathname === "/files") return 2
  if (pathname === "/terminal") return 3
  if (pathname === "/colorir" || pathname === "/mistura") return 4
  if (pathname === "/revisao") return 5
  if (pathname === "/dashboard") {
    if (state === "printing" || state === "paused" || state === "failure") return 6
    // Na tela do Monitor sempre mostramos passo 1 ativo (azul); conectado ou não.
    return 1
  }
  return 1
}
