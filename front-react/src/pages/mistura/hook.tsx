import { useState, useCallback } from "react"
import { useNavigate } from "react-router-dom"
import { usePrinterCommand } from "@/contexts/PrinterCommandContext"

const fetchOptions = { credentials: "include" as RequestCredentials }

export interface CmyMix {
  a: number
  b: number
  c: number
}

const defaultMix = (): CmyMix => ({ a: 33, b: 33, c: 34 })

export const defaultExtrusorColors = {
  a: "#00CED1", // ciano
  b: "#DC143C", // magenta
  c: "#FFD700", // amarelo
} as const

export type ExtrusorColors = { a: string; b: string; c: string }

function hexToRgb(hex: string): { r: number; g: number; b: number } {
  const n = parseInt(hex.slice(1), 16)
  return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255 }
}

/**
 * Calcula as porcentagens (a, b, c) para que a mistura das três cores das extrusoras
 * fique o mais próximo possível da cor alvo (inverse blending).
 */
function targetHexToMix(
  targetHex: string,
  colors: { a: string; b: string; c: string }
): CmyMix {
  const t = hexToRgb(targetHex)
  const A = hexToRgb(colors.a)
  const B = hexToRgb(colors.b)
  const C = hexToRgb(colors.c)
  const b = [100 * t.r, 100 * t.g, 100 * t.b]
  const rA = A.r, rB = B.r, rC = C.r
  const gA = A.g, gB = B.g, gC = C.g
  const bA = A.b, bB = B.b, bC = C.b
  const det = rA * (gB * bC - gC * bB) - rB * (gA * bC - gC * bA) + rC * (gA * bB - gB * bA)
  if (Math.abs(det) < 1e-6) return { a: 33, b: 33, c: 34 }
  const wA = (b[0] * (gB * bC - gC * bB) - rB * (b[1] * bC - b[2] * gC) + rC * (b[1] * bB - b[2] * gB)) / det
  const wB = (rA * (b[1] * bC - b[2] * gC) - b[0] * (gA * bC - gC * bA) + rC * (gA * b[2] - b[1] * bA)) / det
  const wC = (rA * (gB * b[2] - b[1] * bB) - rB * (gA * b[2] - b[1] * bA) + b[0] * (gA * bB - gB * bA)) / det
  let wa = Math.max(0, Math.min(100, wA))
  let wb = Math.max(0, Math.min(100, wB))
  let wc = Math.max(0, Math.min(100, wC))
  const sum = wa + wb + wc
  if (sum <= 0) return { a: 33, b: 33, c: 34 }
  wa = (wa * 100) / sum
  wb = (wb * 100) / sum
  wc = (wc * 100) / sum
  let a = Math.round(wa), b_ = Math.round(wb), c = Math.round(wc)
  const total = a + b_ + c
  if (total !== 100) {
    const diff = 100 - total
    if (diff > 0 && a < 100) a = Math.min(100, a + diff)
    else if (diff > 0 && b_ < 100) b_ = Math.min(100, b_ + diff)
    else if (diff > 0 && c < 100) c = Math.min(100, c + diff)
    else if (diff < 0 && a > 0) a = Math.max(0, a + diff)
    else if (diff < 0 && b_ > 0) b_ = Math.max(0, b_ + diff)
    else if (diff < 0 && c > 0) c = Math.max(0, c + diff)
  }
  return { a: Math.max(0, Math.min(100, a)), b: Math.max(0, Math.min(100, b_)), c: Math.max(0, Math.min(100, c)) }
}

/** Retorna o hex da mistura das três cores pelas porcentagens (total 100%). */
function blendExtrusorColorsHex(
  mix: CmyMix,
  colors: { a: string; b: string; c: string }
): string {
  const total = mix.a + mix.b + mix.c
  if (total <= 0) return "#808080"
  const A = hexToRgb(colors.a)
  const B = hexToRgb(colors.b)
  const C = hexToRgb(colors.c)
  const r = Math.round((A.r * mix.a + B.r * mix.b + C.r * mix.c) / total)
  const g = Math.round((A.g * mix.a + B.g * mix.b + C.g * mix.c) / total)
  const b = Math.round((A.b * mix.a + B.b * mix.b + C.b * mix.c) / total)
  return `#${[r, g, b].map((x) => x.toString(16).padStart(2, "0")).join("")}`
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
  const { exec } = usePrinterCommand()
  const [mix, setMix] = useState<CmyMix>(defaultMix)
  const [suggestColorHex, setSuggestColorHex] = useState("#808080")
  const [extrusorColors, setExtrusorColors] = useState<ExtrusorColors>(defaultExtrusorColors)
  const [notification, setNotification] = useState<{
    message: string
    type: "success" | "error" | "info"
  } | null>(null)
  const [sending, setSending] = useState(false)

  const showNotification = useCallback((message: string, type: "success" | "error" | "info" = "info") => {
    setNotification({ message, type })
    setTimeout(() => setNotification(null), 5000)
  }, [])

  /** Ao alterar um slider, a cor do quadrado "sugerir mistura" passa a ser a prévia da mistura. */
  const updateSlider = useCallback(
    (key: "a" | "b" | "c", value: number) => {
      const next = distributePercentages(mix, key, value)
      setMix(next)
      setSuggestColorHex(blendExtrusorColorsHex(next, extrusorColors))
    },
    [mix, extrusorColors]
  )

  /** Ao alterar a cor de uma extrusora, recalcula as porcentagens para a prévia continuar igual à cor sugerida. */
  const setExtrusorColor = useCallback(
    (key: "a" | "b" | "c", hex: string) => {
      const newColors = { ...extrusorColors, [key]: hex }
      setExtrusorColors(newColors)
      const nextMix = targetHexToMix(suggestColorHex, newColors)
      setMix(nextMix)
    },
    [extrusorColors, suggestColorHex]
  )

  /** Ao escolher uma cor no quadrado, calcula as porcentagens a partir das cores reais das extrusoras. */
  const applySuggestColor = useCallback(
    (hex: string) => {
      setSuggestColorHex(hex)
      const next = targetHexToMix(hex, extrusorColors)
      setMix(next)
    },
    [extrusorColors]
  )

  const sendMixture = useCallback(async () => {
    const sum = mix.a + mix.b + mix.c
    if (sum !== 100) return
    await exec(`Enviando mistura M182…`, async () => {
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
      } catch {
        showNotification("Erro ao enviar mistura", "error")
      } finally {
        setSending(false)
      }
    })
  }, [mix, navigate, showNotification, exec])

  const sum = mix.a + mix.b + mix.c
  const isValid = sum === 100
  const commandPreview = `M182 A${mix.a} B${mix.b} C${mix.c}`

  return {
    mix,
    suggestColorHex,
    extrusorColors,
    setExtrusorColor,
    notification,
    sending,
    isValid,
    commandPreview,
    updateSlider,
    applySuggestColor,
    sendMixture,
  }
}
