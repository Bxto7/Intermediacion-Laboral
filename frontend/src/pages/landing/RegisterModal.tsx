import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { useAuthContext } from '../../context/AuthContext'
import { parseApiError } from '../../lib/parseApiError'
import { LinkuLogoFull } from '../../shared/LinkuLogo'

interface Props { onClose: () => void; onSwitchToLogin: () => void }

const schema = z.object({
  email: z.string().email('Correo no válido'),
  password: z.string().min(8, 'Mínimo 8 caracteres'),
  dni: z.string().length(8, 'El DNI debe tener 8 dígitos'),
  fullName: z.string().min(2, 'Ingresa tu nombre'),
  role: z.enum(['worker', 'employer']).default('worker'),
})
type FormData = z.infer<typeof schema>

export const RegisterModal: React.FC<Props> = ({ onClose, onSwitchToLogin }) => {
  const { register: registerUser } = useAuthContext()
  const navigate = useNavigate()
  const [error, setError] = useState('')
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { role: 'worker' },
  })

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  const onSubmit = async (data: FormData) => {
    setError('')
    try {
      await registerUser({ email: data.email, password: data.password, role: data.role })
      onClose()
      navigate('/onboarding')
    } catch (err) {
      setError(parseApiError(err, 'No pudimos crear tu cuenta. Intenta de nuevo.'))
    }
  }

  return (
    <div
      className="modal-backdrop fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(42,29,20,0.55)', backdropFilter: 'blur(6px)' }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div className="modal-panel w-full max-w-[880px] rounded-2xl overflow-hidden flex shadow-warm-lg" style={{ minHeight: 560 }}>

        {/* ── Panel izquierdo CLARO ── */}
        <div className="hidden md:flex md:w-[46%] flex-col justify-between p-10 relative overflow-hidden"
          style={{ background: 'linear-gradient(160deg, #f4ece0 0%, #f4ece0 55%, #ece0cf 100%)' }}>
          <div className="absolute top-0 left-0 w-48 h-48 rounded-full opacity-30 blur-3xl" style={{ background: '#eab84e' }} />
          <div className="absolute top-0 right-0 w-40 h-40 rounded-full opacity-20 blur-3xl" style={{ background: '#0f6e6e' }} />
          <div className="absolute bottom-0 left-0 w-44 h-44 rounded-full opacity-25 blur-3xl" style={{ background: '#b8442a' }} />
          <div className="absolute bottom-0 right-0 w-36 h-36 rounded-full opacity-20 blur-3xl" style={{ background: '#7a8c5c' }} />

          <div className="relative z-10">
            <LinkuLogoFull size={32} variant="default" />
          </div>

          <div className="relative z-10 space-y-5">
            <h2 className="text-3xl font-bold leading-tight" style={{ color: '#2a1d14', letterSpacing: '-0.03em' }}>
              El trabajo que buscas{' '}
              <span style={{ fontFamily: 'Instrument Serif, Georgia, serif', fontStyle: 'italic', color: '#b8442a' }}>
                está aquí.
              </span>
            </h2>
            <p className="text-sm leading-relaxed" style={{ color: '#5a4a39' }}>
              Únete a la bolsa de empleo formal de la DRTPE-Junín. Crea tu perfil, genera tu CV con IA y conecta con empleos verificados.
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
        <div className="flex-1 p-8 flex flex-col justify-center relative" style={{ background: 'var(--bg-base)' }}>
          <button onClick={onClose} aria-label="Cerrar" className="absolute top-4 right-4 w-8 h-8 rounded-full flex items-center justify-center hover:bg-warm-200 transition-colors" style={{ color: '#6e5d49' }}>
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>

          <div className="max-w-sm mx-auto w-full space-y-5">
            <div>
              <h3 className="text-2xl font-bold" style={{ color: '#2a1d14', letterSpacing: '-0.03em' }}>Crear cuenta</h3>
              <p className="text-sm mt-1" style={{ color: '#6e5d49' }}>Crea tu cuenta gratis en minutos</p>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-3.5" noValidate>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="block text-sm font-semibold" style={{ color: '#3f2c1d' }}>DNI</label>
                  <input {...register('dni')} type="text" inputMode="numeric" maxLength={8} className="input-warm" placeholder="12345678" />
                  {errors.dni && <p className="text-[10px]" style={{ color: 'var(--terra-500)' }}>{errors.dni.message}</p>}
                </div>
                <div className="space-y-1.5">
                  <label className="block text-sm font-semibold" style={{ color: '#3f2c1d' }}>Rol</label>
                  <select {...register('role')} className="input-warm">
                    <option value="worker">Trabajador</option>
                    <option value="employer">Empleador</option>
                  </select>
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="block text-sm font-semibold" style={{ color: '#3f2c1d' }}>Nombre completo</label>
                <input {...register('fullName')} type="text" className="input-warm" placeholder="Juan Pérez" />
                {errors.fullName && <p className="text-xs" style={{ color: 'var(--terra-500)' }}>{errors.fullName.message}</p>}
              </div>

              <div className="space-y-1.5">
                <label className="block text-sm font-semibold" style={{ color: '#3f2c1d' }}>Correo electrónico</label>
                <input {...register('email')} type="email" className="input-warm" placeholder="tu@correo.com" />
                {errors.email && <p className="text-xs" style={{ color: 'var(--terra-500)' }}>{errors.email.message}</p>}
              </div>

              <div className="space-y-1.5">
                <label className="block text-sm font-semibold" style={{ color: '#3f2c1d' }}>Contraseña</label>
                <input {...register('password')} type="password" className="input-warm" placeholder="Mínimo 8 caracteres" />
                {errors.password && <p className="text-xs" style={{ color: 'var(--terra-500)' }}>{errors.password.message}</p>}
              </div>

              {error && (
                <div className="flex gap-2 px-3 py-2.5 rounded-xl text-sm" style={{ background: '#fbeceb', border: '1px solid #f3d4d2', color: '#9e2b25' }}>
                  <svg className="w-4 h-4 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><circle cx="12" cy="12" r="10"/><path d="M12 8v4m0 4h.01"/></svg>
                  {error}
                </div>
              )}

              <button type="submit" disabled={isSubmitting} className="btn-primary w-full py-3">
                {isSubmitting ? (
                  <span className="flex items-center gap-2 justify-center">
                    <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/></svg>
                    Creando cuenta...
                  </span>
                ) : 'Crear cuenta gratis'}
              </button>
            </form>

            <p className="text-center text-sm" style={{ color: '#6e5d49' }}>
              ¿Ya tienes cuenta?{' '}
              <button type="button" onClick={onSwitchToLogin} className="font-semibold" style={{ color: '#b8442a' }}>
                Inicia sesión
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
