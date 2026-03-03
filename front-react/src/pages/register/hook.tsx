import { useState } from "react"
import { useNavigate } from "react-router-dom"

interface RegisterResponse {
  success: boolean
  message: string
}

export function useRegister() {
  const navigate = useNavigate()
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [message, setMessage] = useState<{ text: string; type: "success" | "error" } | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setMessage(null)
    if (password !== confirmPassword) {
      setMessage({ text: "As senhas não coincidem", type: "error" })
      return
    }
    setLoading(true)
    try {
      const res = await fetch("/api/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
        credentials: "include",
      })
      const data: RegisterResponse = await res.json()
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
    confirmPassword,
    setConfirmPassword,
    showPassword,
    setShowPassword,
    showConfirmPassword,
    setShowConfirmPassword,
    message,
    loading,
    handleSubmit,
  }
}
