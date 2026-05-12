import { useState } from 'react'
import { useIntl } from 'react-intl'
import { useWizardStore } from '../../../../store/wizardStore'
import { WizardNavigation } from '../WizardNavigation'
import apiClient from '../../../../api/client'

const SUGGESTIONS = [
  'Ayudé en el negocio familiar',
  'Voluntariado en la comunidad',
  'Proyectos escolares de equipo',
  'Cuidé a familiares menores',
  'Participé en actividades deportivas',
  'Organicé eventos del colegio',
]

export const Step4Activities: React.FC = () => {
  const intl = useIntl()
  const { answers, setAnswer } = useWizardStore()
  const [activities, setActivities] = useState<string[]>(
    answers.activities?.map((a: { description: string }) => a.description) || []
  )
  const [custom, setCustom] = useState('')

  const toggle = (item: string) => {
    setActivities((prev) =>
      prev.includes(item) ? prev.filter((a) => a !== item) : [...prev, item]
    )
  }

  const addCustom = () => {
    if (custom.trim() && !activities.includes(custom.trim())) {
      setActivities((prev) => [...prev, custom.trim()])
      setCustom('')
    }
  }

  const onNext = async () => {
    const actList = activities.map((d) => ({ description: d }))
    setAnswer('activities', actList)
    await apiClient.post('/wizard/step/4', { step: 4, answers: { activities: actList } }).catch(() => null)
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">{intl.formatMessage({ id: 'wizard.step4.title' })}</h2>
        <p className="text-gray-500 text-sm mt-1">{intl.formatMessage({ id: 'wizard.step4.subtitle' })}</p>
      </div>

      <div className="space-y-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => toggle(s)}
            className={`w-full text-left px-4 py-3 rounded-xl border-2 transition-all text-sm font-medium flex items-center gap-3 ${
              activities.includes(s)
                ? 'border-primary-500 bg-primary-50 text-primary-700'
                : 'border-gray-200 hover:border-gray-300 text-gray-600'
            }`}
          >
            <span className={`w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition-all ${
              activities.includes(s) ? 'border-primary-500 bg-primary-500' : 'border-gray-300'
            }`}>
              {activities.includes(s) && <span className="text-white text-xs">✓</span>}
            </span>
            {s}
          </button>
        ))}
      </div>

      <div className="flex gap-2">
        <input
          value={custom}
          onChange={(e) => setCustom(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && addCustom()}
          placeholder="Otra actividad que hayas hecho..."
          className="flex-1 px-3 py-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-primary-500 outline-none"
        />
        <button
          onClick={addCustom}
          className="px-4 py-2.5 bg-primary-600 text-white rounded-xl text-sm font-medium hover:bg-primary-700 transition-colors"
        >
          +
        </button>
      </div>

      {activities.filter((a) => !SUGGESTIONS.includes(a)).map((a) => (
        <div key={a} className="flex items-center gap-2 bg-gray-50 px-3 py-2 rounded-lg text-sm">
          <span className="flex-1 text-gray-700">{a}</span>
          <button onClick={() => toggle(a)} className="text-gray-400 hover:text-red-500">×</button>
        </div>
      ))}

      <WizardNavigation step={4} onNext={onNext} />
    </div>
  )
}
