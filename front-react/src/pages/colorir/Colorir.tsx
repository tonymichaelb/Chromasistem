import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
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
import { useColorir, type CmyMix } from "./hook"
import { HugeiconsIcon } from "@hugeicons/react"
import { SettingsIcon } from "@hugeicons/core-free-icons"

const BRUSH_COUNT = 19

export function Colorir() {
  const {
    currentBrushIndex,
    brushCustomColors,
    tintaCustomColors,
    notification,
    mixtureModalOpen,
    setMixtureModalOpen,
    modalSliders,
    modalCustomColor,
    setModalCustomColor,
    customColorHex,
    customCmy,
    updateCustomColorFromHex,
    helpOpen,
    setHelpOpen,
    selectBrush,
    applyTintaToBrush,
    openMixtureModal,
    updateModalSlider,
    saveMixtureModal,
    applyCustomColorToBrush,
    TINTA_DEFAULT_COLORS,
  } = useColorir()

  const currentBrushLabel =
    currentBrushIndex === null
      ? "Nenhum — Clique em um pincel para começar"
      : brushCustomColors[currentBrushIndex]
        ? `Pincel ${currentBrushIndex + 1} — Com cor aplicada`
        : `Pincel ${currentBrushIndex + 1} — Sem cor (clique em uma tinta para aplicar)`

  return (
    <div className="min-h-screen bg-muted/30">
      <AppHeader />
      <main className="container mx-auto max-w-5xl space-y-6 px-3 py-4 sm:px-4 md:p-6">
        <div>
          <h1 className="text-xl font-semibold sm:text-2xl">Colorir — Sistema de Pincéis e Tintas</h1>
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
          <CardContent className="pt-6">
            <p className="text-center font-medium text-muted-foreground">
              Pincel selecionado: <span className="text-foreground">{currentBrushLabel}</span>
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Pincéis disponíveis (1 a 19)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
              {Array.from({ length: BRUSH_COUNT }, (_, i) => {
                const customColor = brushCustomColors[i]
                return (
                  <Button
                    key={i}
                    variant={currentBrushIndex === i ? "default" : "outline"}
                    className={cn(
                      "flex h-auto flex-col gap-1 py-4 transition-all",
                      customColor && "border-l-4 border-l-primary"
                    )}
                    style={customColor ? { borderLeftColor: customColor } : undefined}
                    onClick={() => selectBrush(i)}
                  >
                    <span className="text-xl">🖌️</span>
                    <span className="text-xs font-medium">Pincel {i + 1}</span>
                  </Button>
                )
              })}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Tintas disponíveis (1 a 19)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6">
              {Array.from({ length: BRUSH_COUNT }, (_, i) => {
                const color = tintaCustomColors[i] ?? TINTA_DEFAULT_COLORS[i]
                return (
                  <div key={i} className="flex flex-col items-center gap-2">
                    <div className="relative w-full">
                      <button
                        type="button"
                        className="h-14 w-full rounded-lg border-2 border-border shadow-sm transition-transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-ring"
                        style={{ backgroundColor: color }}
                        onClick={() => applyTintaToBrush(i)}
                        aria-label={`Aplicar tinta ${i + 1}`}
                      />
                      <Button
                        variant="secondary"
                        size="icon-sm"
                        className="absolute right-1 top-1 size-7 rounded-full shadow"
                        onClick={(e) => {
                          e.stopPropagation()
                          openMixtureModal(i)
                        }}
                        aria-label={`Configurar mistura tinta ${i + 1}`}
                      >
                        <HugeiconsIcon icon={SettingsIcon} className="size-3.5" />
                      </Button>
                    </div>
                    <span className="text-xs font-medium text-muted-foreground">{i + 1}</span>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Cor personalizada (100+ cores)</CardTitle>
            <CardDescription>
              Escolha qualquer cor. O sistema calcula a mistura Ciano/Magenta/Amarelo e aplica ao pincel selecionado.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
              <div className="shrink-0">
                <label className="mb-2 block text-sm font-medium">Clique para escolher a cor</label>
                <div
                  className="size-20 cursor-pointer overflow-hidden rounded-xl border-2 border-border shadow-md"
                  style={{ backgroundColor: customColorHex }}
                >
                  <input
                    type="color"
                    value={customColorHex}
                    onChange={(e) => updateCustomColorFromHex(e.target.value)}
                    className="size-full cursor-pointer opacity-0"
                    aria-label="Seletor de cor"
                  />
                </div>
              </div>
              <div className="min-w-0 flex-1 space-y-2">
                <div
                  className="h-12 w-full rounded-lg border-2 border-border"
                  style={{ backgroundColor: customColorHex }}
                />
                <p className="text-sm text-muted-foreground">
                  Ciano (A): <span className="font-semibold text-foreground">{customCmy.a}%</span>
                  <br />
                  Magenta (B): <span className="font-semibold text-foreground">{customCmy.b}%</span>
                  <br />
                  Amarelo (C): <span className="font-semibold text-foreground">{customCmy.c}%</span>
                </p>
                <Button onClick={applyCustomColorToBrush} className="w-full sm:w-auto">
                  Aplicar ao pincel atual
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </main>

      {/* Botão de ajuda flutuante */}
      <Button
        size="icon"
        className="fixed bottom-6 right-6 size-14 rounded-full shadow-lg"
        onClick={() => setHelpOpen(true)}
        aria-label="Como funciona"
      >
        <span className="text-xl">?</span>
      </Button>

      {/* Modal de mistura */}
      <AlertDialog open={mixtureModalOpen} onOpenChange={setMixtureModalOpen}>
        <AlertDialogContent className="max-w-md">
          <AlertDialogHeader>
            <AlertDialogTitle>Configuração de mistura de cores</AlertDialogTitle>
            <AlertDialogDescription>
              Ajuste as porcentagens de cada filamento. O total deve ser 100%. A prévia mostra a mistura CMY; use o
              seletor para uma cor RGB personalizada.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="space-y-4 py-2">
            <SliderRow
              label="Filamento Ciano"
              value={modalSliders.a}
              onChange={(v) => updateModalSlider("a", v)}
            />
            <SliderRow
              label="Filamento Magenta"
              value={modalSliders.b}
              onChange={(v) => updateModalSlider("b", v)}
            />
            <SliderRow
              label="Filamento Amarelo"
              value={modalSliders.c}
              onChange={(v) => updateModalSlider("c", v)}
            />
            <div className="rounded-lg border-2 border-primary/30 bg-primary/5 px-4 py-3 text-center font-medium">
              Total: {modalSliders.a + modalSliders.b + modalSliders.c}%
            </div>
            <div className="flex flex-wrap justify-center gap-6">
              <div className="flex flex-col items-center gap-1">
                <span className="text-xs font-medium text-muted-foreground">Prévia da mistura</span>
                <div
                  className="size-16 rounded-full border-2 border-border shadow"
                  style={{
                    backgroundColor: cmyToRgbHex(modalSliders),
                  }}
                />
              </div>
              <div className="flex flex-col items-center gap-1">
                <span className="text-xs font-medium text-muted-foreground">Cor personalizada</span>
                <div className="relative size-16 rounded-full border-2 border-border shadow">
                  <div
                    className="absolute inset-0 rounded-full"
                    style={{ backgroundColor: modalCustomColor }}
                  />
                  <input
                    type="color"
                    value={modalCustomColor}
                    onChange={(e) => setModalCustomColor(e.target.value)}
                    className="absolute inset-0 size-full cursor-pointer rounded-full opacity-0"
                  />
                </div>
              </div>
            </div>
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={saveMixtureModal}>Salvar</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Modal de ajuda */}
      <AlertDialog open={helpOpen} onOpenChange={setHelpOpen}>
        <AlertDialogContent className="max-w-lg">
          <AlertDialogHeader>
            <AlertDialogTitle>Como funciona</AlertDialogTitle>
            <AlertDialogDescription asChild>
              <div className="space-y-3 text-left text-foreground">
                <p>
                  <strong>Bem-vindo ao Sistema de Pincéis e Tintas!</strong> Siga os passos abaixo:
                </p>
                <ol className="list-inside list-decimal space-y-2">
                  <li>
                    <strong>Escolha um pincel:</strong> Clique em um dos 19 pincéis. Cada um representa uma ferramenta
                    de impressão.
                  </li>
                  <li>
                    <strong>Selecione uma tinta:</strong> Depois de escolher o pincel, clique em uma das 19 tintas
                    para aplicar a cor.
                  </li>
                  <li>
                    <strong>Personalize a mistura (opcional):</strong> Clique na engrenagem em qualquer tinta para
                    ajustar Ciano, Magenta e Amarelo ou escolher uma cor RGB.
                  </li>
                  <li>
                    <strong>Cor personalizada:</strong> Na seção abaixo, escolha qualquer cor no seletor e aplique ao
                    pincel atual.
                  </li>
                </ol>
                <div className="rounded-lg border-l-4 border-amber-500 bg-amber-500/10 p-3 text-sm text-amber-800 dark:text-amber-200">
                  <strong>Dica:</strong> As configurações são salvas automaticamente no servidor.
                </div>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogAction onClick={() => setHelpOpen(false)}>Entendi</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}

function SliderRow({
  label,
  value,
  onChange,
}: {
  label: string
  value: number
  onChange: (v: number) => void
}) {
  return (
    <div>
      <div className="mb-1 flex justify-between text-sm font-medium">
        <span>{label}</span>
        <span className="text-primary">{value}%</span>
      </div>
      <input
        type="range"
        min={0}
        max={100}
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value, 10))}
        className="w-full accent-primary"
      />
    </div>
  )
}

function cmyToRgbHex(mix: CmyMix): string {
  const total = mix.a + mix.b + mix.c
  if (total <= 0) return "#808080"
  const c = mix.a / total
  const m = mix.b / total
  const y = mix.c / total
  const r = Math.min(255, Math.round(255 * (m + y)))
  const g = Math.min(255, Math.round(255 * (c + y)))
  const b = Math.min(255, Math.round(255 * (c + m)))
  return `#${[r, g, b].map((x) => x.toString(16).padStart(2, "0")).join("")}`
}
