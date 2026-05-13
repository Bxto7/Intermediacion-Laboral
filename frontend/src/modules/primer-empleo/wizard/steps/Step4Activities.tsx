import { useState } from 'react'
import { useIntl } from 'react-intl'
import { Plus, X } from 'lucide-react'
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
        <h2 className="text-2xl font-bold" style={{ color: 'var(--ink-strong)' }}>
          {intl.formatMessage({ id: 'wizard.step4.title' })}
        </h2>
        <p className="text-sm mt-1" style={{ color: 'var(--ink-muted)' }}>
          {intl.formatMessage({ id: 'wizard.step4.subtitle' })}
        </p>
      </div>

      <div className="space-y-2">
        {SUGGESTIONS.map((s) => {
          const active = activities.includes(s)
          return (
            <button
              key={s}
              onClick={() => toggle(s)}
              className="w-full text-left px-4 py-3 rounded-xl text-sm font-medium flex items-center gap-3 transition-all"
              style={{
                border: `2px solid ${active ? 'var(--terra-500)' : 'var(--line)'}`,
                background: active ? 'var(--terra-100)' : 'var(--bg-elevated)',
                color: active ? 'var(--terra-700)' : 'var(--ink-warm)',
              }}
            >
              <span
                className="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 transition-all"
                style={{
                  border: `2px solid ${active ? 'var(--terra-500)' : 'rgba(61,40,24,0.18)'}`,
                  background: active ? 'var(--terra-500)' : 'transparent',
                }}
              >
                {active && <span className="text-white text-xs font-bold">✓</span>}
              </span>
              {s}
            </button>
          )
        })}
      </div>

      <div className="flex gap-2">
        <input
          value={custom}
          onChange={(e) => setCustom(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && addCustom()}
          placeholder="Otra actividad que hayas hecho..."
          className="flex-1 rounded-xl text-sm focus:outline-none"
          style={{ border: '1px solid rgba(61,40,24,0.14)', background: 'var(--bg-soft)', color: 'var(--ink-strong)', padding: '10px 14px' }}
          onFocus={e => { e.currentTarget.style.borderColor = 'var(--terra-500)'; e.currentTarget.style.boxShadow = '0 0 0 3px rgba(194,86,46,0.12)' }}
          onBlur={e => { e.currentTarget.style.borderColor = 'rgba(61,40,24,0.14)'; e.currentTarget.style.boxShadow = 'none' }}
        />
        <button
          onClick={addCustom}
          className="btn-primary px-4 py-2.5"
        >
          <Plus size={16} />
        </button>
      </div>

      {activities.filter((a) => !SUGGESTIONS.includes(a)).map((a) => (
        <div
          key={a}
          className="flex items-center gap-2 px-3 py-2 rounded-xl text-sm"
          style={{ background: 'var(--bg-soft)', border: '1px solid var(--line)' }}
        >
          <span className="flex-1" style={{ color: 'var(--ink-warm)' }}>{a}</span>
          <button
            onClick={() => toggle(a)}
            className="transition-colors"
            style={{ color: 'var(--ink-muted)' }}
            onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.color = 'var(--terra-500)' }}
            onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.color = 'var(--ink-muted)' }}
          >
            <X size={14} />
          </button>
        </div>
      ))}

      <WizardNavigation step={4} onNext={onNext} />
    </div>
  )
}
