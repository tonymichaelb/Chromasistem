import { useState, useRef, useEffect } from "react"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { AppHeader } from "@/components/AppHeader"
import { cn } from "@/lib/utils"
import { useTerminal } from "./hook"
import { HugeiconsIcon } from "@hugeicons/react"
import {
  HomeIcon,
  ArrowUp01Icon,
  ArrowDown01Icon,
  ArrowLeft01Icon,
  ArrowRight01Icon,
} from "@hugeicons/core-free-icons"

const JOG_OPTIONS = [0.1, 1, 10, 100] as const
const QUICK_COMMANDS = [
  { cmd: "M105", label: "M105 (Temp)" },
  { cmd: "M114", label: "M114 (Pos)" },
  { cmd: "M115", label: "M115 (Info)" },
  { cmd: "M503", label: "M503 (Config)" },
  { cmd: "M119", label: "M119 (Endstops)" },
]

export function Terminal() {
  const {
    nozzleInput,
    setNozzleInput,
    bedInput,
    setBedInput,
    currentNozzle,
    currentBed,
    targetNozzle,
    targetBed,
    tempHistory,
    jogDistance,
    setJogDistance,
    terminalLines,
    notification,
    setNozzleTemp,
    setBedTemp,
    setPreset,
    jogAxis,
    homeAxis,
    homeAll,
    extrudeFilament,
    preheatExtruder,
    sendGcode,
    clearTerminal,
    quickCommand,
  } = useTerminal()

  const [gcodeInput, setGcodeInput] = useState("")
  const terminalEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [terminalLines])

  const handleSendGcode = () => {
    sendGcode(gcodeInput.trim())
    setGcodeInput("")
  }

  return (
    <div className="min-h-screen bg-muted/30">
      <AppHeader />
      <main className="container mx-auto max-w-6xl space-y-6 px-3 py-4 sm:px-4 md:p-6">
        <div>
          <h1 className="text-xl font-semibold sm:text-2xl">Terminal & Controles</h1>
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

        <div className="grid gap-6 lg:grid-cols-2">
          {/* Controle de Temperatura */}
          <Card>
            <CardHeader>
              <CardTitle>Controle de Temperatura</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h3 className="mb-2 text-sm font-medium">Bico (Hotend)</h3>
                <div className="flex flex-wrap gap-2">
                  <Input
                    type="number"
                    min={0}
                    max={300}
                    placeholder="Temp (°C)"
                    value={nozzleInput}
                    onChange={(e) => setNozzleInput(e.target.value)}
                    className="w-24"
                  />
                  <Button onClick={() => setNozzleTemp()}>Definir</Button>
                  <Button variant="secondary" onClick={() => setNozzleTemp(0)}>
                    Off
                  </Button>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  Atual: {currentNozzle ?? "--"}°C / Target: {targetNozzle ?? "--"}°C
                </p>
              </div>
              <div>
                <h3 className="mb-2 text-sm font-medium">Mesa (Bed)</h3>
                <div className="flex flex-wrap gap-2">
                  <Input
                    type="number"
                    min={0}
                    max={120}
                    placeholder="Temp (°C)"
                    value={bedInput}
                    onChange={(e) => setBedInput(e.target.value)}
                    className="w-24"
                  />
                  <Button onClick={() => setBedTemp()}>Definir</Button>
                  <Button variant="secondary" onClick={() => setBedTemp(0)}>
                    Off
                  </Button>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  Atual: {currentBed ?? "--"}°C / Target: {targetBed ?? "--"}°C
                </p>
              </div>
              <div>
                <h3 className="mb-2 text-sm font-medium">Presets</h3>
                <div className="flex flex-wrap gap-2">
                  <Button variant="secondary" size="sm" onClick={() => setPreset(210, 60)}>
                    PLA (210/60)
                  </Button>
                  <Button variant="secondary" size="sm" onClick={() => setPreset(240, 80)}>
                    ABS (240/80)
                  </Button>
                  <Button variant="secondary" size="sm" onClick={() => setPreset(230, 85)}>
                    PETG (230/85)
                  </Button>
                  <Button variant="secondary" size="sm" onClick={() => setPreset(220, 60)}>
                    TPU (220/60)
                  </Button>
                  <Button variant="destructive" size="sm" onClick={() => setPreset(0, 0)}>
                    Desligar Tudo
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Temperatura em tempo real (últimas leituras) */}
          <Card>
            <CardHeader>
              <CardTitle>Temperatura em Tempo Real</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="max-h-[300px] overflow-y-auto rounded-lg border border-border bg-muted/30 p-3 font-mono text-xs">
                {tempHistory.length === 0 ? (
                  <p className="text-muted-foreground">Aguardando leituras...</p>
                ) : (
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-border text-muted-foreground">
                        <th className="py-1 text-left">Hora</th>
                        <th className="py-1 text-right">Bico</th>
                        <th className="py-1 text-right">Mesa</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[...tempHistory].reverse().slice(0, 30).map((r, i) => (
                        <tr key={i} className="border-b border-border/50">
                          <td className="py-0.5">{r.time}</td>
                          <td className="text-right text-red-600 dark:text-red-400">{r.nozzle}°C</td>
                          <td className="text-right text-blue-600 dark:text-blue-400">{r.bed}°C</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Controle de Movimento */}
          <Card>
            <CardHeader>
              <CardTitle>Controle de Movimento</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="mb-1 block text-sm font-medium">Distância</label>
                <div className="flex flex-wrap gap-1 [&_button]:min-h-10 [&_button]:touch-manipulation">
                  {JOG_OPTIONS.map((d) => (
                    <Button
                      key={d}
                      variant={jogDistance === d ? "default" : "outline"}
                      size="sm"
                      onClick={() => setJogDistance(d)}
                    >
                      {d}mm
                    </Button>
                  ))}
                </div>
              </div>
              <div>
                <h3 className="mb-2 text-sm font-medium">Eixos X/Y</h3>
                <div className="grid max-w-[220px] grid-cols-3 gap-1 [&_button]:min-h-10 [&_button]:touch-manipulation">
                  <div />
                  <Button variant="secondary" size="sm" onClick={() => jogAxis("Y", jogDistance)}>
                    <HugeiconsIcon icon={ArrowUp01Icon} className="size-4" />
                    Y+
                  </Button>
                  <div />
                  <Button variant="secondary" size="sm" onClick={() => jogAxis("X", -jogDistance)}>
                    <HugeiconsIcon icon={ArrowLeft01Icon} className="size-4" />
                    X-
                  </Button>
                  <Button size="sm" onClick={() => homeAxis("XY")}>
                    <HugeiconsIcon icon={HomeIcon} className="size-4" />
                    Home
                  </Button>
                  <Button variant="secondary" size="sm" onClick={() => jogAxis("X", jogDistance)}>
                    X+
                    <HugeiconsIcon icon={ArrowRight01Icon} className="size-4" />
                  </Button>
                  <div />
                  <Button variant="secondary" size="sm" onClick={() => jogAxis("Y", -jogDistance)}>
                    <HugeiconsIcon icon={ArrowDown01Icon} className="size-4" />
                    Y-
                  </Button>
                  <div />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h3 className="mb-2 text-sm font-medium">Eixo Z</h3>
                  <div className="flex flex-col gap-1">
                    <Button variant="secondary" size="sm" onClick={() => jogAxis("Z", jogDistance)}>
                      <HugeiconsIcon icon={ArrowUp01Icon} className="size-4" />
                      Z+
                    </Button>
                    <Button size="sm" onClick={() => homeAxis("Z")}>
                      <HugeiconsIcon icon={HomeIcon} className="size-4" />
                      Home Z
                    </Button>
                    <Button variant="secondary" size="sm" onClick={() => jogAxis("Z", -jogDistance)}>
                      <HugeiconsIcon icon={ArrowDown01Icon} className="size-4" />
                      Z-
                    </Button>
                  </div>
                </div>
                <div>
                  <h3 className="mb-2 text-sm font-medium">Extrusora</h3>
                  <div className="flex flex-col gap-1">
                    <Button size="sm" onClick={() => extrudeFilament(jogDistance)}>
                      <HugeiconsIcon icon={ArrowUp01Icon} className="size-4" />
                      Extrudar
                    </Button>
                    <Button variant="secondary" size="sm" onClick={preheatExtruder}>
                      Pre-aquecer
                    </Button>
                    <Button variant="destructive" size="sm" onClick={() => extrudeFilament(-jogDistance)}>
                      <HugeiconsIcon icon={ArrowDown01Icon} className="size-4" />
                      Retrair
                    </Button>
                  </div>
                </div>
              </div>
              <Button className="w-full" onClick={homeAll}>
                <HugeiconsIcon icon={HomeIcon} className="size-4" />
                Home All (X, Y, Z)
              </Button>
            </CardContent>
          </Card>

          {/* Terminal G-code */}
          <Card>
            <CardHeader>
              <CardTitle>Terminal G-code</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div
                className="h-[300px] overflow-y-auto rounded-lg border border-border bg-[#1e1e1e] p-3 font-mono text-xs text-[#00ff00]"
                role="log"
                aria-label="Saída do terminal"
              >
                {terminalLines.map((line, i) => (
                  <div
                    key={i}
                    className="mb-0.5 break-all"
                    style={{
                      color:
                        line.type === "command"
                          ? "#ffff00"
                          : line.type === "error"
                            ? "#ff0000"
                            : line.type === "output" && line.text.startsWith("Terminal")
                              ? "#888"
                              : "#00ff00",
                    }}
                  >
                    {line.text}
                  </div>
                ))}
                <div ref={terminalEndRef} />
              </div>
              <div className="flex min-w-0 flex-wrap gap-2 [&_button]:shrink-0 [&_button]:touch-manipulation">
                <Input
                  placeholder="Digite comando G-code (ex: M105)"
                  value={gcodeInput}
                  onChange={(e) => setGcodeInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSendGcode()}
                  className="min-w-0 flex-1 basis-32 font-mono"
                />
                <Button onClick={handleSendGcode}>Enviar</Button>
                <Button variant="secondary" onClick={clearTerminal}>
                  Limpar
                </Button>
              </div>
              <div>
                <h3 className="mb-1 text-sm font-medium">Comandos rápidos</h3>
                <div className="flex flex-wrap gap-1 [&_button]:touch-manipulation">
                  {QUICK_COMMANDS.map(({ cmd, label }) => (
                    <Button key={cmd} variant="secondary" size="sm" onClick={() => quickCommand(cmd)}>
                      {label}
                    </Button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  )
}
