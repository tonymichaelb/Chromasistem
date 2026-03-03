import { useState, useCallback } from "react"
import { useNavigate } from "react-router-dom"

const fetchOptions = { credentials: "include" as RequestCredentials }

export type QualityPreset = "draft" | "normal" | "fine"

const QUALITY_LAYER_HEIGHT: Record<QualityPreset, number> = {
  draft: 0.28,
  normal: 0.2,
  fine: 0.12,
}

export interface SliceResult {
  file_id: number
  filename: string
}

export function useFatiador() {
  const navigate = useNavigate()
  const [slicing, setSlicing] = useState(false)
  const [result, setResult] = useState<SliceResult | null>(null)
  const [notification, setNotification] = useState<{
    message: string
    type: "success" | "error" | "info"
  } | null>(null)

  const showNotification = useCallback((message: string, type: "success" | "error" | "info" = "info") => {
    setNotification({ message, type })
    setTimeout(() => setNotification(null), 4000)
  }, [])

  const slice = useCallback(
    async (file: File, quality: QualityPreset, infill: number) => {
      setSlicing(true)
      setResult(null)
      const formData = new FormData()
      formData.append("file", file)
      formData.append("layer_height", String(QUALITY_LAYER_HEIGHT[quality]))
      formData.append("infill", String(infill))
      try {
        const res = await fetch("/api/slicer/slice", {
          method: "POST",
          credentials: "include",
          body: formData,
        })
        const data = await res.json()
        if (data.success) {
          setResult({ file_id: data.file_id, filename: data.filename })
          showNotification("G-code gerado com sucesso!", "success")
        } else {
          showNotification(data.message || "Erro ao fatiar", "error")
        }
      } catch {
        showNotification("Erro ao comunicar com o servidor", "error")
      } finally {
        setSlicing(false)
      }
    },
    [showNotification]
  )

  const sendToPrint = useCallback(
    async (fileId: number) => {
      try {
        const res = await fetch(`/api/files/print/${fileId}`, {
          method: "POST",
          ...fetchOptions,
        })
        const data = await res.json()
        showNotification(data.message || (data.success ? "Impressão iniciada" : "Erro"), data.success ? "success" : "error")
        if (data.success) navigate("/dashboard")
      } catch {
        showNotification("Erro ao iniciar impressão", "error")
      }
    },
    [navigate, showNotification]
  )

  const goToFiles = useCallback(() => {
    navigate("/files")
  }, [navigate])

  const resetResult = useCallback(() => {
    setResult(null)
  }, [])

  return {
    slicing,
    result,
    notification,
    slice,
    sendToPrint,
    goToFiles,
    resetResult,
    showNotification,
  }
}
