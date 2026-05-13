import { useState } from 'react'
import { useIntl } from 'react-intl'
import { useWizardStore } from '../../../../store/wizardStore'
import { WizardNavigation } from '../WizardNavigation'
import apiClient from '../../../../api/client'

const SECTORS = [
  'Comercio y ventas',
  'Administración',
  'Salud y cuidados',
  'Educación',
  'Tecnología',
  'Gastronomía',
  'Construcción',
  'Transporte y logística',
  'Agricultura',
  'Turismo y hotelería',
  'Manufactura',
  'Servicios generales',
]

export const Step5Interests: React.FC = () => {
  const intl = useIntl()
  const { answers, setAnswer } = useWizardStore()
  const [selected, setSelected] = useState<string[]>(
    answers.job_interests ? [answers.job_interests] : []
  )

  const toggle = (val: string) => {
    setSelected((prev) =>
      prev.includes(val) ? prev.filter((s) => s !== val) : [...prev, val].slice(-3)
    )
  }

  const onNext = async () => {
    const interests = selected.join(', ')
    setAnswer('job_interests', interests)
    await apiClient.post('/wizard/step/5', { step: 5, answers: { job_interests: interests } }).catch(() => null)
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold" style={{ color: 'var(--ink-strong)' }}>
          {intl.formatMessage({ id: 'wizard.step5.title' })}
        </h2>
        <p className="text-sm mt-1" style={{ color: 'var(--ink-muted)' }}>
          {intl.formatMessage({ id: 'wizard.step5.subtitle' })}
          <span className="font-medium" style={{ color: 'var(--terra-500)' }}> (elige hasta 3)</span>
        </p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {SECTORS.map((s) => {
          const active = selected.includes(s)
          return (
            <button
              key={s}
              onClick={() => toggle(s)}
              className="p-3 rounded-xl text-sm font-medium text-center transition-all"
              style={{
                border: `2px solid ${active ? 'var(--terra-500)' : 'var(--line)'}`,
                background: active ? 'var(--terra-100)' : 'var(--bg-elevated)',
                color: active ? 'var(--terra-700)' : 'var(--ink-warm)',
              }}
            >
              {s}
            </button>
          )
        })}
      </div>

      {selected.length > 0 && (
        <div
          className="rounded-xl px-4 py-3 text-sm"
          style={{ background: 'var(--terra-100)', border: '1px solid rgba(194,86,46,0.20)' }}
        >
          <strong style={{ color: 'var(--terra-700)' }}>Seleccionado:</strong>{' '}
          <span style={{ color: 'var(--terra-500)' }}>{selected.join(' · ')}</span>
        </div>
      )}

      <WizardNavigation step={5} onNext={onNext} disabled={selected.length === 0} />
    </div>
  )
}
