import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { useIntl } from 'react-intl'
import { Link, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { useAuthContext } from '../context/AuthContext'
import { LinkuLogoFull } from '../shared/LinkuLogo'

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
})
type FormData = z.infer<typeof schema>

export const LoginPage: React.FC = () => {
  const intl = useIntl()
  const navigate = useNavigate()
  const { login } = useAuthContext()
  const [error, setError] = useState('')
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data: FormData) => {
    setError('')
    try {
      await login(data.email, data.password)
      navigate('/dashboard')
    } catch {
      setError(intl.formatMessage({ id: 'auth.login.error' }))
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 lg:p-8 relative">
      <div className="w-full max-w-5xl mx-auto flex rounded-3xl overflow-hidden shadow-warm-lg"
           style={{ minHeight: '600px', background: 'rgba(255,255,255,0.65)', backdropFilter: 'blur(12px)', border: '1px solid rgba(255,255,255,0.6)' }}>
        
        {/* Lado izquierdo - Visual / Branding */}
        <div className="hidden lg:flex lg:w-[48%] flex-col justify-between p-12 relative overflow-hidden"
             style={{ background: 'linear-gradient(160deg, #fdf6ea 0%, #f7ecd8 55%, #f0e0c4 100%)' }}>
          
          {/* Radial Glows */}
          <div className="absolute top-0 left-0 w-48 h-48 rounded-full opacity-30 blur-3xl pointer-events-none" style={{ background: '#e8b45a' }} />
          <div className="absolute top-0 right-0 w-40 h-40 rounded-full opacity-20 blur-3xl pointer-events-none" style={{ background: '#2d5a82' }} />
          <div className="absolute bottom-0 left-0 w-44 h-44 rounded-full opacity-25 blur-3xl pointer-events-none" style={{ background: '#c2562e' }} />
          <div className="absolute bottom-0 right-0 w-36 h-36 rounded-full opacity-20 blur-3xl pointer-events-none" style={{ background: '#7a8c5c' }} />

          <div className="relative z-10">
            <LinkuLogoFull size={36} variant="default" />
          </div>

          <div className="relative z-10 space-y-6">
            <h2 className="text-4xl font-bold leading-tight" style={{ color: '#3d2818', letterSpacing: '-0.03em' }}>
              Tu próximo empleo{' '}
              <span style={{ fontFamily: 'Instrument Serif, Georgia, serif', fontStyle: 'italic', color: '#c2562e' }}>
                te espera.
              </span>
            </h2>
            <p className="text-base leading-relaxed" style={{ color: '#6b4a35' }}>
              La plataforma oficial de la región. Crea tu perfil en minutos y conéctate con empleos verificados.
            </p>
            <div className="space-y-3">
              {[
                { dot: '#c2562e', text: 'CV automático con IA' },
                { dot: '#2d5a82', text: 'Ofertas formales verificadas' },
                { dot: '#7a8c5c', text: 'Conexión directa y gratuita' },
              ].map((f) => (
                <div key={f.text} className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: f.dot }} />
                  <span className="text-sm font-medium" style={{ color: '#5a3d2b' }}>{f.text}</span>
                </div>
              ))}
            </div>
          </div>

          <p className="relative z-10 text-xs font-mono tracking-widest uppercase" style={{ color: '#8a6648' }}>
            Huancayo, Perú · 2026
          </p>
        </div>

        {/* Lado derecho - Formulario */}
        <div className="flex-1 flex flex-col justify-center p-8 sm:p-12 lg:p-16 relative z-10" style={{ background: 'var(--bg-base)' }}>
          <div className="max-w-sm mx-auto w-full space-y-8">
            <div className="space-y-2">
              <h1 className="text-3xl font-bold" style={{ color: '#3d2818', letterSpacing: '-0.03em' }}>
                {intl.formatMessage({ id: 'auth.login.title' })}
              </h1>
              <p style={{ color: '#8a6648' }}>Ingresa a tu cuenta para continuar</p>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
              <div className="space-y-1.5">
                <label className="block text-sm font-semibold" style={{ color: '#5a3d2b' }}>
                  {intl.formatMessage({ id: 'auth.login.email' })}
                </label>
                <input
                  {...register('email')}
                  id="login-email"
                  type="email"
                  autoComplete="email"
                  className="input-warm"
                  placeholder="tu@correo.com"
                />
                {errors.email && <p className="text-xs" style={{ color: 'var(--terra-500)' }}>{errors.email.message}</p>}
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between items-center">
                  <label className="block text-sm font-semibold" style={{ color: '#5a3d2b' }}>
                    {intl.formatMessage({ id: 'auth.login.password' })}
                  </label>
                  <a href="#" className="text-xs" style={{ color: '#c2562e' }}>¿Olvidaste tu contraseña?</a>
                </div>
                <input
                  {...register('password')}
                  id="login-password"
                  type="password"
                  autoComplete="current-password"
                  className="input-warm"
                  placeholder="••••••••"
                />
              </div>

              {error && (
                <div className="flex items-start gap-3 px-4 py-3 rounded-xl" style={{ background: 'rgba(194,86,46,0.08)', border: '1px solid rgba(194,86,46,0.20)' }}>
                  <svg className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: 'var(--terra-500)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-sm" style={{ color: 'var(--terra-700)' }}>{error}</p>
                </div>
              )}

              <button
                id="login-submit"
                type="submit"
                disabled={isSubmitting}
                className="btn-primary w-full py-3.5 text-base"
              >
                {isSubmitting ? (
                  <span className="flex items-center gap-2 justify-center">
                    <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                    </svg>
                    {intl.formatMessage({ id: 'common.loading' })}
                  </span>
                ) : intl.formatMessage({ id: 'auth.login.submit' })}
              </button>
            </form>

            <p className="text-center text-sm" style={{ color: '#8a6648' }}>
              ¿No tienes cuenta?{' '}
              <Link to="/register" className="font-semibold transition-colors hover:text-opacity-80" style={{ color: '#c2562e' }}>
                Regístrate gratis
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
