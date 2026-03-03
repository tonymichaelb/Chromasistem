/**
 * Respostas mockadas para todas as APIs quando MOCK=true.
 * Usado para testar o front (UI/UX) sem o backend.
 */

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function getPath(url: string): string {
  try {
    const u = typeof url === "string" ? url : url
    return new URL(u, "http://x").pathname
  } catch {
    return url
  }
}

const defaultPrinterStatus = {
  connected: false,
  state: "idle" as const,
  temperature: {
    nozzle: 22,
    bed: 25,
    target_nozzle: 0,
    target_bed: 0,
  },
  filename: "",
  progress: 0,
  time_elapsed: "00:00:00",
  time_remaining: "00:00:00",
  filament: { sensor_enabled: false },
  failure_detected: false,
  failure_message: null as string | null,
  failure_code: null as string | null,
  skipped_objects_count: 0,
}

/** Status mock com falha (para testar UI de detecção de falhas). Troque no getMockResponse se quiser simular falha. */
const printerStatusWithFailure = {
  ...defaultPrinterStatus,
  state: "failure" as const,
  connected: true,
  filename: "modelo.gcode",
  progress: 35,
  failure_detected: true,
  failure_message: "Filamento travado ou defeito detectado.",
  failure_code: "ERR_001",
  skipped_objects_count: 1,
}

const defaultFilesList: Array<{
  id: number
  name: string
  size: number
  uploaded: string
  last_printed: string | null
  print_count: number
  thumbnail: string | null
  print_time: string | null
  filament_used: number | null
  filament_type: string | null
  nozzle_temp: number | null
  bed_temp: number | null
  layer_height: number | null
  infill: number | null
}> = [
  {
    id: 1,
    name: "exemplo.gcode",
    size: 1024000,
    uploaded: new Date().toISOString(),
    last_printed: null,
    print_count: 0,
    thumbnail: null,
    print_time: "2h 30m",
    filament_used: 50,
    filament_type: "PLA",
    nozzle_temp: 210,
    bed_temp: 60,
    layer_height: 0.2,
    infill: 20,
  },
]

function defaultBrushMixtures() {
  const mixtures: Record<string, { a: number; b: number; c: number }> = {}
  for (let i = 0; i < 19; i++) mixtures[String(i)] = { a: 33, b: 33, c: 34 }
  return { mixtures, colors: {} as Record<string, string>, tintaColors: {} as Record<string, string> }
}

const wifiNetworksMock = [
  { ssid: "Rede-Mock-1", signal: 85, security: "WPA2" },
  { ssid: "Rede-Mock-2", signal: 60, security: "WPA2" },
]

export function getMockResponse(input: RequestInfo | URL, init?: RequestInit): Response | null {
  const path = getPath(typeof input === "string" ? input : input instanceof URL ? input.href : input.url)
  const method = (init?.method ?? "GET").toUpperCase()

  // Auth
  if (path === "/api/version") return jsonResponse({ version: "1.0.0-mock" })
  if (path === "/api/login" && method === "POST") return jsonResponse({ success: true, message: "OK" })
  if (path === "/api/register" && method === "POST") return jsonResponse({ success: true })
  if (path === "/api/me") return jsonResponse({ success: true, username: "dev" })
  if (path === "/api/logout" && method === "POST") return jsonResponse({})

  // Printer
  if (path === "/api/printer/status") return jsonResponse({ success: true, status: printerStatusWithFailure })
  if (path === "/api/printer/connect" && method === "POST") return jsonResponse({ success: true })
  if (path === "/api/printer/disconnect" && method === "POST") return jsonResponse({ success: true })
  if (path === "/api/printer/start" && method === "POST") return jsonResponse({ success: true })
  if (path === "/api/printer/pause" && method === "POST") return jsonResponse({ success: true })
  if (path === "/api/printer/resume" && method === "POST") return jsonResponse({ success: true })
  if (path === "/api/printer/stop" && method === "POST") return jsonResponse({ success: true })
  // Detecção de falhas e skip (Task 4)
  if (path === "/api/printer/failure" && method === "POST") return jsonResponse({ success: true, message: "Falha registrada; aguardando ação" })
  if (path === "/api/printer/failure/resolve" && method === "POST") return jsonResponse({ success: true, message: "Aguardando problema resolvido" })
  if (path === "/api/printer/failure/resolved" && method === "POST") return jsonResponse({ success: true, message: "Problema resolvido; retomando impressão" })
  if (path === "/api/printer/skip-object" && method === "POST") return jsonResponse({ success: true, message: "Pulando item; impressão continuará no próximo objeto" })
  if (path === "/api/printer/failure-history") {
    return jsonResponse({
      success: true,
      entries: [
        { id: 1, print_job_id: 1, occurred_at: new Date().toISOString(), failure_code: "ERR_001", failure_message: "Filamento travado.", action: "skipped", object_index_or_name: "0" },
        { id: 2, print_job_id: 1, occurred_at: new Date(Date.now() - 3600000).toISOString(), failure_code: null, failure_message: "Falha detectada na impressão", action: "detected", object_index_or_name: null },
      ],
    })
  }
  if (path === "/api/printer/bed-preview") {
    return jsonResponse({
      success: true,
      bed: { width_mm: 220, depth_mm: 220 },
      objects: [
        { id: 0, name: "Peça 1", min_x: 20, min_y: 20, max_x: 60, max_y: 60 },
        { id: 1, name: "Peça 2", min_x: 80, min_y: 20, max_x: 120, max_y: 60 },
        { id: 2, name: "Peça 3", min_x: 140, min_y: 20, max_x: 180, max_y: 60 },
      ],
    })
  }
  if (path === "/api/printer/current-brush") return jsonResponse({ success: true, brush: 0 })
  if (path === "/api/printer/load-brush-mixtures") return jsonResponse({ success: true, ...defaultBrushMixtures() })
  if (path === "/api/printer/select-brush" && method === "POST") return jsonResponse({ success: true })
  if (path === "/api/printer/send-mixture" && method === "POST") return jsonResponse({ success: true })
  if (path === "/api/printer/save-brush-mixtures" && method === "POST") return jsonResponse({ success: true })
  if (path === "/api/printer/gcode" && method === "POST") return jsonResponse({ success: true, response: "ok" })
  if (path === "/api/printer/commands-history") return jsonResponse({ success: true, history: [], count: 0 })

  // Files
  if (path === "/api/files/list") return jsonResponse({ success: true, files: defaultFilesList })
  if (path === "/api/files/upload" && method === "POST") return jsonResponse({ success: true })
  const deleteMatch = path.match(/^\/api\/files\/delete\/(\d+)$/)
  if (deleteMatch && method === "DELETE") return jsonResponse({ success: true })
  const printMatch = path.match(/^\/api\/files\/print\/(\d+)$/)
  if (printMatch && method === "POST") return jsonResponse({ success: true, message: "Impressão iniciada" })

  // Wi-Fi
  if (path === "/api/wifi/status") return jsonResponse({ success: true, status: { connected: true, ssid: "Rede-Mock-1", ip: "192.168.1.100", is_hotspot: false } })
  if (path === "/api/wifi/saved") return jsonResponse({ success: true, networks: ["Rede-Mock-1"] })
  if (path === "/api/wifi/scan") return jsonResponse({ success: true, networks: wifiNetworksMock })
  if (path === "/api/wifi/connect" && method === "POST") return jsonResponse({ success: true })
  if (path === "/api/wifi/forget" && method === "POST") return jsonResponse({ success: true })

  return null
}
