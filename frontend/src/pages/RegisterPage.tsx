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
  password: z.string().min(8),
  dni: z.string().length(8),
  fullName: z.string().min(2),
  role: z.enum(['worker', 'employer', 'admin']).default('worker')
})
type FormData = z.infer<typeof schema>

export const RegisterPage: React.FC = () => {
  const intl = useIntl()
  const navigate = useNavigate()
  const { register: registerUser } = useAuthContext()
  const [error, setError] = useState('')
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { role: 'worker' }
  })

  const onSubmit = async (data: FormData) => {
    setError('')
    try {
      await registerUser({
        email: data.email,
        password: data.password,
        role: data.role as 'worker' | 'employer',
      })
      navigate('/onboarding')
    } catch {
      setError(intl.formatMessage({ id: 'auth.register.error' }))
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 lg:p-8 relative">
      <div className="w-full max-w-5xl mx-auto flex flex-row-reverse rounded-3xl overflow-hidden shadow-warm-lg"
           style={{ minHeight: '600px', background: 'rgba(255,255,255,0.65)', backdropFilter: 'blur(12px)', border: '1px solid rgba(255,255,255,0.6)' }}>
        
        {/* Lado derecho - Visual / Branding */}
        <div className="hidden lg:flex lg:w-[48%] flex-col justify-between p-12 relative overflow-hidden"
             style={{ background: 'var(--grad-auth)', position: 'relative', overflow: 'hidden' }}>

          {/* Glows de fondo */}
          <div className="absolute -top-20 -left-20 w-72 h-72 rounded-full opacity-20 blur-3xl pointer-events-none"
            style={{ background: 'var(--grad-glow-blue)' }} />
          <div className="absolute -bottom-20 -right-20 w-80 h-80 rounded-full opacity-15 blur-3xl pointer-events-none"
            style={{ background: 'var(--grad-glow-terra)' }} />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 rounded-full opacity-10 blur-3xl pointer-events-none"
            style={{ background: 'radial-gradient(ellipse, rgba(122,140,92,0.4) 0%, transparent 70%)' }} />
          {/* Grid de puntos decorativo */}
          <div className="absolute inset-0 opacity-5 pointer-events-none"
            style={{
              backgroundImage: 'radial-gradient(circle, rgba(255,255,255,0.6) 1px, transparent 1px)',
              backgroundSize: '28px 28px',
            }} />

          <div className="relative z-10">
            <LinkuLogoFull size={36} variant="white" />
          </div>

          <div className="relative z-10 space-y-6">
            <h2 className="text-4xl font-bold leading-tight text-white" style={{ letterSpacing: '-0.03em' }}>
              El trabajo que buscas está{' '}
              <span style={{ fontFamily: 'Instrument Serif, Georgia, serif', fontStyle: 'italic', color: '#8fb1d1' }}>
                aquí.
              </span>
            </h2>
            <p className="text-base leading-relaxed" style={{ color: 'rgba(255,255,255,0.8)' }}>
              Únete a más de 2,400 trabajadores que ya construyen su perfil profesional respaldado por la DRTPE.
            </p>
          </div>

          <p className="relative z-10 text-xs font-mono tracking-widest uppercase" style={{ color: 'rgba(255,255,255,0.4)' }}>
            Huancayo, Perú · 2026
          </p>
        </div>

        {/* Lado izquierdo - Formulario */}
        <div className="flex-1 flex flex-col justify-center p-8 sm:p-12 lg:p-16 relative z-10" style={{ background: 'var(--bg-base)' }}>
          <div className="max-w-sm mx-auto w-full space-y-8">
            <div className="space-y-2">
              <h1 className="text-3xl font-bold" style={{ color: '#3d2818', letterSpacing: '-0.03em' }}>
                {intl.formatMessage({ id: 'auth.register.title' })}
              </h1>
              <p style={{ color: '#785536' }}>Crea tu cuenta gratis en minutos</p>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="block text-sm font-semibold" style={{ color: '#5a3d2b' }}>DNI</label>
                  <input {...register('dni')} type="text" className="input-warm" placeholder="12345678" maxLength={8} />
                  {errors.dni && <p className="text-[10px]" style={{ color: 'var(--terra-500)' }}>{errors.dni.message}</p>}
                </div>
                <div className="space-y-1.5">
                  <label className="block text-sm font-semibold" style={{ color: '#5a3d2b' }}>Rol</label>
                  <select {...register('role')} className="input-warm">
                    <option value="worker">Trabajador</option>
                    <option value="employer">Empleador</option>
                  </select>
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="block text-sm font-semibold" style={{ color: '#5a3d2b' }}>
                  {intl.formatMessage({ id: 'auth.register.full_name' })}
                </label>
                <input {...register('fullName')} type="text" className="input-warm" placeholder="Juan Pérez" />
                {errors.fullName && <p className="text-xs" style={{ color: 'var(--terra-500)' }}>{errors.fullName.message}</p>}
              </div>

              <div className="space-y-1.5">
                <label className="block text-sm font-semibold" style={{ color: '#5a3d2b' }}>
                  {intl.formatMessage({ id: 'auth.register.email' })}
                </label>
                <input {...register('email')} type="email" className="input-warm" placeholder="tu@correo.com" />
                {errors.email && <p className="text-xs" style={{ color: 'var(--terra-500)' }}>{errors.email.message}</p>}
              </div>

              <div className="space-y-1.5">
                <label className="block text-sm font-semibold" style={{ color: '#5a3d2b' }}>
                  {intl.formatMessage({ id: 'auth.register.password' })}
                </label>
                <input {...register('password')} type="password" className="input-warm" placeholder="Mínimo 8 caracteres" />
                {errors.password && <p className="text-xs" style={{ color: 'var(--terra-500)' }}>{errors.password.message}</p>}
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
                type="submit"
                disabled={isSubmitting}
                className="btn-primary w-full py-3.5 text-base mt-2"
              >
                {isSubmitting ? (
                  <span className="flex items-center gap-2 justify-center">
                    <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                    </svg>
                    {intl.formatMessage({ id: 'common.loading' })}
                  </span>
                ) : intl.formatMessage({ id: 'auth.register.submit' })}
              </button>
            </form>

            <p className="text-center text-sm" style={{ color: '#785536' }}>
              ¿Ya tienes cuenta?{' '}
              <Link to="/login" className="font-semibold transition-colors hover:text-opacity-80" style={{ color: '#c2562e' }}>
                Iniciar sesión
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
