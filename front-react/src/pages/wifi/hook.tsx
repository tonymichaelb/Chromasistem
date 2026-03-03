import { useState, useCallback, useEffect, type FormEvent } from "react"
import { useNavigate } from "react-router-dom"

const fetchOptions = { credentials: "include" as RequestCredentials }
const STATUS_POLL_MS = 10000

export interface WifiStatus {
  connected: boolean
  ssid: string | null
  ip: string | null
  is_hotspot: boolean
}

export interface ScannedNetwork {
  ssid: string
  signal: number
  security: string
}

export interface UseWifiReturn {
  status: WifiStatus | null
  savedNetworks: string[]
  availableNetworks: ScannedNetwork[] | null
  loadingStatus: boolean
  loadingSaved: boolean
  scanning: boolean
  notification: { message: string; type: "success" | "error" | "info" } | null
  connectModalOpen: boolean
  setConnectModalOpen: (open: boolean) => void
  connectSSID: string
  connectPassword: string
  setConnectPassword: (v: string) => void
  showConnectPassword: boolean
  setShowConnectPassword: (v: boolean) => void
  connectLoading: boolean
  openConnectModal: (ssid: string) => void
  closeConnectModal: () => void
  connectToNetwork: (e?: FormEvent<HTMLFormElement>) => Promise<void>
  forgetConfirmOpen: boolean
  setForgetConfirmOpen: (open: boolean) => void
  networkToForget: string | null
  openForgetConfirm: (ssid: string) => void
  closeForgetConfirm: () => void
  forgetNetwork: () => Promise<void>
  loadWifiStatus: () => Promise<void>
  loadSavedNetworks: () => Promise<void>
  scanNetworks: () => Promise<void>
  currentSSID: string
  showNotification: (message: string, type?: "success" | "error" | "info") => void
}

export function useWifi(): UseWifiReturn {
  const navigate = useNavigate()
  const [status, setStatus] = useState<WifiStatus | null>(null)
  const [savedNetworks, setSavedNetworks] = useState<string[]>([])
  const [availableNetworks, setAvailableNetworks] = useState<ScannedNetwork[] | null>(null)
  const [loadingStatus, setLoadingStatus] = useState(true)
  const [loadingSaved, setLoadingSaved] = useState(true)
  const [scanning, setScanning] = useState(false)
  const [notification, setNotification] = useState<{
    message: string
    type: "success" | "error" | "info"
  } | null>(null)
  const [connectModalOpen, setConnectModalOpen] = useState(false)
  const [connectSSID, setConnectSSID] = useState("")
  const [connectPassword, setConnectPassword] = useState("")
  const [connectLoading, setConnectLoading] = useState(false)
  const [showConnectPassword, setShowConnectPassword] = useState(false)
  const [forgetConfirmOpen, setForgetConfirmOpen] = useState(false)
  const [networkToForget, setNetworkToForget] = useState<string | null>(null)
  const [, setForgetLoading] = useState(false)

  const showNotification = useCallback((message: string, type: "success" | "error" | "info" = "info") => {
    setNotification({ message, type })
    setTimeout(() => setNotification(null), 4000)
  }, [])

  const api = useCallback(
    async <T,>(url: string, options?: RequestInit): Promise<T> => {
      const res = await fetch(url, { ...fetchOptions, ...options })
      if (res.status === 401) {
        navigate("/login")
        throw new Error("Unauthorized")
      }
      return res.json() as Promise<T>
    },
    [navigate]
  )

  const loadWifiStatus = useCallback(async () => {
    setLoadingStatus(true)
    try {
      const data = await api<{ success: boolean; status?: WifiStatus }>("/api/wifi/status")
      if (data.success && data.status) setStatus(data.status)
      else setStatus({ connected: false, ssid: null, ip: null, is_hotspot: false })
    } catch {
      setStatus({ connected: false, ssid: null, ip: null, is_hotspot: false })
    } finally {
      setLoadingStatus(false)
    }
  }, [api])

  const loadSavedNetworks = useCallback(async () => {
    setLoadingSaved(true)
    try {
      const data = await api<{ success: boolean; networks?: string[] }>("/api/wifi/saved")
      if (data.success && Array.isArray(data.networks)) setSavedNetworks(data.networks)
      else setSavedNetworks([])
    } catch {
      setSavedNetworks([])
    } finally {
      setLoadingSaved(false)
    }
  }, [api])

  const scanNetworks = useCallback(async () => {
    setScanning(true)
    setAvailableNetworks([])
    try {
      const data = await api<{ success: boolean; networks?: ScannedNetwork[] }>("/api/wifi/scan")
      if (data.success && Array.isArray(data.networks)) setAvailableNetworks(data.networks)
      else setAvailableNetworks([])
    } catch {
      setAvailableNetworks([])
      showNotification("Erro ao escanear redes", "error")
    } finally {
      setScanning(false)
    }
  }, [api, showNotification])

  useEffect(() => {
    loadWifiStatus()
    loadSavedNetworks()
  }, [loadWifiStatus, loadSavedNetworks])

  useEffect(() => {
    const t = setInterval(loadWifiStatus, STATUS_POLL_MS)
    return () => clearInterval(t)
  }, [loadWifiStatus])

  const openConnectModal = useCallback((ssid: string) => {
    setConnectSSID(ssid)
    setConnectPassword("")
    setConnectModalOpen(true)
  }, [])

  const closeConnectModal = useCallback(() => {
    setConnectModalOpen(false)
    setConnectSSID("")
    setConnectPassword("")
  }, [])

  const connectToNetwork = useCallback(
    async (e?: React.FormEvent) => {
      e?.preventDefault()
      if (!connectSSID.trim()) return
      setConnectLoading(true)
      try {
        const data = await api<{ success: boolean; message?: string }>("/api/wifi/connect", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ssid: connectSSID, password: connectPassword }),
        })
        if (data.success) {
          showNotification("Conectado com sucesso!", "success")
          closeConnectModal()
          setTimeout(() => {
            loadWifiStatus()
            loadSavedNetworks()
          }, 2000)
        } else {
          showNotification(data.message ?? "Erro ao conectar", "error")
        }
      } catch {
        showNotification("Erro ao conectar", "error")
      } finally {
        setConnectLoading(false)
      }
    },
    [connectSSID, connectPassword, api, showNotification, closeConnectModal, loadWifiStatus, loadSavedNetworks]
  )

  const openForgetConfirm = useCallback((ssid: string) => {
    setNetworkToForget(ssid)
    setForgetConfirmOpen(true)
  }, [])

  const closeForgetConfirm = useCallback(() => {
    setForgetConfirmOpen(false)
    setNetworkToForget(null)
  }, [])

  const forgetNetwork = useCallback(async () => {
    if (!networkToForget) return
    const ssid = networkToForget
    closeForgetConfirm()
    setForgetLoading(true)
    try {
      const data = await api<{ success: boolean; message?: string }>("/api/wifi/forget", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ssid }),
      })
      if (data.success) {
        showNotification("Rede removida com sucesso!", "success")
        loadSavedNetworks()
      } else {
        showNotification(data.message ?? "Erro ao remover rede", "error")
      }
    } catch {
      showNotification("Erro ao remover rede", "error")
    } finally {
      setForgetLoading(false)
    }
  }, [networkToForget, api, showNotification, closeForgetConfirm, loadSavedNetworks])

  const currentSSID = status?.ssid ?? ""

  return {
    status,
    savedNetworks,
    availableNetworks,
    loadingStatus,
    loadingSaved,
    scanning,
    notification,
    connectModalOpen,
    setConnectModalOpen,
    connectSSID,
    connectPassword,
    setConnectPassword,
    showConnectPassword,
    setShowConnectPassword,
    connectLoading,
    openConnectModal,
    closeConnectModal,
    connectToNetwork,
    forgetConfirmOpen,
    setForgetConfirmOpen,
    networkToForget,
    openForgetConfirm,
    closeForgetConfirm,
    forgetNetwork,
    loadWifiStatus,
    loadSavedNetworks,
    scanNetworks,
    currentSSID,
    showNotification,
  }
}
