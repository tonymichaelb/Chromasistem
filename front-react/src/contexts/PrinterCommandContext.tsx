import {
  createContext,
  useContext,
  useState,
  useCallback,
  useRef,
  type ReactNode,
} from "react"

interface PrinterCommandContextValue {
  busy: boolean
  label: string | null
  exec: <T>(label: string, fn: () => Promise<T>) => Promise<T | undefined>
}

const PrinterCommandContext = createContext<PrinterCommandContextValue | null>(
  null,
)

export function PrinterCommandProvider({ children }: { children: ReactNode }) {
  const [label, setLabel] = useState<string | null>(null)
  const busyRef = useRef(false)
  const busy = busyRef.current

  const exec = useCallback(
    async <T,>(cmdLabel: string, fn: () => Promise<T>): Promise<T | undefined> => {
      if (busyRef.current) return undefined
      busyRef.current = true
      setLabel(cmdLabel)
      try {
        return await fn()
      } finally {
        busyRef.current = false
        setLabel(null)
      }
    },
    [],
  )

  return (
    <PrinterCommandContext.Provider value={{ busy, label, exec }}>
      {children}
      {label !== null && <CommandOverlay label={label} />}
    </PrinterCommandContext.Provider>
  )
}

export function usePrinterCommand() {
  const ctx = useContext(PrinterCommandContext)
  if (!ctx) throw new Error("usePrinterCommand must be used within PrinterCommandProvider")
  return ctx
}

function CommandOverlay({ label }: { label: string | null }) {
  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="mx-4 flex w-full max-w-sm flex-col items-center gap-4 rounded-2xl border border-border bg-background p-8 shadow-2xl">
        <div className="relative flex h-12 w-12 items-center justify-center">
          <div className="absolute inset-0 animate-spin rounded-full border-4 border-muted border-t-primary" />
        </div>
        <p className="text-center text-sm font-medium text-foreground">
          {label || "Processando…"}
        </p>
        <p className="text-center text-xs text-muted-foreground">
          Aguarde a impressora responder
        </p>
      </div>
    </div>
  )
}
