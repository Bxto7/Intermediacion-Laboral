import { useState } from 'react'
import { useIntl } from 'react-intl'
import { Plus, FileText, Star, Wrench, ExternalLink, ToggleLeft, ToggleRight } from 'lucide-react'
import { usePortfolio } from '../../../hooks/usePortfolio'
import { PortfolioCard } from './PortfolioCard'
import { AddEntryModal } from './AddEntryModal'
import { LoadingSpinner } from '../../../shared/LoadingSpinner'
import apiClient from '../../../api/client'
import { downloadCV } from '../../../lib/downloadCV'
import { useWorkerContext } from '../../../context/WorkerContext'

export const PortfolioPage: React.FC = () => {
  const intl = useIntl()
  const { entries, isLoading, deleteEntry } = usePortfolio()
  const { worker } = useWorkerContext()
  const [showAddModal, setShowAddModal] = useState(false)
  const [isAvailable, setIsAvailable] = useState(true)
  const [isGeneratingCV, setIsGeneratingCV] = useState(false)

  const toggleAvailability = async () => {
    setIsAvailable((prev) => !prev)
    await apiClient.patch('/workers/me', { is_available: !isAvailable }).catch(() => null)
  }

  const generateCV = async () => {
    if (!worker?.id) return
    setIsGeneratingCV(true)
    try {
      await apiClient.post(`/cv/generate/${worker.id}`)
      await downloadCV(worker.id)
    } catch { /* ignore */ }
    finally { setIsGeneratingCV(false) }
  }

  const allSkills = [...new Set(entries.flatMap((e) => e.extracted_skills))]

  return (
    <div>

      {/* Hero header */}
      <div
        className="relative overflow-hidden py-10 px-4"
        style={{ background: 'linear-gradient(160deg, var(--dark-deep) 0%, var(--dark) 60%, var(--dark-2) 100%)' }}
      >
        <div className="absolute top-0 right-0 w-64 h-64 rounded-full blur-3xl opacity-15 pointer-events-none" style={{ background: 'var(--terra-500)' }} />
        <div className="absolute bottom-0 left-0 w-48 h-48 rounded-full blur-3xl opacity-10 pointer-events-none" style={{ background: 'var(--olive)' }} />

        <div className="max-w-4xl mx-auto relative z-10">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-center gap-4">
              <div
                className="w-14 h-14 rounded-full flex items-center justify-center text-xl font-bold flex-shrink-0"
                style={{ background: 'linear-gradient(135deg, var(--terra-400), var(--terra-500))', color: '#fff' }}
              >
                {worker?.display_name?.[0] || <Wrench size={24} />}
              </div>
              <div>
                <h1 className="text-xl font-bold tracking-tight" style={{ color: 'var(--on-dark)', letterSpacing: '-0.025em' }}>
                  {worker?.display_name || 'Mi portfolio'}
                </h1>
                <p className="text-sm" style={{ color: 'var(--on-dark-muted)' }}>
                  {worker?.trade_category || 'Oficio'} · {worker?.district || 'Huancayo'}
                </p>
                {worker?.avg_rating !== undefined && worker.avg_rating > 0 && (
                  <div className="flex items-center gap-1.5 mt-1">
                    <Star size={12} fill="currentColor" style={{ color: 'var(--gold-light)' }} />
                    <span className="text-sm font-semibold" style={{ color: 'var(--on-dark)' }}>{worker.avg_rating.toFixed(1)}</span>
                    <span className="text-xs" style={{ color: 'var(--on-dark-muted)' }}>/5.0 · {entries.length} trabajos</span>
                  </div>
                )}
              </div>
            </div>

            <div className="flex flex-col items-end gap-2">
              <button
                onClick={toggleAvailability}
                className="flex items-center gap-2 px-4 py-2 rounded-full font-medium text-sm transition-all"
                style={{
                  background: isAvailable ? 'rgba(122,140,92,0.25)' : 'rgba(244,236,224,0.12)',
                  color: 'var(--on-dark)',
                  border: '1px solid ' + (isAvailable ? 'rgba(122,140,92,0.40)' : 'rgba(244,236,224,0.20)'),
                }}
              >
                {isAvailable
                  ? <ToggleRight size={16} style={{ color: 'var(--olive)' }} />
                  : <ToggleLeft size={16} style={{ color: 'var(--on-dark-muted)' }} />
                }
                {isAvailable ? 'Disponible' : 'No disponible'}
              </button>

              {worker?.slug && (
                <a
                  href={`/p/${worker.slug}`}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full transition-colors"
                  style={{ background: 'rgba(244,236,224,0.12)', color: 'var(--on-dark-muted)', border: '1px solid rgba(244,236,224,0.15)' }}
                >
                  <ExternalLink size={11} />
                  {intl.formatMessage({ id: 'oficio.portfolio.view_public' })}
                </a>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-5 space-y-5">

        {/* Action buttons */}
        <div className="flex gap-3">
          <button
            onClick={() => setShowAddModal(true)}
            className="btn-primary flex-1 py-3 gap-2 text-sm"
          >
            <Plus size={16} />
            {intl.formatMessage({ id: 'oficio.portfolio.add_work' })}
          </button>
          <button
            onClick={generateCV}
            disabled={isGeneratingCV}
            className="btn-secondary flex-1 py-3 gap-2 text-sm"
          >
            {isGeneratingCV ? (
              <>
                <span className="h-4 w-4 animate-spin rounded-full border-2" style={{ borderColor: 'var(--bg-warm)', borderTopColor: 'var(--terra-500)' }} />
                Generando...
              </>
            ) : (
              <>
                <FileText size={16} />
                {intl.formatMessage({ id: 'oficio.portfolio.generate_cv' })}
              </>
            )}
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: 'Trabajos',    value: entries.length,                                                                      Icon: Wrench  },
            { label: 'Calificación',value: worker?.avg_rating ? worker.avg_rating.toFixed(1) : '—',                             Icon: Star    },
            { label: 'Habilidades', value: allSkills.length,                                                                    Icon: FileText },
          ].map((stat) => (
            <div key={stat.label} className="card-warm p-4 text-center">
              <div className="w-8 h-8 rounded-xl mx-auto mb-2 flex items-center justify-center" style={{ background: 'var(--terra-100)' }}>
                <stat.Icon size={15} style={{ color: 'var(--terra-500)' }} />
              </div>
              <p className="text-xl font-bold" style={{ color: 'var(--ink-strong)' }}>{stat.value}</p>
              <p className="text-xs mt-0.5" style={{ color: 'var(--ink-muted)' }}>{stat.label}</p>
            </div>
          ))}
        </div>

        {/* Grid de trabajos */}
        {isLoading ? (
          <LoadingSpinner />
        ) : entries.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {entries.map((entry) => (
              <PortfolioCard key={entry.id} entry={entry} onDelete={deleteEntry} />
            ))}
          </div>
        ) : (
          <div
            className="rounded-2xl p-10 text-center"
            style={{ border: '2px dashed rgba(184,68,42,0.20)', background: 'var(--bg-elevated)' }}
          >
            <div
              className="w-16 h-16 rounded-2xl mx-auto mb-4 flex items-center justify-center"
              style={{ background: 'rgba(42,29,20,0.05)' }}
            >
              <Wrench size={28} style={{ color: 'var(--ink-muted)' }} strokeWidth={1.5} />
            </div>
            <p className="font-semibold text-sm mb-1" style={{ color: 'var(--ink-warm)' }}>
              Aún no tienes trabajos en tu portfolio
            </p>
            <p className="text-sm mb-5" style={{ color: 'var(--ink-muted)' }}>
              Agrega fotos y descripciones de tus trabajos para mostrar lo que sabes hacer
            </p>
            <button
              onClick={() => setShowAddModal(true)}
              className="btn-primary text-sm px-6 py-2.5 gap-2"
            >
              <Plus size={14} />
              Agregar mi primer trabajo
            </button>
          </div>
        )}
      </div>

      {showAddModal && <AddEntryModal onClose={() => setShowAddModal(false)} />}
    </div>
  )
}
