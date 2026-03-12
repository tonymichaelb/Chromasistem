import { useState, useCallback, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "@/contexts/AuthContext"
import { usePrinterCommand } from "@/contexts/PrinterCommandContext"
import { usePrinterStatusContext, type PrinterStatus } from "@/contexts/PrinterStatusContext"

export type { PrinterStatus }

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
  /** Índice 0-based do objeto sendo impresso no momento (null se não houver) */
  current_object_index: number | null
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
  const { status, refetch } = usePrinterStatusContext()
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

  const fetchOptions = { credentials: "include" as RequestCredentials }

  const showNotification = useCallback((message: string, type: "success" | "error" | "info" = "info") => {
    setNotification({ message, type })
    setTimeout(() => setNotification(null), 3000)
  }, [])

  const connect = async () => {
    await exec("Conectando à impressora…", async () => {
      setConnectLoading(true)
      try {
        const res = await fetch("/api/printer/connect", { method: "POST", ...fetchOptions })
        const data = await res.json()
        showNotification(data.message || "Conectado", data.success ? "success" : "error")
        if (data.success) refetch()
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
        if (data.success) refetch()
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
      if (data.success) refetch()
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
        if (data.success) refetch()
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
        if (data.success) refetch()
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
        if (data.success) refetch()
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
        if (data.success) refetch()
      } catch {
        showNotification("Erro ao retomar impressão", "error")
      }
    })
  }

  const skipObject = async (objectId?: number, numObjects?: number) => {
    await exec("Pulando objeto…", async () => {
      try {
        const body: { object_id?: number; num_objects?: number } = {}
        if (objectId != null) body.object_id = objectId
        if (numObjects != null && numObjects > 0) body.num_objects = numObjects
        const res = await fetch("/api/printer/skip-object", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
          ...fetchOptions,
        })
        const data = await res.json()
        showNotification(data.message || "Pulando item", data.success ? "success" : "error")
        if (data.success) {
          refetch()
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
        setBedPreviewData({
          bed: data.bed,
          objects: data.objects,
          current_object_index: typeof data.current_object_index === "number" && data.current_object_index >= 0 ? data.current_object_index : null,
        })
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

  const [reportFailureLoading, setReportFailureLoading] = useState(false)

  useEffect(() => {
    if (reportFailureLoading && status?.state === "failure") setReportFailureLoading(false)
  }, [reportFailureLoading, status?.state])

  const reportManualFailure = useCallback(async () => {
    setReportFailureLoading(true)
    try {
      const res = await fetch("/api/printer/failure", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: "Peça com defeito", code: "ERR" }),
        ...fetchOptions,
      })
      const data = await res.json()
      if (!data.success) {
        showNotification(data.message || "Erro ao reportar falha", "error")
        setReportFailureLoading(false)
        return
      }
      refetch()
    } catch {
      showNotification("Erro ao reportar falha", "error")
      setReportFailureLoading(false)
    }
  }, [fetchOptions, showNotification, refetch])

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
    fetchBedPreview,
    openBedPreviewForSkip,
    reportFailureLoading,
    reportManualFailure,
  }
}
