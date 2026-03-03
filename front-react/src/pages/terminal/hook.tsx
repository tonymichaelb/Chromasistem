import { useState, useCallback, useRef, useEffect } from "react"
import { useNavigate } from "react-router-dom"

const STATUS_POLL_MS = 5000
const HISTORY_POLL_MS = 1000
const TEMP_HISTORY_MAX = 50

const fetchOptions = { credentials: "include" as RequestCredentials }

interface TempReading {
  time: string
  nozzle: number
  bed: number
  targetNozzle: number
  targetBed: number
}

interface CommandHistoryItem {
  timestamp: string
  command: string
  type: "sent" | "response" | "error"
}

export function useTerminal() {
  const navigate = useNavigate()
  const [nozzleInput, setNozzleInput] = useState("210")
  const [bedInput, setBedInput] = useState("60")
  const [currentNozzle, setCurrentNozzle] = useState<number | null>(null)
  const [currentBed, setCurrentBed] = useState<number | null>(null)
  const [targetNozzle, setTargetNozzle] = useState<number | null>(null)
  const [targetBed, setTargetBed] = useState<number | null>(null)
  const [tempHistory, setTempHistory] = useState<TempReading[]>([])
  const [jogDistance, setJogDistance] = useState(10)
  const [terminalLines, setTerminalLines] = useState<{ text: string; type: "command" | "output" | "error" }[]>([
    { text: "Terminal G-code pronto. Digite comandos abaixo...", type: "output" },
  ])
  const [notification, setNotification] = useState<{ message: string; type: "success" | "error" | "info" } | null>(null)
  const historyCountRef = useRef(0)

  const showNotification = useCallback((message: string, type: "success" | "error" | "info" = "info") => {
    setNotification({ message, type })
    setTimeout(() => setNotification(null), 3000)
  }, [])

  const sendGcodeCommand = useCallback(
    async (command: string): Promise<{ success: boolean; response?: string }> => {
      try {
        const res = await fetch("/api/printer/gcode", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ command }),
          ...fetchOptions,
        })
        const data = await res.json()
        if (res.status === 401) {
          navigate("/login")
          return { success: false }
        }
        return { success: !!data.success, response: data.response }
      } catch {
        return { success: false }
      }
    },
    [navigate]
  )

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch("/api/printer/status", fetchOptions)
      if (res.status === 401) {
        navigate("/login")
        return
      }
      const data = await res.json()
      if (!data.success || !data.status) return
      const t = data.status.temperature
      setCurrentNozzle(t.nozzle ?? null)
      setCurrentBed(t.bed ?? null)
      setTargetNozzle(t.target_nozzle ?? null)
      setTargetBed(t.target_bed ?? null)
      setTempHistory((prev) => {
        const next = [
          ...prev,
          {
            time: new Date().toLocaleTimeString("pt-BR"),
            nozzle: t.nozzle ?? 0,
            bed: t.bed ?? 0,
            targetNozzle: t.target_nozzle ?? 0,
            targetBed: t.target_bed ?? 0,
          },
        ]
        return next.slice(-TEMP_HISTORY_MAX)
      })
    } catch {
      // ignore
    }
  }, [navigate])

  const fetchCommandsHistory = useCallback(async () => {
    try {
      const res = await fetch("/api/printer/commands-history", fetchOptions)
      if (res.status === 401) return
      const data = await res.json()
      if (!data.success || !Array.isArray(data.history) || data.history.length <= historyCountRef.current)
        return
      const newItems = data.history.slice(historyCountRef.current) as CommandHistoryItem[]
      historyCountRef.current = data.history.length
      setTerminalLines((prev) => [
        ...prev,
        ...newItems.map((item): { text: string; type: "command" | "output" | "error" } => {
          const timeStr = new Date(item.timestamp).toLocaleTimeString("pt-BR", {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
          })
          const prefix = item.type === "sent" ? ">" : item.type === "error" ? "!" : "<"
          const type: "command" | "output" | "error" = item.type === "sent" ? "command" : item.type === "error" ? "error" : "output"
          return { text: `${prefix} ${item.command} [${timeStr}]`, type }
        }),
      ])
    } catch {
      // ignore
    }
  }, [])

  useEffect(() => {
    fetchStatus()
    const t = setInterval(fetchStatus, STATUS_POLL_MS)
    return () => clearInterval(t)
  }, [fetchStatus])

  useEffect(() => {
    fetchCommandsHistory()
    const t = setInterval(fetchCommandsHistory, HISTORY_POLL_MS)
    return () => clearInterval(t)
  }, [fetchCommandsHistory])

  const setNozzleTemp = useCallback(
    async (temp?: number) => {
      const value = temp ?? parseInt(nozzleInput, 10)
      if (Number.isNaN(value)) return
      await sendGcodeCommand(`M104 S${value}`)
      showNotification(`Bico: ${value}°C`, "success")
    },
    [nozzleInput, sendGcodeCommand, showNotification]
  )

  const setBedTemp = useCallback(
    async (temp?: number) => {
      const value = temp ?? parseInt(bedInput, 10)
      if (Number.isNaN(value)) return
      await sendGcodeCommand(`M140 S${value}`)
      showNotification(`Mesa: ${value}°C`, "success")
    },
    [bedInput, sendGcodeCommand, showNotification]
  )

  const setPreset = useCallback(
    async (nozzle: number, bed: number) => {
      await sendGcodeCommand(`M104 S${nozzle}`)
      await sendGcodeCommand(`M140 S${bed}`)
      showNotification(`Preset: Bico ${nozzle}°C, Mesa ${bed}°C`, "success")
    },
    [sendGcodeCommand, showNotification]
  )

  const jogAxis = useCallback(
    async (axis: string, distance: number) => {
      await sendGcodeCommand("G91")
      await sendGcodeCommand(`G0 ${axis}${distance} F3000`)
      await sendGcodeCommand("G90")
      showNotification(`Moveu ${axis} ${distance}mm`, "info")
    },
    [sendGcodeCommand, showNotification]
  )

  const homeAxis = useCallback(
    async (axis: string) => {
      await sendGcodeCommand(`G28 ${axis}`)
      showNotification(`Home ${axis}`, "success")
    },
    [sendGcodeCommand, showNotification]
  )

  const homeAll = useCallback(async () => {
    await sendGcodeCommand("G28")
    showNotification("Home All concluído", "success")
  }, [sendGcodeCommand, showNotification])

  const extrudeFilament = useCallback(
    async (distance: number) => {
      await sendGcodeCommand("G91")
      await sendGcodeCommand(`G1 E${distance} F300`)
      await sendGcodeCommand("G90")
      showNotification(distance > 0 ? `Extrudou ${distance}mm` : `Retraiu ${Math.abs(distance)}mm`, "info")
    },
    [sendGcodeCommand, showNotification]
  )

  const preheatExtruder = useCallback(async () => {
    await sendGcodeCommand("M104 S210")
    showNotification("Pre-aquecendo extrusora para 210°C", "success")
  }, [sendGcodeCommand, showNotification])

  const syncHistoryCount = useCallback(async () => {
    try {
      const res = await fetch("/api/printer/commands-history", fetchOptions)
      const data = await res.json()
      if (data.success && typeof data.count === "number") historyCountRef.current = data.count
    } catch {
      // ignore
    }
  }, [])

  const sendGcode = useCallback(
    async (command: string) => {
      if (!command.trim()) return
      setTerminalLines((prev) => [...prev, { text: `> ${command}`, type: "command" }])
      const result = await sendGcodeCommand(command)
      if (result.success && result.response != null) {
        setTerminalLines((prev) => [...prev, { text: `< ${result.response}`, type: "output" }])
      } else if (!result.success) {
        setTerminalLines((prev) => [...prev, { text: `! ${result.response ?? "Sem resposta"}`, type: "error" }])
      }
      await syncHistoryCount()
    },
    [sendGcodeCommand, syncHistoryCount]
  )

  const clearTerminal = useCallback(() => {
    setTerminalLines([{ text: "Terminal limpo.", type: "output" }])
  }, [])

  const quickCommand = useCallback(
    async (cmd: string) => {
      setTerminalLines((prev) => [...prev, { text: `> ${cmd}`, type: "command" }])
      const result = await sendGcodeCommand(cmd)
      if (result.success && result.response != null) {
        setTerminalLines((prev) => [...prev, { text: `< ${result.response}`, type: "output" }])
      } else if (!result.success) {
        setTerminalLines((prev) => [...prev, { text: `! ${result.response ?? "Sem resposta"}`, type: "error" }])
      }
      await syncHistoryCount()
    },
    [sendGcodeCommand, syncHistoryCount]
  )

  return {
    nozzleInput,
    setNozzleInput,
    bedInput,
    setBedInput,
    currentNozzle,
    currentBed,
    targetNozzle,
    targetBed,
    tempHistory,
    jogDistance,
    setJogDistance,
    terminalLines,
    notification,
    setNozzleTemp,
    setBedTemp,
    setPreset,
    jogAxis,
    homeAxis,
    homeAll,
    extrudeFilament,
    preheatExtruder,
    sendGcode,
    clearTerminal,
    quickCommand,
  }
}
