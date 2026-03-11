import { useEffect } from "react"
import { useLocation } from "react-router-dom"

/**
 * Rolagem para o topo da página sempre que a rota mudar (Avançar, Voltar, links do header).
 */
export function ScrollToTop() {
  const { pathname } = useLocation()

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])

  return null
}
