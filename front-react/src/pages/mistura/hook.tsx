import { useState, useCallback } from "react"
import { useNavigate } from "react-router-dom"

const fetchOptions = { credentials: "include" as RequestCredentials }

export interface CmyMix {
  a: number
  b: number
  c: number
}

const defaultMix = (): CmyMix => ({ a: 33, b: 33, c: 34 })

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

function distributePercentages(
  current: CmyMix,
  changedKey: "a" | "b" | "c",
  newVal: number
): CmyMix {
  const clamped = Math.max(0, Math.min(100, newVal))
  const remaining = 100 - clamped
  const keys: Array<"a" | "b" | "c"> = ["a", "b", "c"]
  const otherKeys = keys.filter((k) => k !== changedKey) as ["a" | "b" | "c", "a" | "b" | "c"]
  const [o1, o2] = otherKeys
  const sumOther = current[o1] + current[o2]
  if (clamped >= 100)
    return {
      a: changedKey === "a" ? 100 : 0,
      b: changedKey === "b" ? 100 : 0,
      c: changedKey === "c" ? 100 : 0,
    }
  if (sumOther <= 0) {
    const half = Math.floor(remaining / 2)
    return { [changedKey]: clamped, [o1]: half, [o2]: remaining - half } as unknown as CmyMix
  }
  const ratio = remaining / sumOther
  const v1 = Math.floor(current[o1] * ratio)
  const v2 = remaining - v1
  return { [changedKey]: clamped, [o1]: v1, [o2]: v2 } as unknown as CmyMix
}

export function useMistura() {
  const navigate = useNavigate()
  const [mix, setMix] = useState<CmyMix>(defaultMix)
  const [suggestColorHex, setSuggestColorHex] = useState("#808080")
  const [notification, setNotification] = useState<{
    message: string
    type: "success" | "error" | "info"
  } | null>(null)
  const [sending, setSending] = useState(false)

  const showNotification = useCallback((message: string, type: "success" | "error" | "info" = "info") => {
    setNotification({ message, type })
    setTimeout(() => setNotification(null), 5000)
  }, [])

  const updateSlider = useCallback((key: "a" | "b" | "c", value: number) => {
    setMix((prev) => distributePercentages(prev, key, value))
  }, [])

  const applySuggestColor = useCallback((hex: string) => {
    setSuggestColorHex(hex)
    const rgb = hexToRgb(hex)
    const next = rgbToCmyPercent(rgb.r, rgb.g, rgb.b)
    setMix(next)
  }, [])

  const sendMixture = useCallback(async () => {
    const sum = mix.a + mix.b + mix.c
    if (sum !== 100) return
    setSending(true)
    try {
      const res = await fetch("/api/printer/send-mixture", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          command: `M182 A${mix.a} B${mix.b} C${mix.c}`,
        }),
        ...fetchOptions,
      })
      if (res.status === 401) {
        navigate("/login")
        return
      }
      const data = await res.json()
      if (data.success) {
        showNotification(`Mistura enviada: M182 A${mix.a} B${mix.b} C${mix.c}`, "success")
      } else {
        showNotification(data.message ?? "Erro ao enviar", "error")
      }
    } catch (err) {
      showNotification("Erro ao enviar mistura", "error")
    } finally {
      setSending(false)
    }
  }, [mix, navigate, showNotification])

  const sum = mix.a + mix.b + mix.c
  const isValid = sum === 100
  const commandPreview = `M182 A${mix.a} B${mix.b} C${mix.c}`

  return {
    mix,
    suggestColorHex,
    notification,
    sending,
    isValid,
    commandPreview,
    updateSlider,
    applySuggestColor,
    sendMixture,
  }
}
