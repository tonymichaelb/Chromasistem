import { useState, useCallback } from "react"
import { useNavigate } from "react-router-dom"
import { useSelectedPrintFile } from "@/contexts/SelectedPrintFileContext"

const fetchOptions = { credentials: "include" as RequestCredentials }
const POLL_MS = 2500
const WAIT_PRINTING_TIMEOUT_MS = 120000

export function useRevisao() {
  const navigate = useNavigate()
  const { selectedFile } = useSelectedPrintFile()
  const [notification, setNotification] = useState<{ message: string; type: "success" | "error" | "info" } | null>(null)
  const [printConfirmOpen, setPrintConfirmOpen] = useState(false)
  const [waitingForPrintStart, setWaitingForPrintStart] = useState(false)

  const showNotification = useCallback((message: string, type: "success" | "error" | "info" = "info") => {
    setNotification({ message, type })
    setTimeout(() => setNotification(null), 3000)
  }, [])

  const openPrintConfirm = useCallback(() => setPrintConfirmOpen(true), [])
  const closePrintConfirm = useCallback(() => setPrintConfirmOpen(false), [])

  const confirmPrint = useCallback(async () => {
    if (!selectedFile) return
    setPrintConfirmOpen(false)
    setWaitingForPrintStart(true)
    try {
      const res = await fetch(`/api/files/print/${selectedFile.id}`, {
        method: "POST",
        ...fetchOptions,
      })
      const data = await res.json()
      if (!data.success) {
        setWaitingForPrintStart(false)
        showNotification(data.message || "Erro ao iniciar impressão", "error")
        return
      }
      const deadline = Date.now() + WAIT_PRINTING_TIMEOUT_MS
      while (Date.now() < deadline) {
        await new Promise((r) => setTimeout(r, POLL_MS))
        const statusRes = await fetch("/api/printer/status", { ...fetchOptions })
        if (statusRes.status !== 200) continue
        const statusData = await statusRes.json()
        if (statusData?.status?.state === "printing") {
          setWaitingForPrintStart(false)
          navigate("/dashboard")
          return
        }
      }
      setWaitingForPrintStart(false)
      showNotification("Impressão iniciada no servidor. Acompanhe no Monitor.", "info")
      navigate("/dashboard")
    } catch {
      setWaitingForPrintStart(false)
      showNotification("Erro ao iniciar impressão", "error")
    }
  }, [selectedFile, showNotification, navigate])

  return {
    selectedFile,
    notification,
    setNotification,
    printConfirmOpen,
    setPrintConfirmOpen,
    openPrintConfirm,
    closePrintConfirm,
    confirmPrint,
    showNotification,
    waitingForPrintStart,
  }
}
