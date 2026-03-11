import { Link, useLocation } from "react-router-dom";
import { usePrinterStatus } from "@/hooks/usePrinterStatus";
import { useSelectedPrintFile } from "@/contexts/SelectedPrintFileContext";
import { Button } from "@/components/ui/button";
import { ArrowRight01Icon } from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";
import { PRINT_FLOW_STEPS, getCurrentStep } from "@/lib/printFlow";
import { cn } from "@/lib/utils";

/**
 * Botão "Avançar" do fluxo de impressão. Deve ser colocado no canto inferior direito ao final de cada página do fluxo.
 * Só renderiza quando há próximo passo (passos 1–4); no passo 5 (Revisão) retorna null.
 */
export function PrintFlowAdvance() {
  const location = useLocation();
  const { connected, state } = usePrinterStatus();
  const { selectedFile } = useSelectedPrintFile();
  const currentStep = getCurrentStep(location.pathname, connected, state);
  const nextStep = currentStep < 5 ? PRINT_FLOW_STEPS[currentStep] : null;
  const prevStep = currentStep > 1 ? PRINT_FLOW_STEPS[currentStep - 2] : null;
  const step2NeedsFile = currentStep === 2 && !selectedFile;
  const canAdvance =
    nextStep &&
    (currentStep === 1 ? connected : true) &&
    (currentStep === 2 ? !!selectedFile : true);

  if (!nextStep && !prevStep) return null;

  const containerClass = cn(
    "flex pt-6 pb-2",
    prevStep ? "justify-between gap-3" : "justify-end",
  );

  return (
    <div className={containerClass}>
      {prevStep && (
        <Button asChild size="sm" variant="ghost">
          <Link to={prevStep.path}>Voltar</Link>
        </Button>
      )}

      {nextStep &&
        (canAdvance ? (
          <Button asChild size="sm">
            <Link to={nextStep.path}>
              Avançar
              <HugeiconsIcon icon={ArrowRight01Icon} className="size-4" />
            </Link>
          </Button>
        ) : (
          <div className="flex flex-col items-end gap-1">
            <Button
              size="sm"
              disabled
              title={
                currentStep === 1
                  ? "Conecte a impressora para avançar"
                  : currentStep === 2
                    ? "Selecione um arquivo para avançar"
                    : undefined
              }
            >
              Avançar
              <HugeiconsIcon icon={ArrowRight01Icon} className="size-4" />
            </Button>
            {step2NeedsFile && (
              <p className="text-xs text-muted-foreground text-right max-w-[280px]">
                Selecione um arquivo g-code lista acima para prosseguir.
              </p>
            )}
          </div>
        ))}
    </div>
  );
}
