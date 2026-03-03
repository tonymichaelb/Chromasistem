import { useState, useEffect, useRef } from "react"
import { Link, useLocation, useNavigate } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { HugeiconsIcon } from "@hugeicons/react"
import {
  LogoutIcon,
  File01Icon,
  PaintBoardIcon,
  ComputerTerminal01Icon,
  WifiIcon,
  SunIcon,
  MoonIcon,
  Menu01Icon,
  Cancel01Icon,
  Chemistry01Icon,
  LayersIcon,
} from "@hugeicons/core-free-icons"
import { useAuth } from "@/contexts/AuthContext"

const THEME_STORAGE_KEY = "croma-theme"

type Theme = "light" | "dark"

function getInitialTheme(): Theme {
  if (typeof window === "undefined") return "light"
  const stored = localStorage.getItem(THEME_STORAGE_KEY) as Theme | null
  if (stored === "dark" || stored === "light") return stored
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"
}

function applyTheme(theme: Theme) {
  const root = document.documentElement
  if (theme === "dark") root.classList.add("dark")
  else root.classList.remove("dark")
}

export interface AppHeaderProps {
  username?: string
  onLogout?: () => void
}

export function AppHeader({ username: usernameProp, onLogout: onLogoutProp }: AppHeaderProps) {
  const location = useLocation()
  const navigate = useNavigate()
  const { username: usernameContext, setUsername } = useAuth()
  const [theme, setTheme] = useState<Theme>(getInitialTheme)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const headerRef = useRef<HTMLElement>(null)

  const username = usernameProp ?? usernameContext ?? ""
  const onLogout =
    onLogoutProp ??
    (() => {
      setUsername(null)
      fetch("/api/logout", { method: "POST", credentials: "include" }).then(() =>
        navigate("/login")
      )
    })

  useEffect(() => {
    applyTheme(theme)
    localStorage.setItem(THEME_STORAGE_KEY, theme)
  }, [theme])

  const toggleTheme = () => setTheme((t) => (t === "light" ? "dark" : "light"))

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (headerRef.current && !headerRef.current.contains(e.target as Node)) {
        setMobileMenuOpen(false)
      }
    }
    if (mobileMenuOpen) {
      document.body.style.overflow = "hidden"
      document.addEventListener("click", handleClickOutside, true)
    }
    return () => {
      document.body.style.overflow = ""
      document.removeEventListener("click", handleClickOutside, true)
    }
  }, [mobileMenuOpen])

  const navLinks = [
    { to: "/dashboard", label: "Dashboard" },
    { to: "/files", label: "Arquivos", icon: File01Icon },
    { to: "/fatiador", label: "Fatiador", icon: LayersIcon },
    { to: "/terminal", label: "Terminal", icon: ComputerTerminal01Icon },
    { to: "/colorir", label: "Colorir", icon: PaintBoardIcon },
    { to: "/mistura", label: "Mistura", icon: Chemistry01Icon },
    { to: "/wifi", label: "Wi-Fi", icon: WifiIcon },
  ]

  return (
    <header ref={headerRef} className="sticky top-0 z-40 border-b border-border bg-background">
      <div className="flex h-14 items-center justify-between gap-2 px-3 sm:px-4 md:px-6">
        <Link to="/dashboard" className="flex shrink-0 items-center gap-2">
          <img
            src="/images/logo-branca.png"
            alt="Croma"
            className="h-7 w-auto object-contain dark:invert sm:h-8"
          />
          <span className="font-semibold text-sm sm:text-base">Croma</span>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden flex-1 items-center justify-center gap-1 md:flex">
          {navLinks.map(({ to, label, icon: Icon }) => (
            <Link key={to} to={to}>
              <Button
                variant={location.pathname === to ? "default" : "ghost"}
                size="sm"
              >
                {Icon && (
                  <HugeiconsIcon icon={Icon} strokeWidth={2} className="size-4" />
                )}
                {label}
              </Button>
            </Link>
          ))}
        </nav>

        <div className="flex shrink-0 items-center gap-1 sm:gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            aria-label={theme === "light" ? "Ativar tema escuro" : "Ativar tema claro"}
          >
            <HugeiconsIcon
              icon={theme === "light" ? MoonIcon : SunIcon}
              strokeWidth={2}
              className="size-4"
            />
          </Button>
          {(usernameProp !== undefined || usernameContext !== null) && (
            <span className="hidden text-sm text-muted-foreground lg:inline">
              Bem-vindo, <strong className="text-foreground">{username || "…"}</strong>
            </span>
          )}
          {onLogout && (
            <Button variant="secondary" size="sm" onClick={onLogout} className="hidden md:inline-flex">
              <HugeiconsIcon icon={LogoutIcon} strokeWidth={2} className="size-4" />
              Sair
            </Button>
          )}
          {/* Mobile menu toggle */}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setMobileMenuOpen((o) => !o)}
            aria-label={mobileMenuOpen ? "Fechar menu" : "Abrir menu"}
            className="md:hidden"
          >
            <HugeiconsIcon
              icon={mobileMenuOpen ? Cancel01Icon : Menu01Icon}
              strokeWidth={2}
              className="size-5"
            />
          </Button>
        </div>
      </div>

      {/* Mobile menu drawer */}
      {mobileMenuOpen && (
        <div className="border-t border-border bg-background px-3 py-4 md:hidden">
          <nav className="flex flex-col gap-1">
            {navLinks.map(({ to, label, icon: Icon }) => (
              <Link
                key={to}
                to={to}
                onClick={() => setMobileMenuOpen(false)}
                className="block"
              >
                <Button
                  variant={location.pathname === to ? "default" : "ghost"}
                  size="sm"
                  className="w-full justify-start"
                >
                  {Icon && (
                    <HugeiconsIcon icon={Icon} strokeWidth={2} className="size-4" />
                  )}
                  {label}
                </Button>
              </Link>
            ))}
          </nav>
          <div className="mt-4 flex flex-col gap-2 border-t border-border pt-4">
            {(usernameProp !== undefined || usernameContext !== null) && (
              <p className="text-sm text-muted-foreground">
                Bem-vindo, <strong className="text-foreground">{username || "…"}</strong>
              </p>
            )}
            {onLogout && (
              <Button
                variant="secondary"
                className="w-full justify-center md:hidden"
                onClick={() => {
                  setMobileMenuOpen(false)
                  onLogout()
                }}
              >
                <HugeiconsIcon icon={LogoutIcon} strokeWidth={2} className="size-4" />
                Sair
              </Button>
            )}
          </div>
        </div>
      )}
    </header>
  )
}
