import { createContext, useContext, useState, useCallback, useRef, useEffect } from "react"
import { useLocation } from "react-router-dom"

const AUTH_ROUTES = ["/dashboard", "/files", "/terminal", "/colorir", "/mistura", "/wifi"]

interface AuthContextValue {
  username: string | null
  setUsername: (username: string | null) => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const location = useLocation()
  const [username, setUsernameState] = useState<string | null>(null)
  const hasFetchedRef = useRef(false)

  const setUsername = useCallback((value: string | null) => {
    setUsernameState(value)
    if (!value) hasFetchedRef.current = false
  }, [])

  useEffect(() => {
    const isAuthRoute = AUTH_ROUTES.some((route) => location.pathname === route)
    if (!isAuthRoute || hasFetchedRef.current) return

    hasFetchedRef.current = true
    fetch("/api/me", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data?.username) setUsernameState(data.username)
        else hasFetchedRef.current = false
      })
      .catch(() => {
        hasFetchedRef.current = false
      })
  }, [location.pathname])

  return (
    <AuthContext.Provider value={{ username, setUsername }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within AuthProvider")
  return ctx
}
