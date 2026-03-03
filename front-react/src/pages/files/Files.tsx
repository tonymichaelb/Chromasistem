import { useState } from "react"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { AppHeader } from "@/components/AppHeader"
import { cn } from "@/lib/utils"
import { useFiles, type GcodeFileItem } from "./hook"
import { HugeiconsIcon } from "@hugeicons/react"
import {
  File01Icon,
  PlayIcon,
  Delete02Icon,
  Download01Icon,
  RefreshIcon,
  Copy01Icon,
} from "@hugeicons/core-free-icons"

const ACCEPT_FILES = ".gcode,.gco,.g"
const MAX_SIZE_MB = 100

function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 Bytes"
  const k = 1024
  const sizes = ["Bytes", "KB", "MB", "GB"]
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${Math.round((bytes / Math.pow(k, i)) * 100) / 100} ${sizes[i]}`
}

function formatDate(iso: string | null): string {
  if (!iso) return "Nunca"
  return new Date(iso).toLocaleString("pt-BR")
}

function FileCard({
  file,
  onPrint,
  onDownload,
  onDelete,
}: {
  file: GcodeFileItem
  onPrint: () => void
  onDownload: () => void
  onDelete: () => void
}) {
  const meta: string[] = []
  if (file.print_time) meta.push(`⏱️ ${file.print_time}`)
  if (file.filament_used != null) {
    meta.push(`🧵 ${file.filament_used}g${file.filament_type ? ` (${file.filament_type})` : ""}`)
  } else if (file.filament_type) meta.push(`🧵 ${file.filament_type}`)
  if (file.layer_height != null) meta.push(`📏 ${file.layer_height}mm`)
  if (file.infill != null) meta.push(`🔲 ${file.infill}%`)
  if (file.nozzle_temp != null) meta.push(`🌡️ Bico: ${file.nozzle_temp}°C`)
  if (file.bed_temp != null) meta.push(`🌡️ Mesa: ${file.bed_temp}°C`)

  return (
    <Card size="sm" className="flex flex-col gap-4 p-4 sm:flex-row sm:items-start">
      <div className="relative flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-lg bg-muted">
        {file.thumbnail ? (
          <>
            <img
              src={`/static/${file.thumbnail}`}
              alt=""
              className="h-full w-full object-cover"
              onError={(e) => {
                e.currentTarget.style.display = "none"
                const next = e.currentTarget.nextElementSibling as HTMLElement
                if (next) next.classList.remove("hidden")
              }}
            />
            <div className="hidden size-full items-center justify-center">
              <HugeiconsIcon icon={File01Icon} strokeWidth={2} className="size-8 text-muted-foreground" />
            </div>
          </>
        ) : (
          <HugeiconsIcon icon={File01Icon} strokeWidth={2} className="size-8 text-muted-foreground" />
        )}
      </div>
      <div className="min-w-0 flex-1 space-y-1">
        <h3 className="truncate font-medium">{file.name}</h3>
        {meta.length > 0 && (
          <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-muted-foreground">
            {meta.map((m, i) => (
              <span key={i}>{m}</span>
            ))}
          </div>
        )}
        <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-muted-foreground">
          <span>📦 {formatFileSize(file.size)}</span>
          <span>📅 {formatDate(file.uploaded)}</span>
          <span>🖨️ {file.print_count}x impresso</span>
        </div>
        <div className="text-xs text-muted-foreground">
          Última impressão: {formatDate(file.last_printed)}
        </div>
      </div>
      <div className="flex shrink-0 flex-row flex-wrap gap-2 sm:flex-col sm:gap-1 [&_button]:min-h-10 [&_button]:touch-manipulation [&_button]:flex-1 sm:[&_button]:flex-none">
        <Button size="sm" onClick={onPrint}>
          <HugeiconsIcon icon={PlayIcon} strokeWidth={2} className="size-4" />
          Imprimir
        </Button>
        <Button size="sm" variant="secondary" onClick={onDownload}>
          <HugeiconsIcon icon={Download01Icon} strokeWidth={2} className="size-4" />
          Baixar
        </Button>
        <Button size="sm" variant="destructive" onClick={onDelete}>
          <HugeiconsIcon icon={Delete02Icon} strokeWidth={2} className="size-4" />
          Excluir
        </Button>
      </div>
    </Card>
  )
}

export function Files() {
  const {
    files,
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
  } = useFiles()

  const [dragOver, setDragOver] = useState(false)

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) uploadFile(file)
  }

  return (
    <div className="min-h-screen bg-muted/30">
      <AppHeader />
      <main className="container mx-auto max-w-5xl space-y-6 px-3 py-4 sm:px-4 md:p-6">
        <div>
          <h1 className="text-xl font-semibold sm:text-2xl">Gerenciador de Arquivos G-Code</h1>
          <p className="text-sm text-muted-foreground sm:text-base">Faça upload, gerencie e imprima seus arquivos G-Code</p>
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

        {/* Upload */}
        <Card>
          <CardHeader>
            <CardTitle>Enviar Arquivo G-Code</CardTitle>
          </CardHeader>
          <CardContent>
            <input
              ref={fileInputRef}
              type="file"
              accept={ACCEPT_FILES}
              className="hidden"
              onChange={handleFileSelect}
            />
            <div
              onDragOver={(e) => {
                e.preventDefault()
                setDragOver(true)
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              className={cn(
                "flex flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed py-10 transition-colors",
                dragOver ? "border-primary bg-primary/5" : "border-border bg-muted/30"
              )}
            >
              {uploading ? (
                <p className="text-muted-foreground">Enviando arquivo...</p>
              ) : (
                <>
                  <HugeiconsIcon icon={File01Icon} strokeWidth={2} className="size-12 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">Arraste e solte seu arquivo G-Code aqui</p>
                  <p className="text-sm text-muted-foreground">ou</p>
                  <Button onClick={openFileDialog}>Selecionar Arquivo</Button>
                  <p className="text-xs text-muted-foreground">
                    Formatos aceitos: .gcode, .gco, .g (máx. {MAX_SIZE_MB}MB)
                  </p>
                </>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Lista de arquivos */}
        <Card>
          <CardHeader className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
            <CardTitle>Meus Arquivos G-Code</CardTitle>
            <div className="flex w-full flex-wrap items-center gap-2 sm:w-auto">
              <Input
                placeholder="Buscar arquivo..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="min-w-0 flex-1 sm:w-48 sm:flex-none"
              />
              <Button variant="secondary" size="sm" onClick={loadFiles} disabled={loading}>
                <HugeiconsIcon icon={RefreshIcon} strokeWidth={2} className="size-4" />
                Atualizar
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="py-8 text-center text-muted-foreground">Carregando arquivos...</p>
            ) : files.length === 0 ? (
              <p className="py-8 text-center text-muted-foreground">
                Nenhum arquivo encontrado. Faça upload do seu primeiro G-Code!
              </p>
            ) : (
              <div className="space-y-3">
                {files.map((file) => (
                  <FileCard
                    key={file.id}
                    file={file}
                    onPrint={() => openPrintConfirm(file.id, file.name)}
                    onDownload={() => downloadFile(file.id)}
                    onDelete={() => openDeleteConfirm(file.id)}
                  />
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Integração OrcaSlicer */}
        <Card>
          <CardHeader>
            <CardTitle>Integração com OrcaSlicer</CardTitle>
            <CardDescription>
              Configure o OrcaSlicer para enviar arquivos diretamente para o Croma:
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:gap-4">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-medium text-primary-foreground">
                1
              </div>
              <div className="min-w-0">
                <h3 className="font-medium">Abra as Configurações do OrcaSlicer</h3>
                <p className="text-sm text-muted-foreground">Vá em Preferences → Network</p>
              </div>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row sm:gap-4">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-medium text-primary-foreground">
                2
              </div>
              <div className="min-w-0 flex-1">
                <h3 className="font-medium">Configure o Servidor</h3>
                <div className="mt-2 flex flex-col gap-2 rounded-lg border border-border bg-muted/30 px-3 py-2 sm:flex-row sm:flex-wrap sm:items-center">
                  <span className="text-sm text-muted-foreground shrink-0">URL do Servidor:</span>
                  <code className="min-w-0 truncate text-sm">{`${typeof window !== "undefined" ? window.location.origin : ""}/api/files/upload`}</code>
                  <Button variant="secondary" size="sm" onClick={copyUploadUrl} className="shrink-0">
                    <HugeiconsIcon icon={Copy01Icon} strokeWidth={2} className="size-4" />
                    Copiar
                  </Button>
                </div>
              </div>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row sm:gap-4">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-medium text-primary-foreground">
                3
              </div>
              <div className="min-w-0">
                <h3 className="font-medium">Token de Autenticação (em breve)</h3>
                <p className="text-sm text-muted-foreground">Por enquanto, faça login no navegador antes de enviar</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </main>

      {/* Confirmação excluir */}
      <AlertDialog open={deleteConfirmOpen} onOpenChange={setDeleteConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Confirmar exclusão</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja excluir este arquivo?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={closeDeleteConfirm}>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDelete} variant="destructive">
              Excluir
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Confirmação imprimir */}
      <AlertDialog open={!!printConfirm} onOpenChange={(open) => !open && setPrintConfirm(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Iniciar impressão</AlertDialogTitle>
            <AlertDialogDescription>
              {printConfirm ? `Iniciar impressão de "${printConfirm.fileName}"?` : ""}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={confirmPrint}>Imprimir</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
