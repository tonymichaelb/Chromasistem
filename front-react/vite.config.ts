import path from "path"
import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      "/api": {
        target: "http://127.0.0.1:80",
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on("proxyReq", (proxyReq) => {
            // Cookie de sessão do Flask deve ser para "localhost" para o browser enviar nas requisições de localhost:5173
            proxyReq.setHeader("Host", "localhost")
          })
        },
      },
      "/static": {
        target: "http://127.0.0.1:80",
        changeOrigin: true,
      },
    },
  },
})
