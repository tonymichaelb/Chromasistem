import { Link, useLocation } from "react-router-dom"
import { usePrinterStatus } from "@/hooks/usePrinterStatus"
import { Button } from "@/components/ui/button"
import { ArrowRight01Icon } from "@hugeicons/core-free-icons"
import { HugeiconsIcon } from "@hugeicons/react"
import { PRINT_FLOW_STEPS, getCurrentStep } from "@/lib/printFlow"

/**
 * Botão "Avançar" do fluxo de impressão. Deve ser colocado no canto inferior direito ao final de cada página do fluxo.
 * Só renderiza quando há próximo passo (passos 1–4); no passo 5 (Revisão) e 6 (Imprimir) retorna null.
 */
export function PrintFlowAdvance() {
  const location = useLocation()
  const { connected, state } = usePrinterStatus()
  const currentStep = getCurrentStep(location.pathname, connected, state)
  const nextStep = currentStep < 5 ? PRINT_FLOW_STEPS[currentStep] : null
  const canAdvance = nextStep && (currentStep === 1 ? connected : true)

  if (!nextStep) return null

  return (
    <div className="flex justify-end pt-6 pb-2">
      {canAdvance ? (
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
      )}
    </div>
  )
}
