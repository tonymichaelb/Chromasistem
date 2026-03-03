import { Link } from "react-router-dom"
import { AppHeader } from "@/components/AppHeader"

/**
 * Placeholders para rotas ainda não implementadas.
 * Cada um pode ser substituído pela página real depois.
 */

const PlaceholderLayout = ({ title }: { title: string }) => (
  <div className="min-h-screen bg-muted/30">
    <AppHeader />
    <div className="flex flex-col items-center justify-center gap-4 p-4 sm:p-8">
      <p className="text-muted-foreground">{title}</p>
      <Link to="/dashboard" className="text-primary underline">Voltar ao Dashboard</Link>
    </div>
  </div>
)

export function FilesPlaceholder() {
  return <PlaceholderLayout title="Página de Arquivos — em breve." />
}

export function TerminalPlaceholder() {
  return <PlaceholderLayout title="Terminal — em breve." />
}

export function ColorirPlaceholder() {
  return <PlaceholderLayout title="Colorir — em breve." />
}

export function WifiPlaceholder() {
  return <PlaceholderLayout title="Wi-Fi — em breve." />
}
