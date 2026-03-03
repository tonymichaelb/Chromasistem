import { StrictMode } from "react"
import { createRoot } from "react-dom/client"

import { setupMockFetch } from "@/mock/setup"
import "./index.css"
import App from "./App.tsx"

setupMockFetch()

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
)
