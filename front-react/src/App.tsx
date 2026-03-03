import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { AuthProvider } from "@/contexts/AuthContext"
import { Login } from "@/pages/login/Login"
import { Register } from "@/pages/register/Register"
import { Dashboard } from "@/pages/dashboard/Dashboard"
import { Files } from "@/pages/files/Files"
import { Terminal } from "@/pages/terminal/Terminal"
import { Colorir } from "@/pages/colorir/Colorir"
import { Mistura } from "@/pages/mistura/Mistura"
import { Wifi } from "@/pages/wifi/Wifi"
import { Fatiador } from "@/pages/fatiador/Fatiador"

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/files" element={<Files />} />
        <Route path="/fatiador" element={<Fatiador />} />
        <Route path="/terminal" element={<Terminal />} />
        <Route path="/colorir" element={<Colorir />} />
        <Route path="/mistura" element={<Mistura />} />
        <Route path="/wifi" element={<Wifi />} />
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
