import { useIntl } from 'react-intl'
import { useWizardStore } from '../../../store/wizardStore'
import { SkillTag } from '../../../shared/SkillTag'

export const CVLivePreview: React.FC = () => {
  const intl = useIntl()
  const { answers, extractedSkills } = useWizardStore()

  return (
    <div className="h-full">
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
        {intl.formatMessage({ id: 'wizard.preview.title' })}
      </p>
      <div className="bg-gradient-to-b from-blue-600 to-blue-700 rounded-xl p-5 text-white shadow-lg">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-14 h-14 rounded-full bg-white/20 flex items-center justify-center text-2xl font-bold">
            {answers.full_name ? answers.full_name[0].toUpperCase() : '?'}
          </div>
          <div>
            <h3 className="font-bold text-lg">{answers.full_name || 'Tu nombre'}</h3>
            <p className="text-blue-200 text-sm">{answers.district || 'Huancayo, Junín'}</p>
          </div>
        </div>

        {answers.job_interests && (
          <div className="mb-3">
            <p className="text-xs text-blue-200 uppercase tracking-wide font-semibold mb-1">Objetivo</p>
            <p className="text-sm opacity-90">{answers.job_interests}</p>
          </div>
        )}

        {extractedSkills.length > 0 && (
          <div>
            <p className="text-xs text-blue-200 uppercase tracking-wide font-semibold mb-2">Habilidades</p>
            <div className="flex flex-wrap gap-1.5">
              {extractedSkills.slice(0, 8).map((skill) => (
                <span key={skill} className="bg-white/20 text-white text-xs px-2 py-0.5 rounded-full">
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {answers.education && answers.education.length > 0 && (
          <div className="mt-3 pt-3 border-t border-white/20">
            <p className="text-xs text-blue-200 uppercase tracking-wide font-semibold mb-1">Educación</p>
            {answers.education.slice(0, 2).map((edu, i) => (
              <p key={i} className="text-sm opacity-90">{edu.institution} · {edu.level}</p>
            ))}
          </div>
        )}
      </div>
      <p className="text-xs text-gray-400 text-center mt-2">
        {intl.formatMessage({ id: 'wizard.preview.live_hint' })}
      </p>
      {/* Progreso */}
      <div className="mt-4">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>Completitud del CV</span>
          <span className="font-semibold text-primary-600">
            {Math.min(100, (extractedSkills.length > 0 ? 20 : 0) + (answers.full_name ? 20 : 0) + (answers.job_interests ? 20 : 0) + (answers.education?.length ? 20 : 0) + (answers.district ? 20 : 0))}%
          </span>
        </div>
        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-primary-400 to-primary-600 rounded-full transition-all duration-500"
            style={{
              width: `${Math.min(100, (extractedSkills.length > 0 ? 20 : 0) + (answers.full_name ? 20 : 0) + (answers.job_interests ? 20 : 0) + (answers.education?.length ? 20 : 0) + (answers.district ? 20 : 0))}%`
            }}
          />
        </div>
      </div>
      {extractedSkills.length > 0 && (
        <div className="mt-4">
          <p className="text-xs font-semibold text-gray-600 mb-2">Habilidades detectadas:</p>
          <div className="flex flex-wrap gap-1.5">
            {extractedSkills.map((skill) => (
              <SkillTag key={skill} label={skill} color="blue" />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
