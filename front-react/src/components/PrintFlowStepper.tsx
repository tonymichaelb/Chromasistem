import { Fragment } from "react"
import { Link, useLocation } from "react-router-dom"
import { cn } from "@/lib/utils"
import { usePrinterStatus } from "@/hooks/usePrinterStatus"
import { Card, CardContent } from "@/components/ui/card"
import { PRINT_FLOW_STEPS, getCurrentStep } from "@/lib/printFlow"

export function PrintFlowStepper() {
  const location = useLocation()
  const { connected, state } = usePrinterStatus()
  const currentStep = getCurrentStep(location.pathname, connected, state)
  const progressPercent =
    PRINT_FLOW_STEPS.length > 1 ? ((currentStep - 1) / (PRINT_FLOW_STEPS.length - 1)) * 100 : 0

  return (
    <Card className="rounded-[22px] border-border bg-card shadow-sm">
      <CardContent className="p-4">
        {/* Passos + separadores — igual ao wireframe (.steps > .step + .sep) */}
        <div
          className="flex flex-wrap items-center gap-2 sm:gap-2.5"
          role="navigation"
          aria-label="Fluxo de impressão"
        >
          {PRINT_FLOW_STEPS.map(({ step, label, path }, index) => {
            const isActive = currentStep === step
            const isCompleted = step < currentStep
            const canNavigate = step === 1 || connected

            const stepContent = (
              <div className="flex items-center gap-2">
                <div
                  className={cn(
                    "flex h-[26px] w-[26px] shrink-0 items-center justify-center rounded-full border text-xs font-bold transition-colors",
                    isActive &&
                      "border-primary bg-primary/10 text-primary dark:bg-primary/20",
                    isCompleted &&
                      "border-primary/40 bg-primary/10 text-primary/80 dark:border-primary/50 dark:bg-primary/15 dark:text-white/70",
                    !isActive &&
                      !isCompleted &&
                      "border-border bg-muted/50 text-muted-foreground"
                  )}
                >
                  {step}
                </div>
                <div
                  className={cn(
                    "text-[13px] transition-colors",
                    isActive && "font-semibold text-foreground",
                    isCompleted &&
                      "font-medium text-primary/80 dark:text-white/70",
                    !isActive &&
                      !isCompleted &&
                      "text-muted-foreground"
                  )}
                >
                  {label}
                </div>
              </div>
            )

            return (
              <Fragment key={step}>
                <div className="flex items-center gap-2">
                  {canNavigate ? (
                    <Link
                      to={path}
                      className="flex items-center gap-2 rounded-md outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                      aria-current={isActive ? "step" : undefined}
                    >
                      {stepContent}
                    </Link>
                  ) : (
                    <span
                      className="flex cursor-not-allowed items-center gap-2 opacity-70"
                      title="Conecte a impressora no passo 1 para continuar"
                    >
                      {stepContent}
                    </span>
                  )}
                </div>
                {index < PRINT_FLOW_STEPS.length - 1 && (
                  <div className="h-px min-w-9 flex-1 bg-border" aria-hidden />
                )}
              </Fragment>
            )
          })}
        </div>

        {/* Barra de progresso — igual ao wireframe: .progress > .bar */}
        <div className="mt-3 h-2.5 overflow-hidden rounded-full bg-muted">
          <div
            className="h-full rounded-full bg-gradient-to-r from-primary to-violet-600 transition-all duration-300"
            style={{ width: `${progressPercent}%` }}
            role="progressbar"
            aria-valuenow={currentStep}
            aria-valuemin={1}
            aria-valuemax={PRINT_FLOW_STEPS.length}
          />
        </div>
      </CardContent>
    </Card>
  )
}
