import axios from "axios"

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1"

const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token")
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

const authErrorMessages: Record<string, string> = {
  "Invalid credentials": "Wrong email or password. Please check and try again.",
  "Email already registered": "An account with this email already exists.",
  "Rate limited": "Rate limited: 60 requests/min. Please wait.",
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (error.response?.status === 429) {
      // Rate limit — surface quickly; UI can show specific message
      error.message = "Rate limited: 60 requests/min. Please wait."
    }
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      const refreshToken = localStorage.getItem("refresh_token")
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          })
          localStorage.setItem("access_token", data.access_token)
          if (data.refresh_token) {
            localStorage.setItem("refresh_token", data.refresh_token)
          }
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`
          return api(originalRequest)
        } catch {
          localStorage.removeItem("access_token")
          localStorage.removeItem("refresh_token")
          localStorage.removeItem("user")
          window.location.href = "/login"
        }
      } else {
        localStorage.removeItem("access_token")
        localStorage.removeItem("user")
        window.location.href = "/login"
      }
    }
    // Map backend auth error details to user-friendly messages
    if (error.response?.data?.detail) {
      const detail = String(error.response.data.detail)
      const mapped = authErrorMessages[detail] || detail
      error.message = mapped
    }
    return Promise.reject(error)
  },
)

export default api
