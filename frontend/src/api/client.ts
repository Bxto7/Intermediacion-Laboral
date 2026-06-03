import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
})

// Interceptor: adjuntar JWT en cada request
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Rutas públicas: no deben redirigir al login ante un 401
// (p. ej. la landing valida un token viejo en segundo plano)
const PUBLIC_PATHS = ['/', '/login', '/register', '/servicios']
const isPublicPath = (path: string) =>
  PUBLIC_PATHS.includes(path) || path.startsWith('/p/')

// Bandera de cierre de sesión voluntario: mientras está activa, el interceptor
// NO redirige a /login ante 401 (el logout decide a dónde ir → la landing).
let loggingOut = false
export const beginLogout = () => {
  loggingOut = true
  // se auto-restablece para no afectar futuros 401 por sesión expirada
  setTimeout(() => { loggingOut = false }, 4000)
}

// Interceptor: manejar 401 → limpiar sesión (y redirigir solo en rutas protegidas)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      if (!loggingOut && !isPublicPath(window.location.pathname)) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  },
)

export default apiClient
