import axios from "axios"

// Same-origin by default: the Vite dev server and the production nginx both
// proxy /api to the backend, so cookies just work and CORS is moot.
// VITE_API_URL remains available for direct-backend setups.
const API_URL = import.meta.env.VITE_API_URL || "/api/v1"
export const API_ORIGIN = API_URL.replace(/\/api\/v1\/?$/, "") || ""

const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
  withCredentials: true, // send/receive HttpOnly auth cookies
})

// CSRF guard: backend rejects state-changing requests from cookie sessions
// unless this custom header is present (cross-site attackers cannot set it).
api.interceptors.request.use((config) => {
  config.headers["X-Requested-With"] = "XMLHttpRequest"
  return config
})

const authErrorMessages: Record<string, string> = {
  "Invalid credentials": "Wrong email or password. Please check and try again.",
  "Email already registered": "An account with this email already exists.",
}

let refreshInFlight: Promise<unknown> | null = null

function singleFlightRefresh(): Promise<unknown> {
  // Backend rotates refresh cookies on every /auth/refresh call - N parallel
  // 401s would race each other over the rotated cookie. One shared promise.
  if (!refreshInFlight) {
    refreshInFlight = axios
      .post(`${API_URL}/auth/refresh`, null, { withCredentials: true })
      .finally(() => {
        refreshInFlight = null
      })
  }
  return refreshInFlight
}

function emitSessionExpired() {
  window.dispatchEvent(new CustomEvent("auth:expired"))
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (error.response?.status === 429) {
      error.message = "Rate limited: 60 requests/min. Please wait."
    }
    const isAuthEndpoint = originalRequest?.url?.startsWith("/auth/")
    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !isAuthEndpoint
    ) {
      originalRequest._retry = true
      try {
        await singleFlightRefresh()
        return api(originalRequest)
      } catch {
        // Session truly dead - let listeners clear caches and redirect.
        emitSessionExpired()
      }
    }
    if (error.response?.data?.detail) {
      const detail = String(error.response.data.detail)
      error.message = authErrorMessages[detail] || detail
    }
    return Promise.reject(error)
  },
)

export default api
