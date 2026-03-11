import { Link } from "react-router-dom";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { AppHeader } from "@/components/AppHeader";
import { PrintFlowAdvance } from "@/components/PrintFlowAdvance";
import { cn } from "@/lib/utils";
import { useRevisao } from "./hook";
import { HugeiconsIcon } from "@hugeicons/react";
import {
  File01Icon,
  PlayIcon,
  Calendar03Icon,
  SettingsIcon,
} from "@hugeicons/core-free-icons";

function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${Math.round((bytes / Math.pow(k, i)) * 100) / 100} ${sizes[i]}`;
}

export function Revisao() {
  const {
    selectedFile,
    notification,
    printConfirmOpen,
    setPrintConfirmOpen,
    openPrintConfirm,
    closePrintConfirm,
    confirmPrint,
    waitingForPrintStart,
  } = useRevisao();

  return (
    <div className="min-h-screen bg-muted/30">
      <AppHeader />

      <main className="container mx-auto max-w-4xl space-y-6 px-3 py-4 sm:px-4 md:p-6">
        <div>
          <h1 className="text-xl font-semibold sm:text-2xl">Revisão</h1>
          <p className="text-sm text-muted-foreground sm:text-base">
            Confira o arquivo e as configurações antes de iniciar a impressão
          </p>
        </div>

        {notification && (
          <div
            role="alert"
            className={cn(
              "rounded-lg px-4 py-3 text-sm",
              notification.type === "success" && "bg-primary/10 text-primary",
              notification.type === "error" &&
                "bg-destructive/10 text-destructive",
              notification.type === "info" && "bg-muted text-muted-foreground",
            )}
          >
            {notification.message}
          </div>
        )}

        {!selectedFile ? (
          <Card className="overflow-hidden border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-16 text-center">
              <div className="mb-4 flex h-20 w-20 items-center justify-center rounded-2xl bg-muted">
                <HugeiconsIcon
                  icon={File01Icon}
                  className="size-10 text-muted-foreground"
                  strokeWidth={1.5}
                />
              </div>
              <h2 className="text-lg font-semibold">
                Nenhum arquivo selecionado
              </h2>
              <p className="mt-2 max-w-sm text-sm text-muted-foreground">
                Selecione um arquivo G-Code na página Arquivos para revisar e
                iniciar a impressão.
              </p>
              <Button asChild className="mt-6">
                <Link to="/files">Ir para Arquivos</Link>
              </Button>
            </CardContent>
          </Card>
        ) : (
          <>
            <Card className="overflow-hidden">
              <div className="grid gap-0 md:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]">
                {/* Preview do arquivo */}
                <div className="relative flex min-h-[240px] items-center justify-center bg-muted/50 p-6 md:min-h-[320px]">
                  <div className="relative w-full max-w-sm overflow-hidden rounded-xl border border-border bg-background shadow-sm aspect-square max-h-[280px] md:max-h-[320px]">
                    {selectedFile.thumbnail ? (
                      <img
                        src={`/static/${selectedFile.thumbnail}`}
                        alt=""
                        className="h-full w-full object-contain"
                      />
                    ) : (
                      <div className="flex h-full w-full items-center justify-center">
                        <HugeiconsIcon
                          icon={File01Icon}
                          className="size-16 text-muted-foreground"
                          strokeWidth={1.5}
                        />
                      </div>
                    )}
                  </div>
                </div>

                {/* Detalhes e ação */}
                <div className="flex flex-col p-6">
                  <CardHeader className="p-0 pb-4">
                    <CardTitle className="line-clamp-2 text-lg">
                      {selectedFile.name}
                    </CardTitle>
                    <CardDescription>
                      Arquivo selecionado para impressão ·{" "}
                      {selectedFile.print_count}x impresso anteriormente
                    </CardDescription>
                  </CardHeader>

                  <ul className="space-y-3 text-sm">
                    <li className="flex items-center gap-3">
                      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
                        <HugeiconsIcon
                          icon={File01Icon}
                          className="size-4 text-muted-foreground"
                        />
                      </span>
                      <div>
                        <span className="text-muted-foreground">Tamanho</span>
                        <p className="font-medium">
                          {formatFileSize(selectedFile.size)}
                        </p>
                      </div>
                    </li>
                    {selectedFile.print_time && (
                      <li className="flex items-center gap-3">
                        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
                          <HugeiconsIcon
                            icon={Calendar03Icon}
                            className="size-4 text-muted-foreground"
                          />
                        </span>
                        <div>
                          <span className="text-muted-foreground">
                            Tempo estimado
                          </span>
                          <p className="font-medium">
                            {selectedFile.print_time}
                          </p>
                        </div>
                      </li>
                    )}
                    {(selectedFile.nozzle_temp != null ||
                      selectedFile.bed_temp != null) && (
                      <li className="flex items-center gap-3">
                        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
                          <HugeiconsIcon
                            icon={SettingsIcon}
                            className="size-4 text-muted-foreground"
                          />
                        </span>
                        <div>
                          <span className="text-muted-foreground">
                            Temperaturas
                          </span>
                          <p className="font-medium">
                            {selectedFile.nozzle_temp != null &&
                              `Bico: ${selectedFile.nozzle_temp}°C`}
                            {selectedFile.nozzle_temp != null &&
                              selectedFile.bed_temp != null &&
                              " · "}
                            {selectedFile.bed_temp != null &&
                              `Mesa: ${selectedFile.bed_temp}°C`}
                          </p>
                        </div>
                      </li>
                    )}
                    {(selectedFile.layer_height != null ||
                      selectedFile.infill != null) && (
                      <li className="flex items-center gap-3">
                        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
                          <span className="text-xs font-medium text-muted-foreground">
                            📏
                          </span>
                        </span>
                        <div>
                          <span className="text-muted-foreground">
                            Impressão
                          </span>
                          <p className="font-medium">
                            {selectedFile.layer_height != null &&
                              `Camada: ${selectedFile.layer_height}mm`}
                            {selectedFile.layer_height != null &&
                              selectedFile.infill != null &&
                              " · "}
                            {selectedFile.infill != null &&
                              `Infill: ${selectedFile.infill}%`}
                          </p>
                        </div>
                      </li>
                    )}
                    {(selectedFile.filament_used != null ||
                      selectedFile.filament_type) && (
                      <li className="flex items-center gap-3">
                        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
                          <span className="text-xs font-medium text-muted-foreground">
                            🧵
                          </span>
                        </span>
                        <div>
                          <span className="text-muted-foreground">
                            Filamento
                          </span>
                          <p className="font-medium">
                            {selectedFile.filament_used != null &&
                              `${selectedFile.filament_used}g`}
                            {selectedFile.filament_used != null &&
                              selectedFile.filament_type &&
                              " · "}
                            {selectedFile.filament_type ?? ""}
                          </p>
                        </div>
                      </li>
                    )}
                  </ul>

                  <div className="mt-auto flex flex-col gap-3 pt-6">
                    <Button
                      size="lg"
                      className="w-full sm:w-auto sm:min-w-[200px]"
                      onClick={openPrintConfirm}
                    >
                      <HugeiconsIcon
                        icon={PlayIcon}
                        strokeWidth={2}
                        className="size-5"
                      />
                      Iniciar impressão
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      asChild
                      className="w-fit text-muted-foreground"
                    >
                      <Link to="/files">Trocar arquivo</Link>
                    </Button>
                  </div>
                </div>
              </div>
            </Card>

            <PrintFlowAdvance />
          </>
        )}
      </main>

      <AlertDialog open={printConfirmOpen} onOpenChange={setPrintConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Iniciar impressão</AlertDialogTitle>
            <AlertDialogDescription>
              {selectedFile
                ? `Iniciar impressão de "${selectedFile.name}"? A impressora deve estar conectada.`
                : ""}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={closePrintConfirm}>
              Cancelar
            </AlertDialogCancel>
            <AlertDialogAction onClick={confirmPrint}>
              Iniciar impressão
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Overlay bloqueante: aguardar impressora iniciar (homing etc.) antes de ir ao Monitor */}
      {waitingForPrintStart && (
        <div className="fixed inset-0 z-[9999] flex flex-col items-center justify-center gap-4 bg-black/60 backdrop-blur-sm">
          <div className="mx-4 flex w-full max-w-sm flex-col items-center gap-4 rounded-2xl border border-border bg-background p-8 shadow-2xl">
            <div className="relative flex h-12 w-12 items-center justify-center">
              <div className="absolute inset-0 animate-spin rounded-full border-4 border-muted border-t-primary" />
            </div>
            <p className="text-center text-sm font-medium text-foreground">
              Aguarde, iniciando impressão…
            </p>
            <p className="text-center text-xs text-muted-foreground">
              Não clique em nada. Você será levado ao Monitor quando a impressora começar a executar.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
