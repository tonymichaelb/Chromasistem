import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { AppHeader } from "@/components/AppHeader"
import { cn } from "@/lib/utils"
import { useMistura } from "./hook"

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

export function Mistura() {
  const {
    mix,
    suggestColorHex,
    notification,
    sending,
    isValid,
    commandPreview,
    updateSlider,
    applySuggestColor,
    sendMixture,
  } = useMistura()

  return (
    <div className="min-h-screen bg-muted/30">
      <AppHeader />
      <main className="container mx-auto max-w-2xl space-y-6 px-3 py-4 sm:px-4 md:p-6">
        <div>
          <h1 className="text-xl font-semibold sm:text-2xl">Mistura de filamentos</h1>
          <p className="text-muted-foreground">Ajuste a proporção de cada filamento. A soma deve ser 100%.</p>
        </div>

        <Card className="border-l-4 border-l-primary">
          <CardContent className="pt-6">
            <p className="text-sm">
              <strong>Comando:</strong> M182 A[%] B[%] C[%]
              <br />
              Filamento A (Extrusora 1) • Filamento B (Extrusora 2) • Filamento C (Extrusora 3)
            </p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-primary">
          <CardHeader>
            <CardTitle className="text-base">Sugerir mistura a partir de uma cor</CardTitle>
            <CardDescription>
              Escolha uma cor para preencher os percentuais automaticamente. Tons mais escuros tendem a uma mistura
              mais neutra; tons mais claros, ao matiz da cor. Ajuste os sliders se quiser e envie.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap items-center gap-4">
              <div
                className="size-14 shrink-0 cursor-pointer overflow-hidden rounded-lg border-2 border-primary shadow"
                style={{ backgroundColor: suggestColorHex }}
              >
                <input
                  type="color"
                  value={suggestColorHex}
                  onChange={(e) => applySuggestColor(e.target.value)}
                  className="size-full cursor-pointer opacity-0"
                  aria-label="Escolher cor para sugerir A/B/C"
                />
              </div>
              <span className="min-w-0 text-sm text-muted-foreground">
                Clique no quadrado para escolher uma cor e preencher Ciano/Magenta/Amarelo.
              </span>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Filamento A (Extrusora 1)</CardTitle>
            </CardHeader>
            <CardContent>
              <SliderRow label="" value={mix.a} onChange={(v) => updateSlider("a", v)} />
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Filamento B (Extrusora 2)</CardTitle>
            </CardHeader>
            <CardContent>
              <SliderRow label="" value={mix.b} onChange={(v) => updateSlider("b", v)} />
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Filamento C (Extrusora 3)</CardTitle>
            </CardHeader>
            <CardContent>
              <SliderRow label="" value={mix.c} onChange={(v) => updateSlider("c", v)} />
            </CardContent>
          </Card>
        </div>

        <Card
          className={cn(
            "text-center",
            isValid ? "border-2 border-primary/30 bg-primary/5" : "border-2 border-destructive/30 bg-destructive/5"
          )}
        >
          <CardContent className="pt-6">
            <p className="text-sm font-medium text-muted-foreground">Total</p>
            <p className={cn("text-2xl font-bold", isValid ? "text-primary" : "text-destructive")}>
              {mix.a + mix.b + mix.c}%
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <p className="mb-1 text-sm font-medium text-muted-foreground">Comando a enviar</p>
            <code className="block break-all rounded-lg bg-muted px-3 py-2 font-mono text-sm">
              {commandPreview}
            </code>
          </CardContent>
        </Card>

        <Button
          className="w-full min-h-10 touch-manipulation"
          disabled={!isValid || sending}
          onClick={sendMixture}
        >
          {sending ? "Enviando…" : "Enviar mistura"}
        </Button>

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
      </main>
    </div>
  )
}
