import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"

interface LoginResponse {
  success: boolean
  message: string
}

export function useLogin() {
  const navigate = useNavigate()
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [message, setMessage] = useState<{ text: string; type: "success" | "error" } | null>(null)
  const [loading, setLoading] = useState(false)
  const [version, setVersion] = useState<string | null>(null)

  useEffect(() => {
    fetch("/api/version", { credentials: "include" })
      .then((res) => res.json())
      .then((data) => setVersion(data.version ?? null))
      .catch(() => setVersion(null))
  }, [])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setMessage(null)
    setLoading(true)
    try {
      const res = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
        credentials: "include",
      })
      const data: LoginResponse = await res.json()
      if (data.success) {
        setMessage({ text: data.message, type: "success" })
        setTimeout(() => navigate("/dashboard"), 1000)
      } else {
        setMessage({ text: data.message, type: "error" })
      }
    } catch {
      setMessage({ text: "Erro ao conectar com o servidor", type: "error" })
    } finally {
      setLoading(false)
    }
  }

  return {
    username,
    setUsername,
    password,
    setPassword,
    showPassword,
    setShowPassword,
    message,
    loading,
    version,
    handleSubmit,
  }
}
