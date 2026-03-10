import { useState, useEffect, useCallback } from "react"
import { useLocation } from "react-router-dom"

const FLOW_ROUTES = ["/dashboard", "/files", "/terminal", "/colorir", "/mistura"]
const POLL_MS = 5000

export function usePrinterStatus() {
  const location = useLocation()
  const [connected, setConnected] = useState<boolean>(false)
  const [state, setState] = useState<"idle" | "printing" | "paused" | "failure" | null>(null)

  const fetchStatus = useCallback(async () => {
    if (!FLOW_ROUTES.includes(location.pathname)) return
    try {
      const res = await fetch("/api/printer/status", { credentials: "include" })
      if (res.status === 401) return
      const data = await res.json()
      if (data.success && data.status) {
        setConnected(!!data.status.connected)
        setState(data.status.state ?? null)
      } else {
        setConnected(false)
        setState(null)
      }
    } catch {
      setConnected(false)
      setState(null)
    }
  }, [location.pathname])

  useEffect(() => {
    fetchStatus()
    if (!FLOW_ROUTES.includes(location.pathname)) return
    const interval = setInterval(fetchStatus, POLL_MS)
    return () => clearInterval(interval)
  }, [fetchStatus, location.pathname])

  return { connected, state }
}
