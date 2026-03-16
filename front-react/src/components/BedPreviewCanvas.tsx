"use client"

import { useMemo } from "react"
import { Stage, Layer, Rect } from "react-konva"

const PREVIEW_SIZE_PX = 360
const MIN_RECT_PX = 32
const GAP_PX = 4

function rectsOverlap(
  a: { x: number; y: number; w: number; h: number },
  b: { x: number; y: number; w: number; h: number }
): boolean {
  return !(a.x + a.w <= b.x || b.x + b.w <= a.x || a.y + a.h <= b.y || b.y + b.h <= a.y)
}

export interface BedPreviewObject {
  id: number
  name?: string | null
  min_x: number | null
  min_y: number | null
  max_x: number | null
  max_y: number | null
}

export interface BedPreviewBed {
  width_mm: number
  depth_mm: number
}

interface BedPreviewCanvasProps {
  bed: BedPreviewBed
  objects: BedPreviewObject[]
  selectedObjectId: number | null
  onSelectObject: (id: number) => void
  /** Índice do objeto sendo impresso no momento (destacado em outra cor) */
  currentObjectIndex?: number | null
}

/**
 * Preview da mesa com Konva: escala fixa (px por mm) e tamanho mínimo em pixels
 * para os blocos ficarem sempre visíveis e clicáveis.
 * Objeto em impressão é pintado em verde.
 */
export function BedPreviewCanvas({
  bed,
  objects,
  selectedObjectId,
  onSelectObject,
  currentObjectIndex = null,
}: BedPreviewCanvasProps) {
  const scaleX = PREVIEW_SIZE_PX / bed.width_mm
  const scaleY = PREVIEW_SIZE_PX / bed.depth_mm

  const positions = useMemo(() => {
    const out: { x: number; y: number; w: number; h: number }[] = []
    for (const obj of objects) {
      let minX = Math.max(0, Math.min(obj.min_x ?? 0, bed.width_mm))
      let minY = Math.max(0, Math.min(obj.min_y ?? 0, bed.depth_mm))
      let maxX = Math.max(0, Math.min(obj.max_x ?? minX, bed.width_mm))
      let maxY = Math.max(0, Math.min(obj.max_y ?? minY, bed.depth_mm))
      if (maxX <= minX) maxX = minX + 5
      if (maxY <= minY) maxY = minY + 5
      const wMm = maxX - minX
      const hMm = maxY - minY
      let x = minX * scaleX
      let y = (bed.depth_mm - maxY) * scaleY
      let w = Math.max(MIN_RECT_PX, wMm * scaleX)
      let h = Math.max(MIN_RECT_PX, hMm * scaleY)
      if (x < 0) { w += x; x = 0 }
      if (y < 0) { h += y; y = 0 }
      if (x + w > PREVIEW_SIZE_PX) x = PREVIEW_SIZE_PX - w
      if (y + h > PREVIEW_SIZE_PX) y = PREVIEW_SIZE_PX - h

      let rx = x
      let ry = y
      let changed = true
      while (changed) {
        changed = false
        for (let j = 0; j < out.length; j++) {
          if (rectsOverlap(out[j], { x: rx, y: ry, w, h })) {
            const other = out[j]
            const tryY = other.y - h - GAP_PX
            if (tryY >= 0) {
              ry = tryY
            } else {
              rx = other.x + other.w + GAP_PX
              if (rx + w > PREVIEW_SIZE_PX) rx = 0
            }
            changed = true
            break
          }
        }
      }
      rx = Math.max(0, Math.min(rx, PREVIEW_SIZE_PX - w))
      ry = Math.max(0, Math.min(ry, PREVIEW_SIZE_PX - h))
      if (rx + w > PREVIEW_SIZE_PX) rx = PREVIEW_SIZE_PX - w
      if (ry + h > PREVIEW_SIZE_PX) ry = PREVIEW_SIZE_PX - h
      out.push({ x: rx, y: ry, w, h })
    }
    return out
  }, [bed.width_mm, bed.depth_mm, objects, scaleX, scaleY])

  return (
    <div
      className="overflow-hidden rounded border border-border bg-muted"
      style={{ width: PREVIEW_SIZE_PX, height: PREVIEW_SIZE_PX }}
    >
      <Stage width={PREVIEW_SIZE_PX} height={PREVIEW_SIZE_PX}>
        <Layer>
          <Rect
            x={0}
            y={0}
            width={PREVIEW_SIZE_PX}
            height={PREVIEW_SIZE_PX}
            fill="#e5e7eb"
            stroke="#d1d5db"
            strokeWidth={1}
            listening={false}
          />
          {objects.map((obj, i) => {
            const pos = positions[i]
            if (!pos) return null
            const selected = selectedObjectId === obj.id
            // currentObjectIndex é um índice (posição na lista), não o id do objeto
            const isPrinting = currentObjectIndex != null && currentObjectIndex === i
            return (
              <Rect
                key={obj.id}
                x={pos.x}
                y={pos.y}
                width={pos.w}
                height={pos.h}
                fill={
                  selected ? "#2563eb" : isPrinting ? "rgba(34, 197, 94, 0.6)" : "rgba(37, 99, 235, 0.4)"
                }
                stroke={isPrinting && !selected ? "#16a34a" : "#2563eb"}
                strokeWidth={selected ? 2 : isPrinting ? 1.5 : 1}
                listening={true}
                onClick={() => onSelectObject(obj.id)}
                onTap={() => onSelectObject(obj.id)}
              />
            )
          })}
        </Layer>
      </Stage>
    </div>
  )
}
