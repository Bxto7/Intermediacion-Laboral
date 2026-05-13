import { useState } from 'react'
import { CheckCircle, AlertCircle } from 'lucide-react'
import { useWorkerContext } from '../context/WorkerContext'
import apiClient from '../api/client'

const EMPLOYMENT_TYPES = [
  'dependiente_formal',
  'dependiente_informal',
  'independiente',
  'temporal',
  'practicante',
  'otro',
]

const EMPLOYMENT_LABELS: Record<string, string> = {
  dependiente_formal:   'Dependiente formal (planilla)',
  dependiente_informal: 'Dependiente informal (sin contrato)',
  independiente:        'Independiente / por cuenta propia',
  temporal:             'Trabajo temporal / eventual',
  practicante:          'Practicante / pasantía',
  otro:                 'Otro',
}

const fieldStyle = {
  border: '1px solid rgba(61,40,24,0.14)',
  background: 'var(--bg-soft)',
  color: 'var(--ink-strong)',
  borderRadius: '12px',
  fontSize: '14px',
  outline: 'none',
  width: '100%',
}

export const EconomicSurveyPage: React.FC = () => {
  const { worker } = useWorkerContext()
  const [phase, setPhase] = useState<'pre' | 'post'>('pre')
  const [income, setIncome] = useState('')
  const [employmentType, setEmploymentType] = useState('')
  const [consent, setConsent] = useState(false)
  const [saving, setSaving] = useState(false)
  const [done, setDone] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (!worker?.id) { setError('Perfil no encontrado'); return }
    if (!income || Number(income) <= 0) { setError('Ingresa un ingreso mensual válido'); return }
    if (!employmentType) { setError('Selecciona el tipo de empleo'); return }
    if (!consent) { setError('Debes aceptar el consentimiento informado para continuar'); return }

    setSaving(true)
    try {
      await apiClient.post('/surveys/economic', {
        worker_id: worker.id,
        survey_phase: phase,
        monthly_income: parseFloat(income),
        employment_type: employmentType,
        consent_given: consent,
      })
      setDone(true)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg || 'Error al enviar la encuesta. Intenta de nuevo.')
    } finally {
      setSaving(false)
    }
  }

  const onFocus = (e: React.FocusEvent<HTMLInputElement | HTMLSelectElement>) => {
    e.currentTarget.style.borderColor = 'var(--terra-500)'
    e.currentTarget.style.boxShadow = '0 0 0 3px rgba(194,86,46,0.12)'
  }
  const onBlur = (e: React.FocusEvent<HTMLInputElement | HTMLSelectElement>) => {
    e.currentTarget.style.borderColor = 'rgba(61,40,24,0.14)'
    e.currentTarget.style.boxShadow = 'none'
  }

  return (
    <div className="max-w-lg mx-auto py-4 space-y-4">
        <div className="mb-6">
          <h1 className="text-xl font-bold" style={{ color: 'var(--ink-strong)' }}>Encuesta económica</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--ink-muted)' }}>
            Tus datos nos ayudan a medir el impacto real de la plataforma en tu situación laboral.
          </p>
        </div>

        {done ? (
          <div className="card-warm p-8 text-center">
            <div className="w-14 h-14 rounded-2xl mx-auto mb-4 flex items-center justify-center" style={{ background: 'var(--olive-100)' }}>
              <CheckCircle size={26} style={{ color: 'var(--olive-deep)' }} />
            </div>
            <h2 className="font-bold mb-1" style={{ color: 'var(--ink-strong)' }}>¡Gracias por participar!</h2>
            <p className="text-sm" style={{ color: 'var(--ink-muted)' }}>
              Tu encuesta {phase === 'pre' ? 'pre-inserción' : 'post-inserción'} fue registrada correctamente.
            </p>
            <button
              onClick={() => { setDone(false); setIncome(''); setEmploymentType(''); setConsent(false) }}
              className="mt-5 text-sm font-medium transition-colors"
              style={{ color: 'var(--terra-500)' }}
            >
              Completar otra fase
            </button>
          </div>
        ) : (
          <form onSubmit={submit} className="card-warm p-6 space-y-5">
            {/* Fase */}
            <div>
              <label className="block text-xs font-semibold mb-2" style={{ color: 'var(--ink-warm)' }}>Fase de la encuesta *</label>
              <div className="grid grid-cols-2 gap-3">
                {(['pre', 'post'] as const).map(p => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => setPhase(p)}
                    className="py-3 rounded-xl text-sm font-semibold transition-all"
                    style={{
                      border: `2px solid ${phase === p ? 'var(--terra-500)' : 'var(--line)'}`,
                      background: phase === p ? 'var(--terra-100)' : 'var(--bg-elevated)',
                      color: phase === p ? 'var(--terra-700)' : 'var(--ink-muted)',
                    }}
                  >
                    {p === 'pre' ? 'Pre-inserción' : 'Post-inserción'}
                    <span className="block text-xs font-normal mt-0.5 opacity-70">
                      {p === 'pre' ? 'Antes de conseguir empleo' : 'Después de conseguir empleo'}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* Ingreso mensual */}
            <div>
              <label className="block text-xs font-semibold mb-1.5" style={{ color: 'var(--ink-warm)' }}>
                Ingreso mensual aproximado (S/.) *
              </label>
              <div className="relative">
                <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-sm font-medium pointer-events-none" style={{ color: 'var(--ink-muted)' }}>S/.</span>
                <input
                  type="number"
                  min="1"
                  step="1"
                  value={income}
                  onChange={e => setIncome(e.target.value)}
                  placeholder="0.00"
                  style={{ ...fieldStyle, paddingLeft: '40px', paddingRight: '16px', paddingTop: '12px', paddingBottom: '12px' }}
                  onFocus={onFocus}
                  onBlur={onBlur}
                />
              </div>
            </div>

            {/* Tipo de empleo */}
            <div>
              <label className="block text-xs font-semibold mb-1.5" style={{ color: 'var(--ink-warm)' }}>Tipo de empleo *</label>
              <select
                value={employmentType}
                onChange={e => setEmploymentType(e.target.value)}
                style={{ ...fieldStyle, padding: '12px' }}
                onFocus={onFocus}
                onBlur={onBlur}
              >
                <option value="">Seleccionar...</option>
                {EMPLOYMENT_TYPES.map(t => (
                  <option key={t} value={t}>{EMPLOYMENT_LABELS[t]}</option>
                ))}
              </select>
            </div>

            {/* Consentimiento */}
            <div
              className="rounded-xl p-4"
              style={{ background: 'var(--blue-100)', border: '1px solid rgba(45,90,130,0.15)' }}
            >
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={consent}
                  onChange={e => setConsent(e.target.checked)}
                  className="mt-0.5 w-4 h-4 rounded flex-shrink-0"
                  style={{ accentColor: 'var(--terra-500)' }}
                />
                <span className="text-xs leading-relaxed" style={{ color: 'var(--blue)' }}>
                  <strong>Consentimiento informado (Ley N° 29733)</strong> — Acepto que mis datos económicos sean
                  procesados de forma anónima con fines de investigación por la DRTPE-Junín y la Universidad Continental.
                  Mis datos personales no serán expuestos ni compartidos con terceros.
                </span>
              </label>
            </div>

            {error && (
              <div className="rounded-xl px-3 py-2.5 flex items-start gap-2" style={{ background: 'rgba(194,86,46,0.08)', border: '1px solid rgba(194,86,46,0.20)' }}>
                <AlertCircle size={14} className="flex-shrink-0 mt-0.5" style={{ color: 'var(--terra-500)' }} />
                <p className="text-xs" style={{ color: 'var(--terra-700)' }}>{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={saving}
              className="btn-primary w-full py-3.5 text-sm"
            >
              {saving ? 'Enviando...' : 'Enviar encuesta'}
            </button>
          </form>
        )}
    </div>
  )
}
