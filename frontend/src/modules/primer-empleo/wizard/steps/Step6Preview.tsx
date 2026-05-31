import { useState } from 'react'
import { useIntl } from 'react-intl'
import { useNavigate } from 'react-router-dom'
import { Download, ArrowRight } from 'lucide-react'
import { useWizardStore } from '../../../../store/wizardStore'
import apiClient from '../../../../api/client'
import { downloadCV } from '../../../../lib/downloadCV'
import { useWorkerContext } from '../../../../context/WorkerContext'

export const Step6Preview: React.FC = () => {
  const intl = useIntl()
  const navigate = useNavigate()
  const { answers, extractedSkills } = useWizardStore()
  const { worker } = useWorkerContext()
  const [isGenerating, setIsGenerating] = useState(false)
  const [downloaded, setDownloaded] = useState(false)

  const generateCV = async () => {
    if (!worker?.id) return
    setIsGenerating(true)
    try {
      await apiClient.post(`/cv/generate/${worker.id}`)
      await downloadCV(worker.id)
      setDownloaded(true)
    } catch { /* ignore */ }
    finally { setIsGenerating(false) }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold" style={{ color: 'var(--ink-strong)' }}>
          {intl.formatMessage({ id: 'wizard.step6.title' })}
        </h2>
        <p className="text-sm mt-1" style={{ color: 'var(--ink-muted)' }}>
          {intl.formatMessage({ id: 'wizard.step6.subtitle' })}
        </p>
      </div>

      {/* CV Preview card */}
      <div
        className="relative overflow-hidden rounded-2xl p-6"
        style={{ background: 'linear-gradient(160deg, var(--dark-deep) 0%, var(--dark) 60%, var(--dark-2) 100%)' }}
      >
        <div className="absolute top-0 right-0 w-40 h-40 rounded-full blur-3xl opacity-15 pointer-events-none" style={{ background: 'var(--terra-500)' }} />
        <div className="relative z-10">
          <div className="flex items-center gap-4 mb-4">
            <div
              className="w-14 h-14 rounded-full flex items-center justify-center text-xl font-bold flex-shrink-0"
              style={{ background: 'linear-gradient(135deg, var(--terra-400), var(--terra-500))', color: '#fff' }}
            >
              {answers.full_name?.[0]?.toUpperCase() || '?'}
            </div>
            <div>
              <h3 className="font-bold text-xl" style={{ color: 'var(--on-dark)' }}>{answers.full_name || 'Tu nombre'}</h3>
              <p className="text-sm" style={{ color: 'var(--on-dark-muted)' }}>{answers.district || 'Huancayo'} · Primer empleo</p>
            </div>
          </div>

          {answers.job_interests && (
            <div className="mb-4">
              <p className="text-xs uppercase tracking-wide font-semibold mb-1" style={{ color: 'var(--on-dark-muted)' }}>Objetivo laboral</p>
              <p className="text-sm opacity-90" style={{ color: 'var(--on-dark)' }}>{answers.job_interests}</p>
            </div>
          )}

          {extractedSkills.length > 0 && (
            <div className="mb-4">
              <p className="text-xs uppercase tracking-wide font-semibold mb-2" style={{ color: 'var(--on-dark-muted)' }}>Habilidades</p>
              <div className="flex flex-wrap gap-1.5">
                {extractedSkills.map((s) => (
                  <span
                    key={s}
                    className="text-xs px-2.5 py-1 rounded-full"
                    style={{ background: 'rgba(253,246,234,0.15)', color: 'var(--on-dark)', border: '1px solid rgba(253,246,234,0.20)' }}
                  >
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}

          {answers.education && answers.education.length > 0 && (
            <div>
              <p className="text-xs uppercase tracking-wide font-semibold mb-1" style={{ color: 'var(--on-dark-muted)' }}>Educación</p>
              {answers.education.map((e: { institution: string; level: string; year: string }, i: number) => (
                <p key={i} className="text-sm opacity-90" style={{ color: 'var(--on-dark)' }}>
                  {e.institution} · {e.level} {e.year && `(${e.year})`}
                </p>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Action buttons */}
      <div className="space-y-3">
        <button
          onClick={generateCV}
          disabled={isGenerating}
          className="btn-primary w-full py-3 gap-2 text-sm"
        >
          {isGenerating ? (
            <>
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
              Generando PDF...
            </>
          ) : (
            intl.formatMessage({ id: 'wizard.step6.download_cv' })
          )}
        </button>

        {downloaded && (
          <button
            onClick={() => worker?.id && downloadCV(worker.id)}
            className="btn-secondary w-full flex items-center justify-center gap-2 py-3 text-sm"
          >
            <Download size={15} />
            Descargar mi CV (PDF) de nuevo
          </button>
        )}

        <button
          onClick={() => navigate('/dashboard')}
          className="w-full py-3 text-sm font-medium flex items-center justify-center gap-1.5 transition-colors"
          style={{ color: 'var(--ink-warm)' }}
          onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.color = 'var(--ink-strong)' }}
          onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.color = 'var(--ink-warm)' }}
        >
          {intl.formatMessage({ id: 'wizard.step6.go_to_dashboard' })}
          <ArrowRight size={14} />
        </button>
      </div>
    </div>
  )
}
