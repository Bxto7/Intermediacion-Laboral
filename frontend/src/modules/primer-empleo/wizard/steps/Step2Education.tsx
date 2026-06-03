import { useState } from 'react'
import { useIntl } from 'react-intl'
import { Plus } from 'lucide-react'
import { useWizardStore } from '../../../../store/wizardStore'
import { WizardNavigation } from '../WizardNavigation'
import apiClient from '../../../../api/client'

const LEVELS = ['Primaria', 'Secundaria', 'Técnica', 'Universitaria', 'Sin estudios']

const fieldStyle = {
  border: '1px solid rgba(42,29,20,0.14)',
  background: 'var(--bg-soft)',
  color: 'var(--ink-strong)',
  borderRadius: '10px',
  fontSize: '14px',
  outline: 'none',
  width: '100%',
  padding: '8px 12px',
}

const onFocus = (e: React.FocusEvent<HTMLInputElement | HTMLSelectElement>) => {
  e.currentTarget.style.borderColor = 'var(--terra-500)'
  e.currentTarget.style.boxShadow = '0 0 0 3px rgba(184,68,42,0.12)'
}
const onBlur = (e: React.FocusEvent<HTMLInputElement | HTMLSelectElement>) => {
  e.currentTarget.style.borderColor = 'rgba(42,29,20,0.14)'
  e.currentTarget.style.boxShadow = 'none'
}

export const Step2Education: React.FC = () => {
  const intl = useIntl()
  const { answers, setAnswer } = useWizardStore()
  const [education, setEducation] = useState(answers.education || [{ institution: '', level: '', year: '' }])

  const update = (i: number, field: string, value: string) => {
    const updated = education.map((e, idx) => idx === i ? { ...e, [field]: value } : e)
    setEducation(updated)
    setAnswer('education', updated)
  }

  const onNext = async () => {
    setAnswer('education', education)
    await apiClient.post('/wizard/step/2', { step: 2, answers: { education } }).catch(() => null)
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold" style={{ color: 'var(--ink-strong)' }}>
          {intl.formatMessage({ id: 'wizard.step2.title' })}
        </h2>
        <p className="text-sm mt-1" style={{ color: 'var(--ink-muted)' }}>
          {intl.formatMessage({ id: 'wizard.step2.subtitle' })}
        </p>
      </div>

      {education.map((edu, i) => (
        <div key={i} className="rounded-xl p-4 space-y-3" style={{ background: 'var(--bg-soft)', border: '1px solid var(--line)' }}>
          <div>
            <label className="block text-xs font-medium mb-1" style={{ color: 'var(--ink-warm)' }}>Institución educativa</label>
            <input
              value={edu.institution}
              onChange={(e) => update(i, 'institution', e.target.value)}
              placeholder="Colegio, Instituto, Universidad..."
              style={fieldStyle}
              onFocus={onFocus}
              onBlur={onBlur}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium mb-1" style={{ color: 'var(--ink-warm)' }}>Nivel</label>
              <select
                value={edu.level}
                onChange={(e) => update(i, 'level', e.target.value)}
                style={fieldStyle}
                onFocus={onFocus}
                onBlur={onBlur}
              >
                <option value="">Seleccionar...</option>
                {LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium mb-1" style={{ color: 'var(--ink-warm)' }}>Año de egreso</label>
              <input
                type="number"
                value={edu.year}
                onChange={(e) => update(i, 'year', e.target.value)}
                placeholder="2023"
                min="1980"
                max={new Date().getFullYear()}
                style={fieldStyle}
                onFocus={onFocus}
                onBlur={onBlur}
              />
            </div>
          </div>
        </div>
      ))}

      <button
        onClick={() => setEducation([...education, { institution: '', level: '', year: '' }])}
        className="w-full py-2.5 text-sm font-medium rounded-xl flex items-center justify-center gap-2 transition-all"
        style={{ border: '2px dashed rgba(184,68,42,0.20)', color: 'var(--ink-muted)' }}
        onMouseEnter={e => {
          (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--terra-500)'
          ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--terra-500)'
        }}
        onMouseLeave={e => {
          (e.currentTarget as HTMLButtonElement).style.borderColor = 'rgba(184,68,42,0.20)'
          ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--ink-muted)'
        }}
      >
        <Plus size={14} />
        Agregar otra institución
      </button>

      <WizardNavigation step={2} onNext={onNext} />
    </div>
  )
}
