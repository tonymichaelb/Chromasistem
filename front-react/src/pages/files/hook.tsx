import { useState, useCallback, useRef, useEffect } from "react"
import { useNavigate } from "react-router-dom"

const fetchOptions = { credentials: "include" as RequestCredentials }

export interface GcodeFileItem {
  id: number
  name: string
  size: number
  uploaded: string
  last_printed: string | null
  print_count: number
  thumbnail: string | null
  print_time: string | null
  filament_used: number | null
  filament_type: string | null
  nozzle_temp: number | null
  bed_temp: number | null
  layer_height: number | null
  infill: number | null
}

export function useFiles() {
  const navigate = useNavigate()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [files, setFiles] = useState<GcodeFileItem[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState("")
  const [uploading, setUploading] = useState(false)
  const [notification, setNotification] = useState<{
    message: string
    type: "success" | "error" | "info"
  } | null>(null)
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false)
  const [fileToDeleteId, setFileToDeleteId] = useState<number | null>(null)
  const [printConfirm, setPrintConfirm] = useState<{ fileId: number; fileName: string } | null>(null)

  const showNotification = useCallback((message: string, type: "success" | "error" | "info" = "info") => {
    setNotification({ message, type })
    setTimeout(() => setNotification(null), 3000)
  }, [])

  const loadFiles = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch("/api/files/list", fetchOptions)
      if (res.status === 401) {
        navigate("/login")
        return
      }
      const data = await res.json()
      if (data.success && Array.isArray(data.files)) setFiles(data.files)
      else setFiles([])
    } catch {
      setFiles([])
      showNotification("Erro ao carregar arquivos", "error")
    } finally {
      setLoading(false)
    }
  }, [navigate, showNotification])

  const uploadFile = useCallback(
    async (file: File) => {
      const formData = new FormData()
      formData.append("file", file)
      setUploading(true)
      try {
        const res = await fetch("/api/files/upload", {
          method: "POST",
          credentials: "include",
          body: formData,
        })
        const data = await res.json()
        if (data.success) {
          showNotification("Arquivo enviado com sucesso!", "success")
          loadFiles()
        } else {
          showNotification(data.message || "Erro ao enviar arquivo", "error")
        }
      } catch (err) {
        showNotification("Erro ao enviar arquivo", "error")
      } finally {
        setUploading(false)
      }
    },
    [loadFiles, showNotification]
  )

  const openFileDialog = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (file) uploadFile(file)
      e.target.value = ""
    },
    [uploadFile]
  )

  const openDeleteConfirm = useCallback((fileId: number) => {
    setFileToDeleteId(fileId)
    setDeleteConfirmOpen(true)
  }, [])

  const closeDeleteConfirm = useCallback(() => {
    setDeleteConfirmOpen(false)
    setFileToDeleteId(null)
  }, [])

  const confirmDelete = useCallback(async () => {
    if (fileToDeleteId == null) return
    const id = fileToDeleteId
    closeDeleteConfirm()
    try {
      const res = await fetch(`/api/files/delete/${id}`, {
        method: "DELETE",
        ...fetchOptions,
      })
      const data = await res.json()
      if (data.success) {
        showNotification("Arquivo excluído com sucesso", "success")
        loadFiles()
      } else {
        showNotification(data.message || "Erro ao excluir", "error")
      }
    } catch {
      showNotification("Erro ao excluir arquivo", "error")
    }
  }, [fileToDeleteId, closeDeleteConfirm, loadFiles, showNotification])

  const openPrintConfirm = useCallback((fileId: number, fileName: string) => {
    setPrintConfirm({ fileId, fileName })
  }, [])

  const confirmPrint = useCallback(async () => {
    const payload = printConfirm
    setPrintConfirm(null)
    if (!payload) return
    try {
      const res = await fetch(`/api/files/print/${payload.fileId}`, {
        method: "POST",
        ...fetchOptions,
      })
      const data = await res.json()
      showNotification(data.message || "Impressão iniciada", data.success ? "success" : "error")
      if (data.success) loadFiles()
    } catch {
      showNotification("Erro ao iniciar impressão", "error")
    }
  }, [printConfirm, showNotification, loadFiles])

  const downloadFile = useCallback((fileId: number) => {
    window.open(`/api/files/download/${fileId}`, "_blank")
  }, [])

  const copyUploadUrl = useCallback(() => {
    const url = `${window.location.origin}/api/files/upload`
    navigator.clipboard.writeText(url)
    showNotification("URL copiada!", "success")
  }, [showNotification])

  const filteredFiles = searchTerm.trim()
    ? files.filter((f) => f.name.toLowerCase().includes(searchTerm.trim().toLowerCase()))
    : files

  useEffect(() => {
    loadFiles()
  }, [loadFiles])

  return {
    files: filteredFiles,
    loading,
    searchTerm,
    setSearchTerm,
    uploading,
    notification,
    fileInputRef,
    handleFileSelect,
    uploadFile,
    openFileDialog,
    loadFiles,
    deleteConfirmOpen,
    setDeleteConfirmOpen,
    closeDeleteConfirm,
    openDeleteConfirm,
    confirmDelete,
    printConfirm,
    setPrintConfirm,
    openPrintConfirm,
    confirmPrint,
    downloadFile,
    copyUploadUrl,
  }
}
