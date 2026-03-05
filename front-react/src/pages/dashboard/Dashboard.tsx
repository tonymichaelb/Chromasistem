import { Link } from "react-router-dom"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { AppHeader } from "@/components/AppHeader"
import { cn } from "@/lib/utils"
import { useDashboard, type PauseOption } from "./hook"
import { HugeiconsIcon } from "@hugeicons/react"
import {
  File01Icon,
  PlayIcon,
  PauseIcon,
  StopIcon,
  Calendar03Icon,
} from "@hugeicons/core-free-icons"

const PAUSE_OPTIONS: { value: PauseOption; label: string }[] = [
  { value: "keep_temp", label: "Manter temperatura — Bico e mesa permanecem aquecidos (recomendado)" },
  { value: "cold", label: "Pausa fria — Desliga aquecedores após pausar" },
  { value: "filament_change", label: "Troca de filamento — Envia M600 (se a impressora suportar)" },
]

function formatSize(bytes: number) {
  return `${(bytes / 1024).toFixed(1)} KB`
}

/** Formata data/hora para exibição no histórico de falhas */
function formatDateTime(iso: string) {
  try {
    const d = new Date(iso)
    return d.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "medium" })
  } catch {
    return iso
  }
}

export function Dashboard() {
  const {
    status,
    stateLabel,
    recentFiles,
    notification,
    pauseModalOpen,
    setPauseModalOpen,
    pauseOption,
    setPauseOption,
    connectLoading,
    canPause,
    canResume,
    canStop,
    disconnectConfirmOpen,
    setDisconnectConfirmOpen,
    stopConfirmOpen,
    setStopConfirmOpen,
    printConfirm,
    setPrintConfirm,
    connect,
    openDisconnectConfirm,
    confirmDisconnect,
    startPrint,
    openPauseModal,
    closePauseModal,
    confirmPause,
    resume,
    openStopConfirm,
    confirmStop,
    openPrintConfirm,
    confirmPrint,
    isFailure,
    failureResolve,
    failureResolved,
    skipObject,
    failureHistoryOpen,
    setFailureHistoryOpen,
    failureHistoryEntries,
    openFailureHistory,
    bedPreviewOpen,
    setBedPreviewOpen,
    bedPreviewData,
    selectedObjectId,
    setSelectedObjectId,
    openBedPreviewForSkip,
  } = useDashboard()

  return (
    <div className="min-h-screen bg-muted/30">
      <AppHeader />

      <main className="container mx-auto max-w-6xl space-y-6 px-3 py-4 sm:px-4 md:p-6">
        {/* Notificação */}
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

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {/* Status da Impressora */}
          <Card>
            <CardHeader>
              <CardTitle>Status da Impressora</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Estado:</span>
                <Badge
                  variant={
                    status?.state === "printing"
                      ? "default"
                      : status?.state === "paused"
                        ? "secondary"
                        : status?.state === "failure"
                          ? "destructive"
                          : "outline"
                  }
                >
                  {status ? stateLabel : "Carregando…"}
                </Badge>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Conexão:</span>
                <Badge variant={status?.connected ? "default" : "destructive"}>
                  {status ? (status.connected ? "Conectado" : "Desconectado") : "Verificando…"}
                </Badge>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Filamento:</span>
                <Badge
                  variant={
                    status?.filament?.sensor_enabled
                      ? status.filament.has_filament
                        ? "default"
                        : "destructive"
                      : "secondary"
                  }
                >
                  {!status
                    ? "Verificando…"
                    : status.filament?.sensor_enabled
                      ? status.filament.has_filament
                        ? "OK"
                        : "SEM FILAMENTO!"
                      : "Sensor desabilitado"}
                </Badge>
              </div>
              <div className="flex gap-2 pt-2">
                <Button className="flex-1" onClick={connect} disabled={connectLoading}>
                  {connectLoading ? "Conectando…" : "Conectar"}
                </Button>
                <Button variant="secondary" className="flex-1" onClick={openDisconnectConfirm}>
                  Desconectar
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Temperatura */}
          <Card>
            <CardHeader>
              <CardTitle>Temperatura</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-lg border border-border bg-muted/30 p-4">
                <div className="text-xs font-medium text-muted-foreground">Bico</div>
                <div className="text-2xl font-semibold">
                  {status?.temperature?.nozzle ?? "--"}°C
                </div>
                <div className="text-sm text-muted-foreground">
                  Alvo: {status?.temperature?.target_nozzle ?? "--"}°C
                </div>
              </div>
              <div className="rounded-lg border border-border bg-muted/30 p-4">
                <div className="text-xs font-medium text-muted-foreground">Mesa</div>
                <div className="text-2xl font-semibold">
                  {status?.temperature?.bed ?? "--"}°C
                </div>
                <div className="text-sm text-muted-foreground">
                  Alvo: {status?.temperature?.target_bed ?? "--"}°C
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Progresso da Impressão */}
          <Card className="sm:col-span-2 lg:col-span-1">
            <CardHeader>
              <CardTitle>Progresso da Impressão</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="text-sm">
                <span className="text-muted-foreground">Arquivo: </span>
                <strong>{status?.filename || "Nenhum arquivo"}</strong>
              </div>
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">Progresso</span>
                  <span className="font-medium">{(status?.progress ?? 0).toFixed(1)}%</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full bg-primary transition-all duration-300"
                    style={{ width: `${status?.progress ?? 0}%` }}
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-muted-foreground">Decorrido: </span>
                  {status?.time_elapsed ?? "00:00:00"}
                </div>
                <div>
                  <span className="text-muted-foreground">Restante: </span>
                  {status?.time_remaining ?? "00:00:00"}
                </div>
              </div>
              {(status?.skipped_objects_count ?? 0) > 0 && (
                <div className="flex items-center gap-2 text-sm text-amber-600 dark:text-amber-400">
                  <span>Itens pulados nesta impressão: {status?.skipped_objects_count ?? 0}</span>
                  <Button variant="ghost" size="sm" className="h-7 px-2" onClick={openFailureHistory}>
                    <HugeiconsIcon icon={Calendar03Icon} className="size-4" />
                    Histórico
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Falha detectada — ações: Pular item, Resolver, Resolvido, Cancelar */}
          {isFailure && (
            <Card className="sm:col-span-2 border-amber-500/50 bg-amber-500/5">
              <CardHeader>
                <CardTitle className="text-amber-700 dark:text-amber-400">Falha detectada</CardTitle>
                <p className="text-sm text-muted-foreground">
                  {status?.failure_message || "Erro na impressão. Escolha uma ação abaixo."}
                  {status?.failure_code && (
                    <span className="ml-2 text-xs">(código: {status.failure_code})</span>
                  )}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  <strong>Resolver:</strong> clique em &quot;Estou resolvendo&quot; se for mexer na impressora; quando terminar, clique em &quot;Problema resolvido — Retomar&quot; para a impressão continuar.
                </p>
                <Button variant="ghost" size="sm" className="mt-1 h-8 w-fit px-2 text-muted-foreground" onClick={openFailureHistory}>
                  <HugeiconsIcon icon={Calendar03Icon} className="size-4" />
                  Ver histórico de falhas
                </Button>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-2 [&_button]:min-h-10 [&_button]:touch-manipulation">
                <Button variant="secondary" onClick={openBedPreviewForSkip}>
                  Pular item com defeito
                </Button>
                <Button variant="secondary" onClick={failureResolve} title="Registra que você vai mexer na impressora; a impressão só retoma quando você clicar em 'Problema resolvido — Retomar'">
                  Estou resolvendo
                </Button>
                <Button onClick={failureResolved} title="Terminei de resolver; a impressão continua de onde parou">
                  Problema resolvido — Retomar
                </Button>
                <Button variant="destructive" onClick={openStopConfirm}>
                  Cancelar impressão
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Controles */}
          <Card className="sm:col-span-2">
            <CardHeader>
              <CardTitle>Controles de Impressão</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-2 [&_button]:min-h-10 [&_button]:touch-manipulation">
              <Button onClick={startPrint}>
                <HugeiconsIcon icon={PlayIcon} strokeWidth={2} className="size-4" />
                Iniciar
              </Button>
              <Button
                variant="secondary"
                onClick={openPauseModal}
                // disabled={!canPause}
                title={canPause ? "Pausar impressão" : "Disponível apenas durante impressão"}
              >
                <HugeiconsIcon icon={PauseIcon} strokeWidth={2} className="size-4" />
                Pausar
              </Button>
              <Button
                variant="secondary"
                onClick={resume}
                // disabled={!canResume}
                title={canResume ? "Retomar impressão" : "Disponível quando pausado"}
              >
                <HugeiconsIcon icon={PlayIcon} strokeWidth={2} className="size-4" />
                Retomar
              </Button>
              <Button
                variant="destructive"
                onClick={openStopConfirm}
                disabled={!canStop}
              >
                <HugeiconsIcon icon={StopIcon} strokeWidth={2} className="size-4" />
                Parar
              </Button>
            </CardContent>
          </Card>

          {/* Arquivos G-Code Recentes */}
          <Card className="sm:col-span-2 lg:col-span-3">
            <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <CardTitle>Arquivos G-Code Recentes</CardTitle>
              <Link to="/files" className="w-full sm:w-auto">
                <Button variant="secondary" size="sm" className="w-full sm:w-auto">Ver Todos</Button>
              </Link>
            </CardHeader>
            <CardContent>
              {recentFiles.length > 0 ? (
                <ul className="space-y-2">
                  {recentFiles.map((file) => (
                    <li
                      key={file.id}
                      className="flex flex-col gap-3 rounded-lg border border-border bg-muted/30 p-3 sm:flex-row sm:items-center sm:gap-3"
                    >
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded bg-muted">
                        {file.thumbnail ? (
                          <img
                            src={`/static/${file.thumbnail}`}
                            alt=""
                            className="h-full w-full object-cover"
                          />
                        ) : (
                          <HugeiconsIcon icon={File01Icon} strokeWidth={2} className="size-5 text-muted-foreground" />
                        )}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="font-medium truncate">{file.name}</div>
                        <div className="text-xs text-muted-foreground">
                          {formatSize(file.size)} · {file.print_count}x impresso
                        </div>
                      </div>
                      <Button
                        size="sm"
                        onClick={() => openPrintConfirm(file.id, file.name)}
                        className="w-full sm:w-auto min-h-10 touch-manipulation"
                      >
                        <HugeiconsIcon icon={PlayIcon} strokeWidth={2} className="size-4" />
                        Imprimir
                      </Button>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border py-8 text-center">
                  <p className="text-sm text-muted-foreground">Nenhum arquivo G-Code ainda</p>
                  <Link to="/files">
                    <Button>Fazer Upload</Button>
                  </Link>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </main>

      {/* Modal de opções de pausa */}
      <AlertDialog open={pauseModalOpen} onOpenChange={setPauseModalOpen}>
        <AlertDialogContent className="max-w-lg">
          <AlertDialogHeader>
            <AlertDialogTitle>Opções de pausa</AlertDialogTitle>
            <AlertDialogDescription>
              Escolha como a impressão deve pausar:
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="min-w-0 py-2">
            <Select value={pauseOption} onValueChange={(v) => setPauseOption(v as PauseOption)}>
              <SelectTrigger className="w-full min-w-0 [&_[data-slot=select-value]]:min-w-0 [&_[data-slot=select-value]]:truncate">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="min-w-[var(--radix-select-trigger-width)]">
                {PAUSE_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    <span className="block break-words">{opt.label}</span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={closePauseModal}>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={confirmPause} className="bg-amber-600 hover:bg-amber-700">
              Pausar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Confirmação: Desconectar impressora */}
      <AlertDialog open={disconnectConfirmOpen} onOpenChange={setDisconnectConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Desconectar impressora?</AlertDialogTitle>
            <AlertDialogDescription>
              A conexão com a impressora será encerrada.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDisconnect}>Desconectar</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Confirmação: Parar impressão */}
      <AlertDialog open={stopConfirmOpen} onOpenChange={setStopConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Parar impressão?</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja parar a impressão em andamento?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={confirmStop} variant="destructive">
              Parar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Confirmação: Iniciar impressão do arquivo */}
      <AlertDialog open={!!printConfirm} onOpenChange={(open) => !open && setPrintConfirm(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Iniciar impressão</AlertDialogTitle>
            <AlertDialogDescription>
              {printConfirm
                ? `Iniciar impressão de "${printConfirm.fileName}"?`
                : ""}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={confirmPrint}>Imprimir</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Histórico de falhas */}
      <AlertDialog open={failureHistoryOpen} onOpenChange={setFailureHistoryOpen}>
        <AlertDialogContent className="max-h-[85vh] max-w-lg flex flex-col">
          <AlertDialogHeader>
            <AlertDialogTitle>Histórico de falhas</AlertDialogTitle>
            <AlertDialogDescription>
              Últimas falhas e ações (skip, resolvido, cancelado).
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="min-h-0 overflow-y-auto rounded-md border border-border bg-muted/30 p-2">
            {failureHistoryEntries.length === 0 ? (
              <p className="py-4 text-center text-sm text-muted-foreground">Nenhum registro ainda.</p>
            ) : (
              <ul className="space-y-2">
                {failureHistoryEntries.map((entry) => (
                  <li
                    key={entry.id}
                    className="rounded border border-border bg-background p-3 text-sm"
                  >
                    <div className="flex justify-between gap-2">
                      <Badge variant={entry.action === "skipped" ? "secondary" : "outline"}>
                        {entry.action}
                      </Badge>
                      <span className="text-muted-foreground">{formatDateTime(entry.occurred_at)}</span>
                    </div>
                    {(entry.failure_message || entry.failure_code) && (
                      <p className="mt-1 text-muted-foreground">
                        {entry.failure_message}
                        {entry.failure_code && ` (${entry.failure_code})`}
                      </p>
                    )}
                    {entry.object_index_or_name != null && (
                      <p className="mt-0.5 text-xs text-muted-foreground">Objeto: {entry.object_index_or_name}</p>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel>Fechar</AlertDialogCancel>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Escolher peça a pular — visualização da mesa */}
      <AlertDialog open={bedPreviewOpen} onOpenChange={(open) => !open && setBedPreviewOpen(false)}>
        <AlertDialogContent className="max-w-lg">
          <AlertDialogHeader>
            <AlertDialogTitle>Pular item com defeito</AlertDialogTitle>
            <AlertDialogDescription>
              {bedPreviewData && bedPreviewData.objects.length > 0
                ? "Clique em uma peça na mesa para selecioná-la e depois em \"Pular este objeto\"."
                : "O arquivo não possui marcadores de objeto. Use \"Pular item atual\" para avançar até a próxima camada/objeto."}
            </AlertDialogDescription>
          </AlertDialogHeader>
          {bedPreviewData && (
            <>
              <div className="rounded-lg border border-border bg-muted/30 p-4">
                <div
                  className="relative mx-auto overflow-hidden rounded bg-muted"
                  style={{
                    width: "100%",
                    maxWidth: 280,
                    aspectRatio: `${bedPreviewData.bed.width_mm}/${bedPreviewData.bed.depth_mm}`,
                  }}
                >
                  <svg
                    viewBox={`0 0 ${bedPreviewData.bed.width_mm} ${bedPreviewData.bed.depth_mm}`}
                    className="h-full w-full"
                    preserveAspectRatio="xMidYMid meet"
                  >
                    <rect
                      width={bedPreviewData.bed.width_mm}
                      height={bedPreviewData.bed.depth_mm}
                      fill="var(--muted)"
                      stroke="var(--border)"
                      strokeWidth={0.5}
                    />
                    {bedPreviewData.objects.map((obj) => {
                      const minX = obj.min_x ?? 0
                      const minY = obj.min_y ?? 0
                      const maxX = obj.max_x ?? minX
                      const maxY = obj.max_y ?? minY
                      const w = maxX - minX || 1
                      const h = maxY - minY || 1
                      const depthMm = bedPreviewData.bed.depth_mm
                      const svgY = depthMm - maxY
                      const selected = selectedObjectId === obj.id
                      return (
                        <rect
                          key={obj.id}
                          x={minX}
                          y={svgY}
                          width={w}
                          height={h}
                          fill={selected ? "var(--primary)" : "var(--primary / 0.3)"}
                          stroke="var(--primary)"
                          strokeWidth={selected ? 1.5 : 0.5}
                          className="cursor-pointer"
                          onClick={() => setSelectedObjectId(obj.id)}
                          role="button"
                          aria-label={obj.name ?? `Objeto ${obj.id + 1}`}
                        />
                      )
                    })}
                  </svg>
                </div>
                {selectedObjectId != null && bedPreviewData.objects.some((o) => o.id === selectedObjectId) && (
                  <p className="mt-2 text-center text-sm text-muted-foreground">
                    Objeto selecionado: {bedPreviewData.objects.find((o) => o.id === selectedObjectId)?.name ?? `#${selectedObjectId + 1}`}
                  </p>
                )}
              </div>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancelar</AlertDialogCancel>
                {bedPreviewData.objects.length > 0 ? (
                  <AlertDialogAction
                    onClick={() => skipObject(selectedObjectId ?? undefined)}
                    disabled={selectedObjectId == null}
                    className="bg-amber-600 hover:bg-amber-700"
                  >
                    Pular este objeto
                  </AlertDialogAction>
                ) : (
                  <AlertDialogAction onClick={() => skipObject()} className="bg-amber-600 hover:bg-amber-700">
                    Pular item atual
                  </AlertDialogAction>
                )}
              </AlertDialogFooter>
            </>
          )}
          {!bedPreviewData && (
            <>
              <p className="text-sm text-muted-foreground">Carregando visualização da mesa…</p>
              <AlertDialogFooter>
                <AlertDialogCancel>Fechar</AlertDialogCancel>
              </AlertDialogFooter>
            </>
          )}
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
