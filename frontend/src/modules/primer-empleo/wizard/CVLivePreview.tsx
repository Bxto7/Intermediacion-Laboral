import { useIntl } from 'react-intl'
import { useWizardStore } from '../../../store/wizardStore'
import { SkillTag } from '../../../shared/SkillTag'

export const CVLivePreview: React.FC = () => {
  const intl = useIntl()
  const { answers, extractedSkills } = useWizardStore()

  const completeness = Math.min(100,
    (extractedSkills.length > 0 ? 20 : 0) +
    (answers.full_name ? 20 : 0) +
    (answers.job_interests ? 20 : 0) +
    (answers.education?.length ? 20 : 0) +
    (answers.district ? 20 : 0)
  )

  return (
    <div className="h-full">
      <p className="text-xs font-semibold uppercase tracking-wide mb-3" style={{ color: 'var(--ink-muted)' }}>
        {intl.formatMessage({ id: 'wizard.preview.title' })}
      </p>

      {/* CV card — warm dark */}
      <div
        className="relative overflow-hidden rounded-xl p-5"
        style={{ background: 'linear-gradient(160deg, var(--dark-deep) 0%, var(--dark) 70%, var(--dark-2) 100%)' }}
      >
        <div className="absolute top-0 right-0 w-24 h-24 rounded-full blur-3xl opacity-20 pointer-events-none" style={{ background: 'var(--terra-500)' }} />
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-4">
            <div
              className="w-12 h-12 rounded-full flex items-center justify-center text-lg font-bold flex-shrink-0"
              style={{ background: 'linear-gradient(135deg, var(--terra-400), var(--terra-500))', color: '#fff' }}
            >
              {answers.full_name ? answers.full_name[0].toUpperCase() : '?'}
            </div>
            <div>
              <h3 className="font-bold" style={{ color: 'var(--on-dark)' }}>{answers.full_name || 'Tu nombre'}</h3>
              <p className="text-xs" style={{ color: 'var(--on-dark-muted)' }}>{answers.district || 'Huancayo, Junín'}</p>
            </div>
          </div>

          {answers.job_interests && (
            <div className="mb-3">
              <p className="text-xs uppercase tracking-wide font-semibold mb-1" style={{ color: 'var(--on-dark-muted)' }}>Objetivo</p>
              <p className="text-xs opacity-90" style={{ color: 'var(--on-dark)' }}>{answers.job_interests}</p>
            </div>
          )}

          {extractedSkills.length > 0 && (
            <div>
              <p className="text-xs uppercase tracking-wide font-semibold mb-2" style={{ color: 'var(--on-dark-muted)' }}>Habilidades</p>
              <div className="flex flex-wrap gap-1">
                {extractedSkills.slice(0, 8).map((skill) => (
                  <span
                    key={skill}
                    className="text-[11px] px-2 py-0.5 rounded-full"
                    style={{ background: 'rgba(244,236,224,0.15)', color: 'var(--on-dark)', border: '1px solid rgba(244,236,224,0.18)' }}
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}

          {answers.education && answers.education.length > 0 && (
            <div className="mt-3 pt-3" style={{ borderTop: '1px solid rgba(244,236,224,0.15)' }}>
              <p className="text-xs uppercase tracking-wide font-semibold mb-1" style={{ color: 'var(--on-dark-muted)' }}>Educación</p>
              {answers.education.slice(0, 2).map((edu: { institution: string; level: string }, i: number) => (
                <p key={i} className="text-xs opacity-90" style={{ color: 'var(--on-dark)' }}>{edu.institution} · {edu.level}</p>
              ))}
            </div>
          )}
        </div>
      </div>

      <p className="text-xs text-center mt-2" style={{ color: 'var(--ink-muted)' }}>
        {intl.formatMessage({ id: 'wizard.preview.live_hint' })}
      </p>

      {/* Completeness bar */}
      <div className="mt-4">
        <div className="flex justify-between text-xs mb-1" style={{ color: 'var(--ink-muted)' }}>
          <span>Completitud del CV</span>
          <span className="font-semibold" style={{ color: 'var(--terra-500)' }}>{completeness}%</span>
        </div>
        <div className="h-2 rounded-full overflow-hidden" style={{ background: 'var(--bg-warm)' }}>
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{ width: `${completeness}%`, background: 'linear-gradient(to right, var(--terra-400), var(--terra-500))' }}
          />
        </div>
      </div>

      {extractedSkills.length > 0 && (
        <div className="mt-4">
          <p className="text-xs font-semibold mb-2" style={{ color: 'var(--ink-warm)' }}>Habilidades detectadas:</p>
          <div className="flex flex-wrap gap-1.5">
            {extractedSkills.map((skill) => (
              <SkillTag key={skill} label={skill} color="amber" />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
