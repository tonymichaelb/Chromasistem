import { useState, useRef, useCallback } from "react"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { AppHeader } from "@/components/AppHeader"
import { cn } from "@/lib/utils"
import { useFatiador, type QualityPreset } from "./hook"
import { HugeiconsIcon } from "@hugeicons/react"
import { File01Icon, PlayIcon, Copy01Icon } from "@hugeicons/core-free-icons"

const ACCEPT_3D = ".stl,.obj"
const QUALITY_OPTIONS: { value: QualityPreset; label: string }[] = [
  { value: "draft", label: "Rápido (0,28 mm)" },
  { value: "normal", label: "Normal (0,20 mm)" },
  { value: "fine", label: "Fininho (0,12 mm)" },
]

export function Fatiador() {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [quality, setQuality] = useState<QualityPreset>("normal")
  const [infill, setInfill] = useState(20)

  const {
    slicing,
    result,
    notification,
    slice,
    sendToPrint,
    goToFiles,
    resetResult,
  } = useFatiador()

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      if (result) resetResult()
    }
    e.target.value = ""
  }, [result, resetResult])

  const openFileDialog = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const handleSlice = useCallback(() => {
    if (!selectedFile) return
    slice(selectedFile, quality, infill)
  }, [selectedFile, quality, infill, slice])

  const handleSendToPrint = useCallback(() => {
    if (result) sendToPrint(result.file_id)
  }, [result, sendToPrint])

  return (
    <div className="min-h-screen bg-muted/30">
      <AppHeader />
      <main className="container mx-auto max-w-2xl space-y-6 px-3 py-4 sm:px-4 md:p-6">
        <div>
          <h1 className="text-xl font-semibold sm:text-2xl">Fatiador integrado</h1>
          <p className="text-sm text-muted-foreground sm:text-base">
            Envie um modelo 3D (.stl ou .obj) para gerar o G-code e enviar para impressão
          </p>
        </div>

        {notification && (
          <div
            role="alert"
            className={cn(
              "rounded-lg px-4 py-3 text-sm",
              notification.type === "success" && "bg-primary/10 text-primary",
              notification.type === "error" && "bg-destructive/10 text-destructive",
              notification.type === "info" && "bg-muted text-muted-foreground"
            )}
          >
            {notification.message}
          </div>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <HugeiconsIcon icon={File01Icon} strokeWidth={2} className="size-5" />
              Enviar modelo 3D
            </CardTitle>
            <CardDescription>
              Selecione um arquivo .stl ou .obj e as opções de fatiamento. O servidor usará o OrcaSlicer para gerar o G-code.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <input
              ref={fileInputRef}
              type="file"
              accept={ACCEPT_3D}
              className="hidden"
              onChange={handleFileSelect}
            />
            <div className="space-y-2">
              <label className="block text-sm font-medium">Arquivo 3D</label>
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                <Input
                  readOnly
                  value={selectedFile ? selectedFile.name : ""}
                  placeholder="Nenhum arquivo selecionado"
                  className="bg-muted/50"
                />
                <Button type="button" variant="secondary" onClick={openFileDialog}>
                  <HugeiconsIcon icon={File01Icon} strokeWidth={2} className="size-4" />
                  Selecionar arquivo
                </Button>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <label className="block text-sm font-medium">Qualidade (altura de camada)</label>
                <select
                  value={quality}
                  onChange={(e) => setQuality(e.target.value as QualityPreset)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  {QUALITY_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <label className="block text-sm font-medium">Preenchimento (%)</label>
                <Input
                  type="number"
                  min={5}
                  max={100}
                  value={infill}
                  onChange={(e) => setInfill(Number(e.target.value) || 20)}
                />
              </div>
            </div>

            <Button
              onClick={handleSlice}
              disabled={!selectedFile || slicing}
              className="w-full sm:w-auto"
            >
              {slicing ? "Fatiando…" : "Fatiar"}
            </Button>
          </CardContent>
        </Card>

        {result && (
          <Card className="border-primary/30 bg-primary/5">
            <CardHeader>
              <CardTitle>G-code gerado</CardTitle>
              <CardDescription>
                Arquivo: {result.filename}. Você pode enviar para impressão ou ver na lista de arquivos.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-2">
              <Button onClick={handleSendToPrint}>
                <HugeiconsIcon icon={PlayIcon} strokeWidth={2} className="size-4" />
                Enviar para impressão
              </Button>
              <Button variant="secondary" onClick={goToFiles}>
                <HugeiconsIcon icon={Copy01Icon} strokeWidth={2} className="size-4" />
                Ver em Arquivos
              </Button>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  )
}
