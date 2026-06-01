import { useState } from 'react'
import { CheckCircle, LogOut, Circle } from 'lucide-react'
import { useWorkerContext } from '../context/WorkerContext'
import { useAuthContext } from '../context/AuthContext'
import { useCompleteness } from '../hooks/useCompleteness'
import apiClient from '../api/client'

const DISTRICTS = ['Huancayo', 'El Tambo', 'Chilca']

const inputStyle: React.CSSProperties = {
  border: '1px solid var(--line-strong)',
  background: 'var(--bg-soft)',
  color: 'var(--ink-strong)',
  borderRadius: '12px',
  fontSize: '14px',
  padding: '10px 14px',
  width: '100%',
  outline: 'none',
}

export const SettingsPage: React.FC = () => {
  const { worker, refreshWorker } = useWorkerContext()
  const { user, logout } = useAuthContext()
  const { completeness } = useCompleteness(user?.role === 'worker')

  const [fullName, setFullName] = useState(worker?.full_name ?? worker?.display_name ?? '')
  const [district, setDistrict] = useState(worker?.district ?? '')
  const [jobTitle, setJobTitle] = useState(worker?.job_title ?? '')
  const [bio, setBio] = useState(worker?.bio ?? '')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  const onFocus = (e: React.FocusEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    e.currentTarget.style.borderColor = 'var(--terra-500)'
    e.currentTarget.style.boxShadow = '0 0 0 3px rgba(194,86,46,0.12)'
  }
  const onBlur = (e: React.FocusEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    e.currentTarget.style.borderColor = 'var(--line-strong)'
    e.currentTarget.style.boxShadow = 'none'
  }

  const save = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSaving(true)
    try {
      const patch: Record<string, unknown> = {}
      if (fullName.trim()) patch.full_name = fullName.trim()
      if (district)         patch.district = district
      if (jobTitle.trim())  patch.job_title = jobTitle.trim()
      if (bio.trim())       patch.bio = bio.trim()

      await apiClient.patch('/workers/me', patch)
      await refreshWorker()
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch {
      setError('No se pudo guardar. Intenta de nuevo.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="max-w-lg mx-auto space-y-5 py-2">
      <div>
        <h1 className="text-xl font-bold" style={{ color: 'var(--ink-strong)', letterSpacing: '-0.02em' }}>Configuración</h1>
        <p className="text-sm mt-0.5" style={{ color: 'var(--ink-muted)' }}>Gestiona tu cuenta y preferencias</p>
      </div>

      {/* Account info card */}
      <div className="card-warm p-5">
        <p className="kicker mb-3">Cuenta</p>
        <div className="flex items-center gap-3">
          <div
            className="w-12 h-12 rounded-xl flex items-center justify-center text-lg font-bold text-white flex-shrink-0"
            style={{ background: 'linear-gradient(135deg, var(--terra-400), var(--terra-500))' }}
          >
            {user?.email?.charAt(0).toUpperCase() ?? 'U'}
          </div>
          <div>
            <p className="font-semibold text-sm" style={{ color: 'var(--ink-strong)' }}>{user?.email}</p>
            <p className="text-xs mt-0.5 capitalize" style={{ color: 'var(--ink-muted)' }}>
              {user?.role === 'admin' ? 'Administrador DRTPE' : user?.role === 'employer' ? 'Empleador' : 'Trabajador'}
            </p>
          </div>
        </div>
      </div>

      {/* Profile settings — workers only */}
      {user?.role === 'worker' && (
        <form onSubmit={save} className="card-warm p-5 space-y-4">
          <p className="kicker mb-1">Perfil público</p>

          <div>
            <label htmlFor="settings-name" className="block text-xs font-semibold mb-1.5" style={{ color: 'var(--ink-warm)' }}>Nombre completo</label>
            <input
              id="settings-name"
              type="text"
              value={fullName}
              onChange={e => setFullName(e.target.value)}
              placeholder="Ej: Juan Pérez"
              maxLength={100}
              style={inputStyle}
              onFocus={onFocus}
              onBlur={onBlur}
            />
          </div>

          {(worker?.worker_type === 'experiencia' || worker?.worker_type === 'oficio') && (
            <div>
              <label htmlFor="settings-jobtitle" className="block text-xs font-semibold mb-1.5" style={{ color: 'var(--ink-warm)' }}>Título profesional</label>
              <input
                id="settings-jobtitle"
                type="text"
                value={jobTitle}
                onChange={e => setJobTitle(e.target.value)}
                placeholder="Ej: Electricista residencial"
                maxLength={100}
                style={inputStyle}
                onFocus={onFocus}
                onBlur={onBlur}
              />
            </div>
          )}

          <div>
            <label htmlFor="settings-district" className="block text-xs font-semibold mb-1.5" style={{ color: 'var(--ink-warm)' }}>Distrito</label>
            <select
              id="settings-district"
              value={district}
              onChange={e => setDistrict(e.target.value)}
              style={{ ...inputStyle, padding: '10px 14px' }}
              onFocus={onFocus}
              onBlur={onBlur}
            >
              <option value="">Seleccionar...</option>
              {DISTRICTS.map(d => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>

          <div>
            <label htmlFor="settings-bio" className="block text-xs font-semibold mb-1.5" style={{ color: 'var(--ink-warm)' }}>Descripción breve</label>
            <textarea
              id="settings-bio"
              value={bio}
              onChange={e => setBio(e.target.value)}
              placeholder="Cuéntanos sobre ti y tu experiencia..."
              maxLength={500}
              rows={3}
              style={{ ...inputStyle, resize: 'none' }}
              onFocus={onFocus}
              onBlur={onBlur}
            />
            <p className="text-[11px] mt-0.5 text-right" style={{ color: 'var(--ink-muted)' }}>{bio.length}/500</p>
          </div>

          {error && (
            <p role="alert" className="text-xs px-3 py-2 rounded-xl" style={{ background: 'rgba(194,86,46,0.08)', color: 'var(--terra-500)', border: '1px solid rgba(194,86,46,0.2)' }}>
              {error}
            </p>
          )}

          <button type="submit" disabled={saving} className="btn-primary w-full py-2.5 text-sm flex items-center justify-center gap-2">
            {saved
              ? <><CheckCircle size={15} /> Cambios guardados</>
              : saving ? 'Guardando...' : 'Guardar cambios'}
          </button>
        </form>
      )}

      {/* Profile completeness nudge — con detalle de lo que falta */}
      {user?.role === 'worker' && completeness && completeness.percentage < 100 && (
        <div
          className="rounded-2xl p-4"
          style={{ background: 'var(--terra-100)', border: '1px solid rgba(194,86,46,0.2)' }}
        >
          <div className="flex items-center gap-3">
            <div className="flex-1">
              <p className="text-xs font-semibold" style={{ color: 'var(--terra-700)' }}>
                Tu perfil está al {completeness.percentage}%
              </p>
              <p className="text-[11px] mt-0.5" style={{ color: 'var(--terra-500)' }}>
                {completeness.next_action || 'Complétalo para aparecer en más búsquedas'}
              </p>
            </div>
            <div className="w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0" style={{ background: 'var(--terra-500)', color: '#fff' }}>
              {completeness.percentage}%
            </div>
          </div>

          {completeness.missing_fields.length > 0 && (
            <div className="mt-3 pt-3 space-y-1.5" style={{ borderTop: '1px solid rgba(194,86,46,0.18)' }}>
              <p className="text-[11px] font-semibold" style={{ color: 'var(--terra-700)' }}>Para llegar al 100% te falta:</p>
              {completeness.missing_fields.map((item) => (
                <div key={item} className="flex items-center gap-2">
                  <Circle size={11} strokeWidth={2.5} style={{ color: 'var(--terra-500)' }} />
                  <span className="text-[11.5px]" style={{ color: 'var(--terra-700)' }}>{item}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Logout */}
      <div className="card-warm p-5">
        <p className="kicker mb-3">Sesión</p>
        <button
          onClick={() => logout()}
          className="w-full py-2.5 text-sm font-medium rounded-xl transition-all flex items-center justify-center gap-2"
          style={{ border: '1.5px solid rgba(194,86,46,0.25)', color: 'var(--terra-500)', background: 'transparent' }}
          onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'rgba(194,86,46,0.06)' }}
          onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'transparent' }}
        >
          <LogOut size={14} /> Cerrar sesión
        </button>
      </div>
    </div>
  )
}
