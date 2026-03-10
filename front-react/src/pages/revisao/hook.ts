import { useState, useCallback } from "react"
import { useSelectedPrintFile } from "@/contexts/SelectedPrintFileContext"

const fetchOptions = { credentials: "include" as RequestCredentials }

export function useRevisao() {
  const { selectedFile } = useSelectedPrintFile()
  const [notification, setNotification] = useState<{ message: string; type: "success" | "error" | "info" } | null>(null)
  const [printConfirmOpen, setPrintConfirmOpen] = useState(false)

  const showNotification = useCallback((message: string, type: "success" | "error" | "info" = "info") => {
    setNotification({ message, type })
    setTimeout(() => setNotification(null), 3000)
  }, [])

  const openPrintConfirm = useCallback(() => setPrintConfirmOpen(true), [])
  const closePrintConfirm = useCallback(() => setPrintConfirmOpen(false), [])

  const confirmPrint = useCallback(async () => {
    if (!selectedFile) return
    setPrintConfirmOpen(false)
    try {
      const res = await fetch(`/api/files/print/${selectedFile.id}`, {
        method: "POST",
        ...fetchOptions,
      })
      const data = await res.json()
      showNotification(data.message || "Impressão iniciada", data.success ? "success" : "error")
    } catch {
      showNotification("Erro ao iniciar impressão", "error")
    }
  }, [selectedFile, showNotification])

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
  }
}
