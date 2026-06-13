import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthContext } from '../../context/AuthContext'
import { LinkuLogoFull } from '../../shared/LinkuLogo'

interface Props { onClose: () => void; onSwitchToRegister: () => void }

export const LoginModal: React.FC<Props> = ({ onClose, onSwitchToRegister }) => {
  const { login } = useAuthContext()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(''); setLoading(true)
    try {
      await login(email, password)
      onClose()
      // Nunca regresar a una ruta pública tras el login (landing, servicios, etc.)
      const PUBLIC = ['/', '/login', '/register', '/servicios']
      let returnUrl = sessionStorage.getItem('login_return_url') || '/dashboard'
      sessionStorage.removeItem('login_return_url')
      if (PUBLIC.includes(returnUrl) || returnUrl.startsWith('/p/')) returnUrl = '/dashboard'
      navigate(returnUrl)
    } catch (err) {
      const status = (err as { response?: { status?: number } })?.response?.status
      setError(
        status === 401 ? 'Credenciales incorrectas. Intenta nuevamente.'
        : status === 429 ? 'Demasiados intentos. Espera unos minutos.'
        : 'No pudimos iniciar sesión. Intenta de nuevo en un momento.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="modal-backdrop fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(42,29,20,0.55)', backdropFilter: 'blur(6px)' }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div ref={ref} className="modal-panel w-full max-w-[880px] rounded-2xl overflow-hidden flex shadow-warm-lg" style={{ minHeight: 540 }}>

        {/* ── Panel izquierdo CLARO ── */}
        <div className="hidden md:flex md:w-[46%] flex-col justify-between p-10 relative overflow-hidden"
          style={{ background: 'linear-gradient(160deg, #f4ece0 0%, #f4ece0 55%, #ece0cf 100%)' }}>
          {/* Glows */}
          <div className="absolute top-0 left-0 w-48 h-48 rounded-full opacity-30 blur-3xl" style={{ background: '#eab84e' }} />
          <div className="absolute top-0 right-0 w-40 h-40 rounded-full opacity-20 blur-3xl" style={{ background: '#0f6e6e' }} />
          <div className="absolute bottom-0 left-0 w-44 h-44 rounded-full opacity-25 blur-3xl" style={{ background: '#b8442a' }} />
          <div className="absolute bottom-0 right-0 w-36 h-36 rounded-full opacity-20 blur-3xl" style={{ background: '#7a8c5c' }} />

          <div className="relative z-10">
            <LinkuLogoFull size={32} variant="default" />
          </div>

          <div className="relative z-10 space-y-5">
            <h2 className="text-3xl font-bold leading-tight" style={{ color: '#2a1d14', letterSpacing: '-0.03em' }}>
              Tu próximo empleo{' '}
              <span style={{ fontFamily: 'Instrument Serif, Georgia, serif', fontStyle: 'italic', color: '#b8442a' }}>
                te espera.
              </span>
            </h2>
            <p className="text-sm leading-relaxed" style={{ color: '#5a4a39' }}>
              La bolsa de empleo formal de la Dirección Regional de Trabajo de Junín. CV con IA, empleos verificados y matching inteligente.
            </p>
            <div className="space-y-2.5">
              {[
                { dot: '#b8442a', text: 'CV generado con inteligencia artificial' },
                { dot: '#0f6e6e', text: 'Empleos verificados por la DRTPE' },
                { dot: '#7a8c5c', text: 'Matching personalizado por ML' },
              ].map((f) => (
                <div key={f.text} className="flex items-center gap-3">
                  <div className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: f.dot }} />
                  <span className="text-xs" style={{ color: '#5a4a39' }}>{f.text}</span>
                </div>
              ))}
            </div>
          </div>

          <p className="relative z-10 text-xs" style={{ color: '#6e5d49' }}>Huancayo, Perú · 2026</p>
        </div>

        {/* ── Panel derecho — formulario ── */}
        <div className="flex-1 p-8 flex flex-col justify-center" style={{ background: 'var(--bg-base)' }}>
          <button onClick={onClose} className="absolute top-4 right-4 w-8 h-8 rounded-full flex items-center justify-center hover:bg-warm-200 transition-colors" style={{ color: '#6e5d49' }}>
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>

          <div className="max-w-sm mx-auto w-full space-y-7">
            <div>
              <h3 className="text-2xl font-bold" style={{ color: '#2a1d14', letterSpacing: '-0.03em' }}>Iniciar sesión</h3>
              <p className="text-sm mt-1" style={{ color: '#6e5d49' }}>Ingresa tus credenciales para continuar</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label className="block text-sm font-semibold" style={{ color: '#3f2c1d' }}>Correo electrónico</label>
                <input
                  type="email" value={email} onChange={e => setEmail(e.target.value)}
                  className="input-warm" placeholder="tu@correo.com" required
                />
              </div>
              <div className="space-y-1.5">
                <div className="flex justify-between">
                  <label className="block text-sm font-semibold" style={{ color: '#3f2c1d' }}>Contraseña</label>
                  <a href="#" className="text-xs" style={{ color: '#b8442a' }}>¿Olvidaste tu contraseña?</a>
                </div>
                <input
                  type="password" value={password} onChange={e => setPassword(e.target.value)}
                  className="input-warm" placeholder="••••••••" required
                />
              </div>

              {error && (
                <div className="flex gap-2 px-3 py-2.5 rounded-xl text-sm" style={{ background: '#fbeceb', border: '1px solid #f3d4d2', color: '#9e2b25' }}>
                  <svg className="w-4 h-4 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><circle cx="12" cy="12" r="10"/><path d="M12 8v4m0 4h.01"/></svg>
                  {error}
                </div>
              )}

              <button type="submit" disabled={loading} className="btn-primary w-full py-3">
                {loading ? (
                  <span className="flex items-center gap-2 justify-center">
                    <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/></svg>
                    Ingresando...
                  </span>
                ) : 'Ingresar'}
              </button>
            </form>

            <div className="flex items-center gap-3">
              <div className="flex-1 h-px" style={{ background: 'var(--bg-warm)' }} />
              <span className="text-xs" style={{ color: '#6e5d49' }}>o continúa con</span>
              <div className="flex-1 h-px" style={{ background: 'var(--bg-warm)' }} />
            </div>

            <div className="grid grid-cols-2 gap-3">
              {[
                { name: 'Google', icon: <svg className="w-4 h-4" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg> },
                { name: 'Facebook', icon: <svg className="w-4 h-4" viewBox="0 0 24 24" fill="#1877F2"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg> },
              ].map((s) => (
                <button key={s.name} className="flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-medium transition-all" style={{ background: 'white', border: '1px solid rgba(42,29,20,0.15)', color: '#3f2c1d' }}>
                  {s.icon} {s.name}
                </button>
              ))}
            </div>

            <p className="text-center text-sm" style={{ color: '#6e5d49' }}>
              ¿No tienes cuenta?{' '}
              <button type="button" onClick={onSwitchToRegister} className="font-semibold" style={{ color: '#b8442a' }}>Regístrate gratis</button>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
