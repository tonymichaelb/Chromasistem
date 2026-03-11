import { useState, useEffect, useCallback, useRef } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "@/contexts/AuthContext"
import { usePrinterCommand } from "@/contexts/PrinterCommandContext"

const STATUS_POLL_MS = 3000
const MAX_UNAUTHORIZED_RETRIES = 2
const STATUS_RETRIES_ON_ERROR = 3
const STATUS_RETRY_DELAY_MS = 1000

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
  /** Detecção de falhas (Task 4) */
  failure_detected?: boolean
  failure_message?: string | null
  failure_code?: string | null
  skipped_objects_count?: number
}

export type PauseOption = "keep_temp" | "cold" | "filament_change"

export interface BedObject {
  id: number
  name?: string | null
  min_x: number | null
  min_y: number | null
  max_x: number | null
  max_y: number | null
}

export interface BedPreview {
  bed: { width_mm: number; depth_mm: number }
  objects: BedObject[]
}

export interface FailureHistoryEntry {
  id: number
  print_job_id: number
  occurred_at: string
  failure_code: string | null
  failure_message: string | null
  action: string
  object_index_or_name: string | null
}

export function useDashboard() {
  const navigate = useNavigate()
  const { username } = useAuth()
  const { exec } = usePrinterCommand()
  const [status, setStatus] = useState<PrinterStatus | null>(null)
  const [notification, setNotification] = useState<{ message: string; type: "success" | "error" | "info" } | null>(null)
  const [pauseModalOpen, setPauseModalOpen] = useState(false)
  const [pauseOption, setPauseOption] = useState<PauseOption>("keep_temp")
  const [connectLoading, setConnectLoading] = useState(false)
  const [disconnectConfirmOpen, setDisconnectConfirmOpen] = useState(false)
  const [stopConfirmOpen, setStopConfirmOpen] = useState(false)
  const [failureHistoryOpen, setFailureHistoryOpen] = useState(false)
  const [failureHistoryEntries, setFailureHistoryEntries] = useState<FailureHistoryEntry[]>([])
  const [bedPreviewOpen, setBedPreviewOpen] = useState(false)
  const [bedPreviewData, setBedPreviewData] = useState<BedPreview | null>(null)
  const [selectedObjectId, setSelectedObjectId] = useState<number | null>(null)
  const unauthorizedCountRef = useRef(0)
  const pollStoppedRef = useRef(false)

  const fetchOptions = { credentials: "include" as RequestCredentials }

  const showNotification = useCallback((message: string, type: "success" | "error" | "info" = "info") => {
    setNotification({ message, type })
    setTimeout(() => setNotification(null), 3000)
  }, [])

  const fetchStatus = useCallback(async (): Promise<boolean> => {
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

  useEffect(() => {
    let cancelled = false
    let timeoutId: ReturnType<typeof setTimeout>
    const scheduleNext = () => {
      if (cancelled) return
      timeoutId = setTimeout(() => {
        runWithRetries()
      }, STATUS_POLL_MS)
    }
    const runWithRetries = async () => {
      if (cancelled) return
      let attempt = 0
      while (attempt <= STATUS_RETRIES_ON_ERROR) {
        const ok = await fetchStatus()
        if (cancelled) return
        if (ok) break
        attempt++
        if (attempt <= STATUS_RETRIES_ON_ERROR) {
          await new Promise((r) => setTimeout(r, STATUS_RETRY_DELAY_MS))
        }
      }
      scheduleNext()
    }
    runWithRetries()
    return () => {
      cancelled = true
      clearTimeout(timeoutId)
    }
  }, [fetchStatus])

  const connect = async () => {
    await exec("Conectando à impressora…", async () => {
      setConnectLoading(true)
      try {
        const res = await fetch("/api/printer/connect", { method: "POST", ...fetchOptions })
        const data = await res.json()
        showNotification(data.message || "Conectado", data.success ? "success" : "error")
        if (data.success) fetchStatus()
      } catch {
        showNotification("Erro ao conectar impressora", "error")
      } finally {
        setConnectLoading(false)
      }
    })
  }

  const openDisconnectConfirm = () => setDisconnectConfirmOpen(true)
  const confirmDisconnect = async () => {
    setDisconnectConfirmOpen(false)
    await exec("Desconectando impressora…", async () => {
      try {
        const res = await fetch("/api/printer/disconnect", { method: "POST", ...fetchOptions })
        const data = await res.json()
        showNotification(data.message || "Desconectado", data.success ? "success" : "error")
        if (data.success) fetchStatus()
      } catch {
        showNotification("Erro ao desconectar impressora", "error")
      }
    })
  }

  const startPrint = async () => {
    try {
      const res = await fetch("/api/printer/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: "modelo.gcode" }),
        ...fetchOptions,
      })
      const data = await res.json()
      showNotification(data.message || "Iniciado", data.success ? "success" : "error")
      if (data.success) fetchStatus()
    } catch {
      showNotification("Erro ao iniciar impressão", "error")
    }
  }

  const openPauseModal = () => setPauseModalOpen(true)
  const closePauseModal = () => setPauseModalOpen(false)

  const confirmPause = async () => {
    closePauseModal()
    await exec("Pausando impressão…", async () => {
      try {
        const res = await fetch("/api/printer/pause", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ option: pauseOption }),
          ...fetchOptions,
        })
        const data = await res.json()
        showNotification(data.message || "Pausado", data.success ? "success" : "error")
        if (data.success) fetchStatus()
      } catch {
        showNotification("Erro ao pausar impressão", "error")
      }
    })
  }

  const resume = async () => {
    await exec("Retomando impressão…", async () => {
      try {
        const res = await fetch("/api/printer/resume", { method: "POST", ...fetchOptions })
        const data = await res.json()
        showNotification(data.message || "Retomado", data.success ? "success" : "error")
        if (data.success) fetchStatus()
      } catch {
        showNotification("Erro ao retomar impressão", "error")
      }
    })
  }

  const openStopConfirm = () => setStopConfirmOpen(true)
  const confirmStop = async () => {
    setStopConfirmOpen(false)
    await exec("Parando impressão…", async () => {
      try {
        const res = await fetch("/api/printer/stop", { method: "POST", ...fetchOptions })
        const data = await res.json()
        showNotification(data.message || "Parado", data.success ? "success" : "error")
        if (data.success) fetchStatus()
      } catch {
        showNotification("Erro ao parar impressão", "error")
      }
    })
  }

  const logout = async () => {
    try {
      await fetch("/api/logout", { method: "POST", ...fetchOptions })
      navigate("/login")
    } catch {
      navigate("/login")
    }
  }

  const canPause = status?.state === "printing"
  const canResume = status?.state === "paused"
  const canStop = status?.state === "printing" || status?.state === "paused" || status?.state === "failure"
  const isFailure = status?.state === "failure"

  const stateLabel =
    status?.state === "printing"
      ? "Imprimindo"
      : status?.state === "paused"
        ? "Pausado"
        : status?.state === "failure"
          ? "Falha detectada"
          : status?.state === "idle"
            ? "Ocioso"
            : "Parado"

  const failureResolve = async () => {
    await exec("Registrando resolução…", async () => {
      try {
        const res = await fetch("/api/printer/failure/resolve", { method: "POST", ...fetchOptions })
        const data = await res.json()
        showNotification(data.message || "Aguardando problema resolvido", data.success ? "success" : "error")
      } catch {
        showNotification("Erro ao registrar ação", "error")
      }
    })
  }

  const failureResolved = async () => {
    await exec("Retomando após resolução…", async () => {
      try {
        const res = await fetch("/api/printer/failure/resolved", { method: "POST", ...fetchOptions })
        const data = await res.json()
        showNotification(data.message || "Retomando impressão", data.success ? "success" : "error")
        if (data.success) fetchStatus()
      } catch {
        showNotification("Erro ao retomar impressão", "error")
      }
    })
  }

  const skipObject = async (objectId?: number) => {
    await exec("Pulando objeto…", async () => {
      try {
        const res = await fetch("/api/printer/skip-object", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(objectId != null ? { object_id: objectId } : {}),
          ...fetchOptions,
        })
        const data = await res.json()
        showNotification(data.message || "Pulando item", data.success ? "success" : "error")
        if (data.success) {
          fetchStatus()
          setBedPreviewOpen(false)
          setSelectedObjectId(null)
        }
      } catch {
        showNotification("Erro ao pular item", "error")
      }
    })
  }

  const fetchFailureHistory = useCallback(async () => {
    try {
      const res = await fetch("/api/printer/failure-history?limit=30", fetchOptions)
      if (res.status === 401) return
      const data = await res.json()
      if (data.success && Array.isArray(data.entries)) setFailureHistoryEntries(data.entries)
    } catch {
      setFailureHistoryEntries([])
    }
  }, [])

  const openFailureHistory = useCallback(() => {
    setFailureHistoryOpen(true)
    fetchFailureHistory()
  }, [fetchFailureHistory])

  const fetchBedPreview = useCallback(async () => {
    try {
      const res = await fetch("/api/printer/bed-preview", fetchOptions)
      if (res.status === 401) return null
      const data = await res.json()
      if (data.success && data.bed && Array.isArray(data.objects)) {
        setBedPreviewData({ bed: data.bed, objects: data.objects })
        return data.objects.length
      }
      setBedPreviewData(null)
      return 0
    } catch {
      setBedPreviewData(null)
      return 0
    }
  }, [])

  const openBedPreviewForSkip = useCallback(async () => {
    const count = await fetchBedPreview()
    setSelectedObjectId(null)
    setBedPreviewOpen(true)
    return count
  }, [fetchBedPreview])

  return {
    username,
    status,
    stateLabel,
    notification,
    pauseModalOpen,
    setPauseModalOpen,
    pauseOption,
    setPauseOption,
    connectLoading,
    canPause,
    canResume,
    canStop,
    disconnectConfirmOpen,
    setDisconnectConfirmOpen,
    stopConfirmOpen,
    setStopConfirmOpen,
    connect,
    openDisconnectConfirm,
    confirmDisconnect,
    startPrint,
    openPauseModal,
    closePauseModal,
    confirmPause,
    resume,
    openStopConfirm,
    confirmStop,
    logout,
    isFailure,
    failureResolve,
    failureResolved,
    skipObject,
    failureHistoryOpen,
    setFailureHistoryOpen,
    failureHistoryEntries,
    openFailureHistory,
    bedPreviewOpen,
    setBedPreviewOpen,
    bedPreviewData,
    selectedObjectId,
    setSelectedObjectId,
    openBedPreviewForSkip,
  }
}
