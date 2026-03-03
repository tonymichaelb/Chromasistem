import { useState, useCallback, useEffect } from "react"
import { useNavigate } from "react-router-dom"

const fetchOptions = { credentials: "include" as RequestCredentials }
const BRUSH_COUNT = 19

const TINTA_DEFAULT_COLORS: Record<number, string> = {
  0: "#000000",
  1: "#FF0000",
  2: "#00AA00",
  3: "#0000FF",
  4: "#FFFF00",
  5: "#FF00FF",
  6: "#00FFFF",
  7: "#FFFFFF",
  8: "#FFA500",
  9: "#FF69B4",
  10: "#800080",
  11: "#8B4513",
  12: "#808080",
  13: "#8B0000",
  14: "#006400",
  15: "#00008B",
  16: "#FFD700",
  17: "#C0C0C0",
  18: "#B87333",
}

export interface CmyMix {
  a: number
  b: number
  c: number
}

const defaultMixture = (): CmyMix => ({ a: 33, b: 33, c: 34 })

function hexToRgb(hex: string): { r: number; g: number; b: number } {
  const n = parseInt(hex.slice(1), 16)
  return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255 }
}

function rgbToHsv(r: number, g: number, b: number): { h: number; s: number; v: number } {
  r /= 255
  g /= 255
  b /= 255
  const max = Math.max(r, g, b),
    min = Math.min(r, g, b)
  const d = max - min
  const v = max
  const s = max === 0 ? 0 : d / max
  let h = 0
  if (d !== 0) {
    if (max === r) h = (g - b) / d + (g < b ? 6 : 0)
    else if (max === g) h = (b - r) / d + 2
    else h = (r - g) / d + 4
    h /= 6
  }
  return { h, s, v }
}

export function rgbToCmyPercent(r: number, g: number, b: number): CmyMix {
  const R = r / 255,
    G = g / 255,
    B = b / 255
  let c = (G + B - R) / 2,
    m = (R + B - G) / 2,
    y = (R + G - B) / 2
  c = Math.max(0, Math.min(1, c))
  m = Math.max(0, Math.min(1, m))
  y = Math.max(0, Math.min(1, y))
  let total = c + m + y
  if (total <= 0) return { a: 33, b: 33, c: 34 }
  const scale = 100 / total
  let aPct = c * scale,
    bPct = m * scale,
    cPct = y * scale
  const hsv = rgbToHsv(r, g, b)
  const neutral = { a: 33, b: 33, c: 34 }
  const hueMix = { a: aPct, b: bPct, c: cPct }
  const V = hsv.v
  const blendA = V * hueMix.a + (1 - V) * neutral.a
  const blendB = V * hueMix.b + (1 - V) * neutral.b
  const blendC = V * hueMix.c + (1 - V) * neutral.c
  const sumBlend = blendA + blendB + blendC
  const scaleBlend = sumBlend > 0 ? 100 / sumBlend : 1
  let aPctFinal = Math.round(blendA * scaleBlend),
    bPctFinal = Math.round(blendB * scaleBlend),
    cPctFinal = Math.round(blendC * scaleBlend)
  if (aPctFinal + bPctFinal + cPctFinal !== 100)
    cPctFinal += 100 - aPctFinal - bPctFinal - cPctFinal
  return { a: aPctFinal, b: bPctFinal, c: Math.max(0, cPctFinal) }
}

const STORAGE_KEYS = {
  brushCustomColors: "brushCustomColors",
  tintaCustomColors: "tintaCustomColors",
  brushMixtures: "brushMixtures",
} as const

function loadJson<T>(key: string, fallback: T): T {
  try {
    const s = localStorage.getItem(key)
    return s ? (JSON.parse(s) as T) : fallback
  } catch {
    return fallback
  }
}

function saveJson(key: string, value: unknown) {
  localStorage.setItem(key, JSON.stringify(value))
}

export function useColorir() {
  const navigate = useNavigate()
  const [currentBrushIndex, setCurrentBrushIndex] = useState<number | null>(null)
  const [brushCustomColors, setBrushCustomColors] = useState<Record<number, string>>(() =>
    loadJson(STORAGE_KEYS.brushCustomColors, {})
  )
  const [tintaCustomColors, setTintaCustomColors] = useState<Record<number, string>>(() =>
    loadJson(STORAGE_KEYS.tintaCustomColors, {})
  )
  const [brushMixtures, setBrushMixtures] = useState<Record<number, CmyMix>>(() => {
    const stored = loadJson<Record<string, { a: number; b: number; c: number }>>(
      STORAGE_KEYS.brushMixtures,
      {}
    )
    const out: Record<number, CmyMix> = {}
    for (let i = 0; i < BRUSH_COUNT; i++) out[i] = stored[String(i)] ?? defaultMixture()
    return out
  })
  const [notification, setNotification] = useState<{
    message: string
    type: "success" | "error" | "info"
  } | null>(null)
  const [mixtureModalOpen, setMixtureModalOpen] = useState(false)
  const [editingTintaIndex, setEditingTintaIndex] = useState<number | null>(null)
  const [modalSliders, setModalSliders] = useState<CmyMix>(defaultMixture())
  const [modalCustomColor, setModalCustomColor] = useState("#808080")
  const [customColorHex, setCustomColorHex] = useState("#808080")
  const [customCmy, setCustomCmy] = useState<CmyMix>(() => {
    const rgb = hexToRgb("#808080")
    return rgbToCmyPercent(rgb.r, rgb.g, rgb.b)
  })
  const [helpOpen, setHelpOpen] = useState(false)

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

  const loadCurrentBrush = useCallback(async () => {
    try {
      const data = await api<{ success: boolean; brush?: number }>("/api/printer/current-brush")
      if (data.success && typeof data.brush === "number") setCurrentBrushIndex(data.brush)
    } catch {
      // ignore
    }
  }, [api])

  const loadBrushMixtures = useCallback(async () => {
    try {
      const data = await api<{
        success: boolean
        mixtures?: Record<string, CmyMix>
        colors?: Record<string, string>
        tintaColors?: Record<string, string>
      }>("/api/printer/load-brush-mixtures")
      if (!data.success) return
      if (data.mixtures) {
        const mix: Record<number, CmyMix> = {}
        for (let i = 0; i < BRUSH_COUNT; i++) mix[i] = defaultMixture()
        Object.entries(data.mixtures).forEach(([k, v]) => {
          const i = parseInt(k, 10)
          if (!Number.isNaN(i) && 0 <= i && i < BRUSH_COUNT && v) mix[i] = v as CmyMix
        })
        setBrushMixtures(mix)
      }
      if (data.colors) {
        const col: Record<number, string> = {}
        Object.entries(data.colors).forEach(([k, v]) => {
          const i = parseInt(k, 10)
          if (!Number.isNaN(i) && v) col[i] = v
        })
        setBrushCustomColors(col)
      }
      if (data.tintaColors) {
        const col: Record<number, string> = {}
        Object.entries(data.tintaColors).forEach(([k, v]) => {
          const i = parseInt(k, 10)
          if (!Number.isNaN(i) && v) col[i] = v
        })
        setTintaCustomColors(col)
      }
    } catch {
      // ignore
    }
  }, [api])

  useEffect(() => {
    loadCurrentBrush()
    loadBrushMixtures()
  }, [loadCurrentBrush, loadBrushMixtures])

  const sendMixtureForBrush = useCallback(
    async (_brushIndex: number, mix: CmyMix) => {
      try {
        await api("/api/printer/send-mixture", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ command: `M182 A${mix.a} B${mix.b} C${mix.c}` }),
        })
      } catch {
        // ignore
      }
    },
    [api]
  )

  const saveToServer = useCallback(
    async (mixtures: Record<number, CmyMix>, colors: Record<number, string>, tintaColors: Record<number, string>) => {
      const toStr = (o: Record<number, unknown>) => {
        const out: Record<string, unknown> = {}
        Object.entries(o).forEach(([k, v]) => {
          out[k] = v
        })
        return out
      }
      try {
        await api("/api/printer/save-brush-mixtures", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            mixtures: toStr(mixtures),
            colors: toStr(colors),
            tintaColors: toStr(tintaColors),
          }),
        })
      } catch {
        // ignore
      }
    },
    [api]
  )

  const selectBrush = useCallback(
    async (index: number) => {
      setCurrentBrushIndex(index)
      const mix = brushMixtures[index] ?? defaultMixture()
      showNotification(
        `Pincel ${index + 1} selecionado! Clique em uma tinta abaixo para aplicar.`,
        "success"
      )
      try {
        await api("/api/printer/select-brush", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ brush: index }),
        })
        await sendMixtureForBrush(index, mix)
      } catch {
        showNotification("Comando T pode não ter sido enviado", "info")
      }
    },
    [brushMixtures, api, sendMixtureForBrush, showNotification]
  )

  const applyTintaToBrush = useCallback(
    async (tintaIndex: number) => {
      if (currentBrushIndex === null) {
        showNotification("Primeiro escolha um pincel acima.", "error")
        return
      }
      const tintaColor = tintaCustomColors[tintaIndex] ?? TINTA_DEFAULT_COLORS[tintaIndex]
      const tintaMixture = brushMixtures[tintaIndex] ?? defaultMixture()
      const newBrushColors = { ...brushCustomColors, [currentBrushIndex]: tintaColor }
      const newMixtures = { ...brushMixtures, [currentBrushIndex]: tintaMixture }
      setBrushCustomColors(newBrushColors)
      setBrushMixtures(newMixtures)
      saveJson(STORAGE_KEYS.brushCustomColors, newBrushColors)
      saveJson(STORAGE_KEYS.brushMixtures, newMixtures)
      await sendMixtureForBrush(currentBrushIndex, tintaMixture)
      await saveToServer(newMixtures, newBrushColors, tintaCustomColors)
      showNotification(`Pincel ${currentBrushIndex + 1} agora tem a cor da Tinta ${tintaIndex + 1}!`, "success")
    },
    [
      currentBrushIndex,
      brushCustomColors,
      brushMixtures,
      tintaCustomColors,
      sendMixtureForBrush,
      saveToServer,
      showNotification,
    ]
  )

  const openMixtureModal = useCallback((tintaIndex: number) => {
    setEditingTintaIndex(tintaIndex)
    const mix = brushMixtures[tintaIndex] ?? defaultMixture()
    setModalSliders(mix)
    const color = tintaCustomColors[tintaIndex] ?? TINTA_DEFAULT_COLORS[tintaIndex]
    setModalCustomColor(color)
    setMixtureModalOpen(true)
  }, [brushMixtures, tintaCustomColors])

  const distributePercentages = useCallback((current: CmyMix, changedKey: "a" | "b" | "c", newVal: number): CmyMix => {
    const clamped = Math.max(0, Math.min(100, newVal))
    const remaining = 100 - clamped
    const keys: Array<"a" | "b" | "c"> = ["a", "b", "c"]
    const otherKeys = keys.filter((k) => k !== changedKey) as [ "a" | "b" | "c", "a" | "b" | "c" ]
    const [o1, o2] = otherKeys
    const sumOther = current[o1] + current[o2]
    if (clamped >= 100) return { a: changedKey === "a" ? 100 : 0, b: changedKey === "b" ? 100 : 0, c: changedKey === "c" ? 100 : 0 }
    if (sumOther <= 0) {
      const half = Math.floor(remaining / 2)
      return { [changedKey]: clamped, [o1]: half, [o2]: remaining - half } as unknown as CmyMix
    }
    const ratio = remaining / sumOther
    const v1 = Math.floor(current[o1] * ratio)
    const v2 = remaining - v1
    return { [changedKey]: clamped, [o1]: v1, [o2]: v2 } as unknown as CmyMix
  }, [])

  const updateModalSlider = useCallback(
    (key: "a" | "b" | "c", value: number) => {
      setModalSliders((prev) => distributePercentages(prev, key, value))
    },
    [distributePercentages]
  )

  const saveMixtureModal = useCallback(() => {
    if (editingTintaIndex === null) return
    const mix = modalSliders
    const newMixtures = { ...brushMixtures, [editingTintaIndex]: mix }
    const newTintaColors = { ...tintaCustomColors, [editingTintaIndex]: modalCustomColor }
    setBrushMixtures(newMixtures)
    setTintaCustomColors(newTintaColors)
    saveJson(STORAGE_KEYS.brushMixtures, newMixtures)
    saveJson(STORAGE_KEYS.tintaCustomColors, newTintaColors)
    saveToServer(newMixtures, brushCustomColors, newTintaColors)
    setMixtureModalOpen(false)
    setEditingTintaIndex(null)
    showNotification("Configurações salvas com sucesso!", "success")
  }, [editingTintaIndex, modalSliders, modalCustomColor, brushMixtures, tintaCustomColors, brushCustomColors, saveToServer, showNotification])

  const updateCustomColorFromHex = useCallback((hex: string) => {
    setCustomColorHex(hex)
    const rgb = hexToRgb(hex)
    const mix = rgbToCmyPercent(rgb.r, rgb.g, rgb.b)
    setCustomCmy(mix)
    return mix
  }, [])

  const applyCustomColorToBrush = useCallback(() => {
    if (currentBrushIndex === null) {
      showNotification("Primeiro escolha um pincel acima.", "error")
      return
    }
    const mix = updateCustomColorFromHex(customColorHex)
    const newBrushColors = { ...brushCustomColors, [currentBrushIndex]: customColorHex }
    const newMixtures = { ...brushMixtures, [currentBrushIndex]: mix }
    setBrushCustomColors(newBrushColors)
    setBrushMixtures(newMixtures)
    saveJson(STORAGE_KEYS.brushCustomColors, newBrushColors)
    saveJson(STORAGE_KEYS.brushMixtures, newMixtures)
    sendMixtureForBrush(currentBrushIndex, mix)
    saveToServer(newMixtures, newBrushColors, tintaCustomColors)
    showNotification(`Cor personalizada aplicada ao Pincel ${currentBrushIndex + 1}!`, "success")
  }, [currentBrushIndex, customColorHex, brushCustomColors, brushMixtures, tintaCustomColors, updateCustomColorFromHex, sendMixtureForBrush, saveToServer, showNotification])

  return {
    currentBrushIndex,
    brushCustomColors,
    tintaCustomColors,
    brushMixtures,
    notification,
    mixtureModalOpen,
    setMixtureModalOpen,
    editingTintaIndex,
    modalSliders,
    setModalSliders,
    modalCustomColor,
    setModalCustomColor,
    customColorHex,
    setCustomColorHex,
    customCmy,
    updateCustomColorFromHex,
    helpOpen,
    setHelpOpen,
    selectBrush,
    applyTintaToBrush,
    openMixtureModal,
    updateModalSlider,
    saveMixtureModal,
    applyCustomColorToBrush,
    TINTA_DEFAULT_COLORS,
    BRUSH_COUNT,
    showNotification,
  }
}
