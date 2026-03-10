import { createContext, useContext, useState, useCallback } from "react"

export interface SelectedPrintFile {
  id: number
  name: string
  size: number
  uploaded: string
  last_printed: string | null
  print_count: number
  thumbnail: string | null
  print_time: string | null
  filament_used: number | null
  filament_type: string | null
  nozzle_temp: number | null
  bed_temp: number | null
  layer_height: number | null
  infill: number | null
}

interface SelectedPrintFileContextValue {
  selectedFile: SelectedPrintFile | null
  setSelectedFile: (file: SelectedPrintFile | null) => void
}

const SelectedPrintFileContext = createContext<SelectedPrintFileContextValue | null>(null)

export function SelectedPrintFileProvider({ children }: { children: React.ReactNode }) {
  const [selectedFile, setSelectedFileState] = useState<SelectedPrintFile | null>(null)
  const setSelectedFile = useCallback((file: SelectedPrintFile | null) => {
    setSelectedFileState(file)
  }, [])
  return (
    <SelectedPrintFileContext.Provider value={{ selectedFile, setSelectedFile }}>
      {children}
    </SelectedPrintFileContext.Provider>
  )
}

export function useSelectedPrintFile() {
  const ctx = useContext(SelectedPrintFileContext)
  if (!ctx) throw new Error("useSelectedPrintFile must be used within SelectedPrintFileProvider")
  return ctx
}
