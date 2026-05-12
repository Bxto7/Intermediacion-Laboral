import { useState } from 'react'
import { useIntl } from 'react-intl'
import { useWizardStore } from '../../../../store/wizardStore'
import { WizardNavigation } from '../WizardNavigation'
import apiClient from '../../../../api/client'

const LEVELS = ['Primaria', 'Secundaria', 'Técnica', 'Universitaria', 'Sin estudios']

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
        <h2 className="text-2xl font-bold text-gray-900">{intl.formatMessage({ id: 'wizard.step2.title' })}</h2>
        <p className="text-gray-500 text-sm mt-1">{intl.formatMessage({ id: 'wizard.step2.subtitle' })}</p>
      </div>

      {education.map((edu, i) => (
        <div key={i} className="bg-gray-50 rounded-xl p-4 space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Institución educativa</label>
            <input
              value={edu.institution}
              onChange={(e) => update(i, 'institution', e.target.value)}
              placeholder="Colegio, Instituto, Universidad..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Nivel</label>
              <select
                value={edu.level}
                onChange={(e) => update(i, 'level', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none bg-white"
              >
                <option value="">Seleccionar...</option>
                {LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Año de egreso</label>
              <input
                type="number"
                value={edu.year}
                onChange={(e) => update(i, 'year', e.target.value)}
                placeholder="2023"
                min="1980"
                max={new Date().getFullYear()}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
              />
            </div>
          </div>
        </div>
      ))}

      <button
        onClick={() => setEducation([...education, { institution: '', level: '', year: '' }])}
        className="w-full py-2.5 border-2 border-dashed border-gray-300 hover:border-primary-400 text-gray-500 hover:text-primary-600 rounded-xl text-sm font-medium transition-colors"
      >
        + Agregar otra institución
      </button>

      <WizardNavigation step={2} onNext={onNext} />
    </div>
  )
}
