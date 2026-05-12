import { useState } from 'react'
import { useIntl } from 'react-intl'
import { useNavigate } from 'react-router-dom'
import { useWizardStore } from '../../../../store/wizardStore'
import apiClient from '../../../../api/client'
import { useWorkerContext } from '../../../../context/WorkerContext'

export const Step6Preview: React.FC = () => {
  const intl = useIntl()
  const navigate = useNavigate()
  const { answers, extractedSkills } = useWizardStore()
  const { worker } = useWorkerContext()
  const [isGenerating, setIsGenerating] = useState(false)
  const [cvUrl, setCvUrl] = useState<string | null>(null)

  const generateCV = async () => {
    if (!worker?.id) return
    setIsGenerating(true)
    try {
      await apiClient.post(`/cv/generate/${worker.id}`)
      setCvUrl(`/api/v1/cv/download/${worker.id}`)
    } catch { /* ignore */ }
    finally { setIsGenerating(false) }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">{intl.formatMessage({ id: 'wizard.step6.title' })}</h2>
        <p className="text-gray-500 text-sm mt-1">{intl.formatMessage({ id: 'wizard.step6.subtitle' })}</p>
      </div>

      {/* Preview card */}
      <div className="bg-gradient-to-br from-blue-600 to-indigo-600 rounded-2xl p-6 text-white">
        <div className="flex items-center gap-4 mb-4">
          <div className="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center text-2xl font-bold">
            {answers.full_name?.[0]?.toUpperCase() || '👤'}
          </div>
          <div>
            <h3 className="font-bold text-xl">{answers.full_name || 'Tu nombre'}</h3>
            <p className="text-blue-100 text-sm">{answers.district || 'Huancayo'} · Primer empleo</p>
          </div>
        </div>

        {answers.job_interests && (
          <div className="mb-4">
            <p className="text-xs text-blue-200 uppercase tracking-wide font-semibold mb-1">Objetivo laboral</p>
            <p className="text-sm opacity-90">{answers.job_interests}</p>
          </div>
        )}

        {extractedSkills.length > 0 && (
          <div className="mb-4">
            <p className="text-xs text-blue-200 uppercase tracking-wide font-semibold mb-2">Habilidades</p>
            <div className="flex flex-wrap gap-1.5">
              {extractedSkills.map((s) => (
                <span key={s} className="bg-white/20 text-white text-xs px-2.5 py-1 rounded-full">{s}</span>
              ))}
            </div>
          </div>
        )}

        {answers.education && answers.education.length > 0 && (
          <div>
            <p className="text-xs text-blue-200 uppercase tracking-wide font-semibold mb-1">Educación</p>
            {answers.education.map((e: { institution: string; level: string; year: string }, i: number) => (
              <p key={i} className="text-sm opacity-90">{e.institution} · {e.level} {e.year && `(${e.year})`}</p>
            ))}
          </div>
        )}
      </div>

      {/* Action buttons */}
      <div className="space-y-3">
        <button
          onClick={generateCV}
          disabled={isGenerating}
          className="w-full flex items-center justify-center gap-2 bg-primary-600 hover:bg-primary-700 disabled:opacity-60 text-white font-semibold py-3 rounded-xl transition-colors shadow-sm"
        >
          {isGenerating ? (
            <><span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" /> Generando PDF...</>
          ) : (
            <>{intl.formatMessage({ id: 'wizard.step6.download_cv' })}</>
          )}
        </button>

        {cvUrl && (
          <a
            href={cvUrl}
            target="_blank"
            rel="noreferrer"
            className="w-full block text-center bg-green-500 hover:bg-green-600 text-white font-semibold py-3 rounded-xl transition-colors"
          >
            ⬇ Descargar mi CV (PDF)
          </a>
        )}

        <button
          onClick={() => navigate('/dashboard')}
          className="w-full py-3 border-2 border-gray-200 hover:bg-gray-50 text-gray-700 font-medium rounded-xl transition-colors"
        >
          {intl.formatMessage({ id: 'wizard.step6.go_to_dashboard' })} →
        </button>
      </div>
    </div>
  )
}
