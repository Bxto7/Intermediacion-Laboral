import { useState, useRef } from 'react'
import { useIntl } from 'react-intl'
import { Sparkles, Info } from 'lucide-react'
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
        <h2 className="text-2xl font-bold" style={{ color: 'var(--ink-strong)' }}>
          {intl.formatMessage({ id: 'wizard.step3.title' })}
        </h2>
        <p className="text-sm mt-1" style={{ color: 'var(--ink-muted)' }}>
          {intl.formatMessage({ id: 'wizard.step3.subtitle' })}
        </p>
      </div>

      <div
        className="rounded-xl p-3 flex items-start gap-2.5"
        style={{ background: 'var(--blue-100)', border: '1px solid rgba(15,110,110,0.15)' }}
      >
        <Info size={15} className="flex-shrink-0 mt-0.5" style={{ color: 'var(--blue)' }} />
        <p className="text-sm" style={{ color: 'var(--blue)' }}>
          <strong>Tip:</strong> No te preocupes por sonar formal. Escribe como hablas normalmente.
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium mb-2" style={{ color: 'var(--ink-warm)' }}>
          {intl.formatMessage({ id: 'wizard.step3.question' })}
        </label>
        <textarea
          value={freeText}
          onChange={handleTextChange}
          rows={5}
          placeholder={intl.formatMessage({ id: 'wizard.step3.placeholder' })}
          className="w-full rounded-xl p-3.5 text-sm transition resize-none focus:outline-none"
          style={{ border: '1px solid rgba(42,29,20,0.14)', background: 'var(--bg-soft)', color: 'var(--ink-strong)' }}
          onFocus={e => { e.currentTarget.style.borderColor = 'var(--terra-500)'; e.currentTarget.style.boxShadow = '0 0 0 3px rgba(184,68,42,0.12)' }}
          onBlur={e => { e.currentTarget.style.borderColor = 'rgba(42,29,20,0.14)'; e.currentTarget.style.boxShadow = 'none' }}
        />
        <p className="text-xs mt-1" style={{ color: 'var(--ink-muted)' }}>{freeText.length} caracteres · mínimo 15</p>
      </div>

      {isExtracting && (
        <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--terra-500)' }}>
          <span className="h-4 w-4 animate-spin rounded-full border-2" style={{ borderColor: 'rgba(184,68,42,0.20)', borderTopColor: 'var(--terra-500)' }} />
          {intl.formatMessage({ id: 'wizard.step3.extracting' })}
        </div>
      )}

      {extractedSkills.length > 0 && (
        <div
          className="rounded-xl p-4"
          style={{ background: 'var(--olive-100)', border: '1px solid rgba(122,140,92,0.25)' }}
        >
          <p className="text-sm font-semibold mb-2 flex items-center gap-1.5" style={{ color: 'var(--olive-deep)' }}>
            <Sparkles size={14} />
            {intl.formatMessage({ id: 'wizard.step3.skills_found' })}
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
