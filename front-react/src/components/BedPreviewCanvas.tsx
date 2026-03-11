"use client"

import { Stage, Layer, Rect } from "react-konva"

const PREVIEW_SIZE_PX = 360
const MIN_RECT_PX = 32

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

  return (
    <div
      className="overflow-hidden rounded border border-border bg-muted"
      style={{ width: PREVIEW_SIZE_PX, height: PREVIEW_SIZE_PX }}
    >
      <Stage width={PREVIEW_SIZE_PX} height={PREVIEW_SIZE_PX}>
        <Layer>
          {/* Mesa (fundo) em pixels */}
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
          {/* Objetos: mm → px; Y invertido (fundo da mesa = topo do canvas) */}
          {objects.map((obj) => {
            const minX = Math.max(0, Math.min(obj.min_x ?? 0, bed.width_mm))
            const minY = Math.max(0, Math.min(obj.min_y ?? 0, bed.depth_mm))
            const maxX = Math.max(0, Math.min(obj.max_x ?? minX, bed.width_mm))
            const maxY = Math.max(0, Math.min(obj.max_y ?? minY, bed.depth_mm))
            const wMm = Math.max(0.1, maxX - minX)
            const hMm = Math.max(0.1, maxY - minY)
            const x = minX * scaleX
            const y = (bed.depth_mm - maxY) * scaleY
            const wPx = wMm * scaleX
            const hPx = hMm * scaleY
            const w = Math.max(MIN_RECT_PX, wPx)
            const h = Math.max(MIN_RECT_PX, hPx)
            const selected = selectedObjectId === obj.id
            const isPrinting = currentObjectIndex != null && currentObjectIndex === obj.id

            return (
              <Rect
                key={obj.id}
                x={x}
                y={y}
                width={w}
                height={h}
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
