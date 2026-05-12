import { useState, useRef } from 'react'
import { useIntl } from 'react-intl'
import { useWizardStore } from '../../../../store/wizardStore'
import { WizardNavigation } from '../WizardNavigation'
import { SkillTag } from '../../../../shared/SkillTag'
import apiClient from '../../../../api/client'

export const Step3Skills: React.FC = () => {
  const intl = useIntl()
  const { answers, setAnswer, extractedSkills, setExtractedSkills, removeSkill } = useWizardStore()
  const [isExtracting, setIsExtracting] = useState(false)
  const [freeText, setFreeText] = useState(answers.free_text_skills || '')
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const extractSkills = async (text: string) => {
    if (text.length < 15) return
    setIsExtracting(true)
    try {
      const { data } = await apiClient.post('/nlp/extract-skills', {
        user_text: text,
        worker_type: 'primer_empleo',
      })
      setExtractedSkills(data.skills || [])
    } catch { /* silencioso */ }
    finally { setIsExtracting(false) }
  }

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value
    setFreeText(val)
    setAnswer('free_text_skills', val)
    if (timerRef.current) clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => extractSkills(val), 1000)
  }

  const onNext = async () => {
    await apiClient.post('/wizard/step/3', {
      step: 3,
      answers: { free_text_skills: freeText, skills: extractedSkills },
    }).catch(() => null)
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">
          {intl.formatMessage({ id: 'wizard.step3.title' })}
        </h2>
        <p className="text-gray-500 text-sm mt-1">
          {intl.formatMessage({ id: 'wizard.step3.subtitle' })}
        </p>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-xl p-3 text-sm text-blue-700">
        💡 <strong>Tip:</strong> No te preocupes por sonar formal. Escribe como hablas normalmente.
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {intl.formatMessage({ id: 'wizard.step3.question' })}
        </label>
        <textarea
          value={freeText}
          onChange={handleTextChange}
          rows={5}
          placeholder={intl.formatMessage({ id: 'wizard.step3.placeholder' })}
          className="w-full border border-gray-300 rounded-xl p-3.5 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition resize-none"
        />
        <p className="text-xs text-gray-400 mt-1">{freeText.length} caracteres · mínimo 15</p>
      </div>

      {isExtracting && (
        <div className="flex items-center gap-2 text-sm text-primary-600">
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-primary-200 border-t-primary-600" />
          {intl.formatMessage({ id: 'wizard.step3.extracting' })}
        </div>
      )}

      {extractedSkills.length > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-4">
          <p className="text-sm font-semibold text-green-700 mb-2">
            ✨ {intl.formatMessage({ id: 'wizard.step3.skills_found' })}
          </p>
          <div className="flex flex-wrap gap-2">
            {extractedSkills.map((skill) => (
              <SkillTag key={skill} label={skill} removable onRemove={removeSkill} color="green" />
            ))}
          </div>
        </div>
      )}

      <WizardNavigation step={3} onNext={onNext} />
    </div>
  )
}
