/**
 * Substitui window.fetch quando MOCK=true para retornar dados mockados em /api/*.
 * Chamado em main.tsx antes de renderizar o app.
 */
import { MOCK } from "@/config"
import { getMockResponse } from "./api"

export function setupMockFetch(): void {
  if (!MOCK || typeof window === "undefined") return

  const originalFetch = window.fetch
  window.fetch = function mockFetch(
    input: RequestInfo | URL,
    init?: RequestInit
  ): Promise<Response> {
    const mock = getMockResponse(input, init)
    if (mock !== null) return Promise.resolve(mock)
    return originalFetch.call(window, input, init)
  }
}
