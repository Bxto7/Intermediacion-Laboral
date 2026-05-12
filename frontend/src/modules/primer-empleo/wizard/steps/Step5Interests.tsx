import { useState } from 'react'
import { useIntl } from 'react-intl'
import { useWizardStore } from '../../../../store/wizardStore'
import { WizardNavigation } from '../WizardNavigation'
import apiClient from '../../../../api/client'

const SECTORS = [
  { value: 'Comercio y ventas', emoji: '🛒' },
  { value: 'Administración', emoji: '📋' },
  { value: 'Salud y cuidados', emoji: '🏥' },
  { value: 'Educación', emoji: '📚' },
  { value: 'Tecnología', emoji: '💻' },
  { value: 'Gastronomía', emoji: '🍳' },
  { value: 'Construcción', emoji: '🏗️' },
  { value: 'Transporte y logística', emoji: '🚚' },
  { value: 'Agricultura', emoji: '🌾' },
  { value: 'Turismo y hotelería', emoji: '🏨' },
  { value: 'Manufactura', emoji: '🏭' },
  { value: 'Servicios generales', emoji: '🧹' },
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
        <h2 className="text-2xl font-bold text-gray-900">{intl.formatMessage({ id: 'wizard.step5.title' })}</h2>
        <p className="text-gray-500 text-sm mt-1">
          {intl.formatMessage({ id: 'wizard.step5.subtitle' })}
          <span className="text-primary-600 font-medium"> (elige hasta 3)</span>
        </p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {SECTORS.map((s) => (
          <button
            key={s.value}
            onClick={() => toggle(s.value)}
            className={`flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all ${
              selected.includes(s.value)
                ? 'border-primary-500 bg-primary-50 shadow-md'
                : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
            }`}
          >
            <span className="text-2xl">{s.emoji}</span>
            <span className="text-xs font-medium text-gray-700 text-center leading-tight">{s.value}</span>
          </button>
        ))}
      </div>

      {selected.length > 0 && (
        <div className="bg-primary-50 border border-primary-200 rounded-xl px-4 py-3 text-sm text-primary-700">
          <strong>Seleccionado:</strong> {selected.join(' · ')}
        </div>
      )}

      <WizardNavigation step={5} onNext={onNext} disabled={selected.length === 0} />
    </div>
  )
}
