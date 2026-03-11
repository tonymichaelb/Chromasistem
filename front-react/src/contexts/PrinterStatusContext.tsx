/**
 * Fonte única de polling para /api/printer/status.
 * Evita múltiplos loops (usePrinterStatus + dashboard + terminal) encavalando requisições.
 */

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  useRef,
  type ReactNode,
} from "react"
import { useLocation, useNavigate } from "react-router-dom"

const FLOW_ROUTES = ["/dashboard", "/files", "/terminal", "/colorir", "/mistura"]
const POLL_MS = 4000
const RETRIES_ON_ERROR = 3
const RETRY_DELAY_MS = 1000
const MAX_UNAUTHORIZED_RETRIES = 2

export interface PrinterStatus {
  connected: boolean
  state: "idle" | "printing" | "paused" | "failure"
  temperature: {
    nozzle: number
    bed: number
    target_nozzle: number
    target_bed: number
  }
  filename: string
  progress: number
  time_elapsed: string
  time_remaining: string
  filament?: {
    sensor_enabled: boolean
    has_filament?: boolean
  }
  failure_detected?: boolean
  failure_message?: string | null
  failure_code?: string | null
  skipped_objects_count?: number
}

interface PrinterStatusContextValue {
  status: PrinterStatus | null
  connected: boolean
  state: "idle" | "printing" | "paused" | "failure" | null
  refetch: () => Promise<void>
}

const PrinterStatusContext = createContext<PrinterStatusContextValue | null>(null)

const fetchOptions = { credentials: "include" as RequestCredentials }

export function PrinterStatusProvider({ children }: { children: ReactNode }) {
  const location = useLocation()
  const navigate = useNavigate()
  const [status, setStatus] = useState<PrinterStatus | null>(null)
  const unauthorizedCountRef = useRef(0)
  const pollStoppedRef = useRef(false)

  const fetchOnce = useCallback(async (): Promise<boolean> => {
    if (pollStoppedRef.current) return true
    try {
      const res = await fetch("/api/printer/status", fetchOptions)
      if (res.status === 401) {
        unauthorizedCountRef.current += 1
        if (unauthorizedCountRef.current >= MAX_UNAUTHORIZED_RETRIES) {
          pollStoppedRef.current = true
          navigate("/login")
        }
        return true
      }
      unauthorizedCountRef.current = 0
      const data = await res.json()
      if (data.success && data.status) {
        setStatus(data.status)
        return true
      }
      setStatus(null)
      return false
    } catch {
      setStatus(null)
      return false
    }
  }, [navigate])

  const refetch = useCallback(async () => {
    await fetchOnce()
  }, [fetchOnce])

  useEffect(() => {
    if (!FLOW_ROUTES.includes(location.pathname)) return
    let cancelled = false
    let timeoutId: ReturnType<typeof setTimeout>
    const scheduleNext = () => {
      if (cancelled || pollStoppedRef.current) return
      timeoutId = setTimeout(() => {
        runWithRetries()
      }, POLL_MS)
    }
    const runWithRetries = async () => {
      if (cancelled || pollStoppedRef.current) return
      let attempt = 0
      while (attempt <= RETRIES_ON_ERROR) {
        const ok = await fetchOnce()
        if (cancelled || pollStoppedRef.current) return
        if (ok) break
        attempt++
        if (attempt <= RETRIES_ON_ERROR) {
          await new Promise((r) => setTimeout(r, RETRY_DELAY_MS))
        }
      }
      scheduleNext()
    }
    runWithRetries()
    return () => {
      cancelled = true
      clearTimeout(timeoutId)
    }
  }, [location.pathname, fetchOnce])

  const value: PrinterStatusContextValue = {
    status,
    connected: !!status?.connected,
    state: status?.state ?? null,
    refetch,
  }

  return (
    <PrinterStatusContext.Provider value={value}>
      {children}
    </PrinterStatusContext.Provider>
  )
}

export function usePrinterStatusContext() {
  const ctx = useContext(PrinterStatusContext)
  if (!ctx) throw new Error("usePrinterStatusContext must be used within PrinterStatusProvider")
  return ctx
}
