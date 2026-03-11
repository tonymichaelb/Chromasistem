import { Link, useLocation } from "react-router-dom"
import { usePrinterStatus } from "@/hooks/usePrinterStatus"
import { Button } from "@/components/ui/button"
import { ArrowRight01Icon } from "@hugeicons/core-free-icons"
import { HugeiconsIcon } from "@hugeicons/react"
import { PRINT_FLOW_STEPS, getCurrentStep } from "@/lib/printFlow"
import { cn } from "@/lib/utils"

/**
 * Botão "Avançar" do fluxo de impressão. Deve ser colocado no canto inferior direito ao final de cada página do fluxo.
 * Só renderiza quando há próximo passo (passos 1–4); no passo 5 (Revisão) e 6 (Imprimir) retorna null.
 */
export function PrintFlowAdvance() {
  const location = useLocation()
  const { connected, state } = usePrinterStatus()
  const currentStep = getCurrentStep(location.pathname, connected, state)
  const nextStep = currentStep < 5 ? PRINT_FLOW_STEPS[currentStep] : null
  const prevStep = currentStep > 1 && currentStep !== 6 ? PRINT_FLOW_STEPS[currentStep - 2] : null
  const canAdvance = nextStep && (currentStep === 1 ? connected : true)

  // No passo 6 (Monitor com impressora imprimindo) não exibir barra (sem Voltar nem Avançar)
  if (currentStep === 6) return null
  if (!nextStep && !prevStep) return null

  const containerClass = cn(
    "flex pt-6 pb-2",
    prevStep ? "justify-between gap-3" : "justify-end"
  )

  return (
    <div className={containerClass}>
      {prevStep && (
        <Button asChild size="sm" variant="ghost">
          <Link to={prevStep.path}>Voltar</Link>
        </Button>
      )}

      {nextStep && (
        canAdvance ? (
          <Button asChild size="sm">
            <Link to={nextStep.path}>
              Avançar
              <HugeiconsIcon icon={ArrowRight01Icon} className="size-4" />
            </Link>
          </Button>
        ) : (
          <Button
            size="sm"
            disabled
            title={currentStep === 1 ? "Conecte a impressora para avançar" : undefined}
          >
            Avançar
            <HugeiconsIcon icon={ArrowRight01Icon} className="size-4" />
          </Button>
        )
      )}
    </div>
  )
}
