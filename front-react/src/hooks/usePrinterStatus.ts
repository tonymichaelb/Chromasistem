import { usePrinterStatusContext } from "@/contexts/PrinterStatusContext"

/**
 * Retorna connected e state da impressora. O polling é feito uma única vez em PrinterStatusContext.
 */
export function usePrinterStatus() {
  const { connected, state } = usePrinterStatusContext()
  return { connected, state }
}
