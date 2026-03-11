import { useState, useEffect, useCallback } from "react"
import { useLocation } from "react-router-dom"

const FLOW_ROUTES = ["/dashboard", "/files", "/terminal", "/colorir", "/mistura"]
const POLL_MS = 5000
const RETRIES_ON_ERROR = 3
const RETRY_DELAY_MS = 1000

export function usePrinterStatus() {
  const location = useLocation()
  const [connected, setConnected] = useState<boolean>(false)
  const [state, setState] = useState<"idle" | "printing" | "paused" | "failure" | null>(null)

  const fetchStatus = useCallback(async (): Promise<boolean> => {
    if (!FLOW_ROUTES.includes(location.pathname)) return true
    try {
      const res = await fetch("/api/printer/status", { credentials: "include" })
      if (res.status === 401) return true
      const data = await res.json()
      if (data.success && data.status) {
        setConnected(!!data.status.connected)
        setState(data.status.state ?? null)
        return true
      }
      setConnected(false)
      setState(null)
      return false
    } catch {
      setConnected(false)
      setState(null)
      return false
    }
  }, [location.pathname])

  useEffect(() => {
    if (!FLOW_ROUTES.includes(location.pathname)) return
    let cancelled = false
    let timeoutId: ReturnType<typeof setTimeout>
    const scheduleNext = () => {
      if (cancelled) return
      timeoutId = setTimeout(() => {
        runWithRetries()
      }, POLL_MS)
    }
    const runWithRetries = async () => {
      if (cancelled) return
      let attempt = 0
      while (attempt <= RETRIES_ON_ERROR) {
        const ok = await fetchStatus()
        if (cancelled) return
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
  }, [fetchStatus, location.pathname])

  return { connected, state }
}
