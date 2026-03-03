import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
import { cn } from "@/lib/utils";
import { useWifi, type ScannedNetwork, type UseWifiReturn } from "./hook";
import { HugeiconsIcon } from "@hugeicons/react";
import {
  RefreshIcon,
  LockIcon,
  Delete02Icon,
} from "@hugeicons/core-free-icons";

function SignalIcon() {
  return (
    <span className="text-2xl" aria-hidden>
      📶
    </span>
  );
}

export function Wifi() {
  const wifi = useWifi() as UseWifiReturn;
  const {
    status,
    savedNetworks,
    availableNetworks,
    loadingStatus,
    loadingSaved,
    scanning,
    notification,
    connectModalOpen,
    setConnectModalOpen,
    connectSSID,
    connectPassword,
    setConnectPassword,
    showConnectPassword,
    setShowConnectPassword,
    connectLoading,
    openConnectModal,
    closeConnectModal,
    connectToNetwork,
    forgetConfirmOpen,
    setForgetConfirmOpen,
    networkToForget,
    openForgetConfirm,
    closeForgetConfirm,
    forgetNetwork,
    scanNetworks,
    currentSSID,
  } = wifi;

  return (
    <div className="min-h-screen bg-muted/30">
      <AppHeader />
      <main className="container mx-auto max-w-2xl space-y-6 px-3 py-4 sm:px-4 md:p-6">
        <div>
          <h1 className="text-xl font-semibold sm:text-2xl">
            Configuração Wi-Fi
          </h1>
          <p className="text-muted-foreground">
            Gerencie conexões Wi-Fi e configure redes
          </p>
        </div>

        {/* Status da conexão atual */}
        <Card
          className={cn(
            "text-center text-primary-foreground",
            status?.connected
              ? status.is_hotspot
                ? "border-amber-500/50 bg-linear-to-br from-amber-600 to-amber-700"
                : "border-primary/50 bg-linear-to-br from-green-600 to-green-700"
              : "border-border bg-muted",
          )}
        >
          <CardContent className="pt-6">
            <h3 className="mb-2 text-sm font-medium opacity-90">
              Status da conexão
            </h3>
            {loadingStatus ? (
              <p
                className={
                  status ? "text-primary-foreground" : "text-muted-foreground"
                }
              >
                Carregando…
              </p>
            ) : status?.connected ? (
              <>
                <p className="text-lg font-semibold sm:text-xl">
                  {status.ssid}
                  {status.is_hotspot && (
                    <span className="ml-2 inline-block rounded-full bg-amber-400/90 px-2 py-0.5 text-xs font-bold text-amber-950">
                      HOTSPOT ATIVO
                    </span>
                  )}
                </p>
                <p className="mt-1 text-sm opacity-90">
                  IP: {status.ip ?? "N/A"}
                </p>
              </>
            ) : (
              <p
                className={cn(
                  "font-medium",
                  status ? "text-destructive" : "text-muted-foreground",
                )}
              >
                Desconectado
              </p>
            )}
          </CardContent>
        </Card>

        {/* Redes salvas */}
        <Card>
          <CardHeader>
            <CardTitle>Redes salvas</CardTitle>
          </CardHeader>
          <CardContent>
            {loadingSaved ? (
              <p className="py-4 text-center text-sm text-muted-foreground">
                Carregando…
              </p>
            ) : savedNetworks.length === 0 ? (
              <p className="py-4 text-center text-sm text-muted-foreground">
                Nenhuma rede salva
              </p>
            ) : (
              <ul className="space-y-2">
                {savedNetworks.map((ssid: string) => {
                  const isConnected = ssid === currentSSID;
                  return (
                    <li
                      key={ssid}
                      className={cn(
                        "flex flex-col gap-2 rounded-lg border p-4 sm:flex-row sm:items-center sm:justify-between",
                        isConnected
                          ? "border-primary/50 bg-primary/10"
                          : "border-border bg-card",
                      )}
                    >
                      <div className="min-w-0 flex-1">
                        <p className="font-medium">
                          {ssid}
                          {isConnected && (
                            <span className="ml-1 text-primary" aria-hidden>
                              ✓
                            </span>
                          )}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Rede salva
                        </p>
                      </div>
                      {!isConnected && (
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => openForgetConfirm(ssid)}
                          className="shrink-0"
                        >
                          <HugeiconsIcon
                            icon={Delete02Icon}
                            className="size-4"
                          />
                          Esquecer
                        </Button>
                      )}
                    </li>
                  );
                })}
              </ul>
            )}
          </CardContent>
        </Card>

        {/* Redes disponíveis */}
        <Card>
          <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <CardTitle>Redes disponíveis</CardTitle>
            <Button
              onClick={scanNetworks}
              disabled={scanning}
              className="w-full sm:w-auto"
            >
              <HugeiconsIcon icon={RefreshIcon} className="size-4" />
              {scanning ? "Escaneando" : "Atualizar"}
            </Button>
          </CardHeader>
          <CardContent>
            {availableNetworks === null ? (
              <p className="py-6 text-center text-sm text-muted-foreground">
                Clique em &quot;Atualizar&quot; para escanear redes
              </p>
            ) : scanning ? (
              <p className="py-6 text-center text-sm text-muted-foreground">
                Escaneando redes…
              </p>
            ) : availableNetworks.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">
                Nenhuma rede encontrada
              </p>
            ) : (
              <ul className="space-y-2">
                {availableNetworks.map((net: ScannedNetwork) => {
                  const isConnected = net.ssid === currentSSID;
                  return (
                    <li
                      key={`${net.ssid}-${net.signal}`}
                      className={cn(
                        "flex flex-col gap-2 rounded-lg border p-4 sm:flex-row sm:items-center sm:gap-4",
                        isConnected
                          ? "border-primary/50 bg-primary/10"
                          : "border-border bg-card",
                      )}
                    >
                      <div className="flex shrink-0">
                        <SignalIcon />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="font-medium">
                          {net.security !== "Aberta" && (
                            <HugeiconsIcon
                              icon={LockIcon}
                              className="mr-1 inline size-4"
                              aria-hidden
                            />
                          )}
                          {net.ssid}
                          {isConnected && (
                            <span className="ml-1 text-primary" aria-hidden>
                              ✓
                            </span>
                          )}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Sinal: {net.signal}% | {net.security}
                        </p>
                      </div>
                      {!isConnected && (
                        <Button
                          size="sm"
                          onClick={() => openConnectModal(net.ssid)}
                          className="shrink-0"
                        >
                          Conectar
                        </Button>
                      )}
                    </li>
                  );
                })}
              </ul>
            )}
          </CardContent>
        </Card>

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
      </main>

      {/* Modal Conectar */}
      <AlertDialog open={connectModalOpen} onOpenChange={setConnectModalOpen}>
        <AlertDialogContent className="max-w-sm">
          <form id="wifi-connect-form" onSubmit={connectToNetwork}>
            <AlertDialogHeader>
              <AlertDialogTitle>Conectar à rede Wi-Fi</AlertDialogTitle>
              <AlertDialogDescription asChild>
                <div className="mt-2 space-y-4 text-left">
                  <div>
                    <label
                      htmlFor="wifi-ssid"
                      className="mb-1 block text-sm font-medium text-foreground"
                    >
                      Rede
                    </label>
                    <Input
                      id="wifi-ssid"
                      type="text"
                      value={connectSSID}
                      readOnly
                      className="bg-muted"
                    />
                  </div>
                  <div>
                    <label
                      htmlFor="wifi-password"
                      className="mb-1 block text-sm font-medium text-foreground"
                    >
                      Senha
                    </label>
                    <Input
                      id="wifi-password"
                      type={showConnectPassword ? "text" : "password"}
                      value={connectPassword}
                      onChange={(e) => setConnectPassword(e.target.value)}
                      placeholder="Digite a senha"
                      required
                    />
                    <label className="mt-2 flex cursor-pointer items-center gap-2 text-sm text-muted-foreground">
                      <input
                        type="checkbox"
                        checked={showConnectPassword}
                        onChange={(e) =>
                          setShowConnectPassword(e.target.checked)
                        }
                        className="rounded border-border"
                      />
                      Mostrar senha
                    </label>
                  </div>
                </div>
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel type="button" onClick={closeConnectModal}>
                Cancelar
              </AlertDialogCancel>
              <Button type="submit" disabled={connectLoading}>
                {connectLoading ? "Conectando…" : "Conectar"}
              </Button>
            </AlertDialogFooter>
          </form>
        </AlertDialogContent>
      </AlertDialog>

      {/* Modal Esquecer rede */}
      <AlertDialog open={forgetConfirmOpen} onOpenChange={setForgetConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remover rede</AlertDialogTitle>
            <AlertDialogDescription>
              Deseja remover a rede &quot;{networkToForget}&quot;?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={closeForgetConfirm}>
              Cancelar
            </AlertDialogCancel>
            <AlertDialogAction variant="destructive" onClick={forgetNetwork}>
              Esquecer
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
