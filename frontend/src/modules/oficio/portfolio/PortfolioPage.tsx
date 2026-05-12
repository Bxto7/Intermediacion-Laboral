import { useState } from 'react'
import { useIntl } from 'react-intl'
import { usePortfolio } from '../../../hooks/usePortfolio'
import { PortfolioCard } from './PortfolioCard'
import { AddEntryModal } from './AddEntryModal'
import { LoadingSpinner } from '../../../shared/LoadingSpinner'
import apiClient from '../../../api/client'
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
      window.open(`/api/v1/cv/download/${worker.id}`, '_blank')
    } catch { /* ignore */ }
    finally { setIsGeneratingCV(false) }
  }

  return (
    <div className="min-h-screen bg-amber-50">
      {/* Header amber */}
      <div className="bg-gradient-to-r from-amber-700 to-amber-600 text-white">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <div className="w-14 h-14 rounded-full bg-white/20 flex items-center justify-center text-2xl font-bold">
                  {worker?.display_name?.[0] || '🛠️'}
                </div>
                <div>
                  <h1 className="text-xl font-bold">{worker?.display_name || 'Mi portfolio'}</h1>
                  <p className="text-amber-200 text-sm">
                    {worker?.trade_category || 'Oficio'} · {worker?.district || 'Huancayo'}
                  </p>
                </div>
              </div>
              {worker?.avg_rating !== undefined && worker.avg_rating > 0 && (
                <div className="flex items-center gap-1.5">
                  <span className="text-yellow-300">{'★'.repeat(Math.round(worker.avg_rating))}</span>
                  <span className="text-amber-100 text-sm">{worker.avg_rating.toFixed(1)}/5.0</span>
                  <span className="text-amber-200 text-xs">({entries.length} trabajos)</span>
                </div>
              )}
            </div>

            <div className="flex flex-col items-end gap-2">
              {/* Toggle disponibilidad */}
              <button
                onClick={toggleAvailability}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl font-medium text-sm transition-all ${
                  isAvailable
                    ? 'bg-green-500 hover:bg-green-600 text-white'
                    : 'bg-white/20 hover:bg-white/30 text-white'
                }`}
              >
                <span className={`w-2 h-2 rounded-full ${isAvailable ? 'bg-white animate-pulse' : 'bg-white/50'}`} />
                {isAvailable ? 'Disponible' : 'No disponible'}
              </button>

              {worker?.slug && (
                <a
                  href={`/p/${worker.slug}`}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs bg-amber-600 hover:bg-amber-500 px-3 py-1.5 rounded-lg transition-colors"
                >
                  {intl.formatMessage({ id: 'oficio.portfolio.view_public' })} ↗
                </a>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 py-5 space-y-5">
        {/* Action buttons */}
        <div className="flex gap-3">
          <button
            onClick={() => setShowAddModal(true)}
            className="flex-1 flex items-center justify-center gap-2 py-3 bg-amber-500 hover:bg-amber-600 text-white rounded-xl font-semibold text-sm transition-colors shadow-sm"
          >
            + {intl.formatMessage({ id: 'oficio.portfolio.add_work' })}
          </button>
          <button
            onClick={generateCV}
            disabled={isGeneratingCV}
            className="flex-1 flex items-center justify-center gap-2 py-3 bg-white border-2 border-amber-400 text-amber-700 hover:bg-amber-50 rounded-xl font-semibold text-sm transition-colors disabled:opacity-60"
          >
            {isGeneratingCV ? (
              <><span className="h-4 w-4 animate-spin rounded-full border-2 border-amber-300 border-t-amber-700" /> Generando...</>
            ) : (
              <>📄 {intl.formatMessage({ id: 'oficio.portfolio.generate_cv' })}</>
            )}
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: 'Trabajos', value: entries.length, icon: '🛠️' },
            { label: 'Calificación', value: worker?.avg_rating?.toFixed(1) || '—', icon: '⭐' },
            { label: 'Habilidades', value: [...new Set(entries.flatMap((e) => e.extracted_skills))].length, icon: '🎯' },
          ].map((stat) => (
            <div key={stat.label} className="bg-white rounded-xl border border-amber-100 p-3 text-center shadow-sm">
              <span className="text-xl block mb-1">{stat.icon}</span>
              <p className="text-xl font-bold text-gray-900">{stat.value}</p>
              <p className="text-xs text-gray-500">{stat.label}</p>
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
          <div className="bg-white rounded-2xl border-2 border-dashed border-amber-200 p-10 text-center">
            <span className="text-5xl block mb-3">🛠️</span>
            <p className="font-semibold text-gray-700 mb-1">Aún no tienes trabajos en tu portfolio</p>
            <p className="text-sm text-gray-500 mb-4">Agrega fotos y descripciones de tus trabajos para mostrar lo que sabes hacer</p>
            <button
              onClick={() => setShowAddModal(true)}
              className="bg-amber-500 hover:bg-amber-600 text-white px-6 py-2.5 rounded-xl font-semibold text-sm transition-colors"
            >
              Agregar mi primer trabajo
            </button>
          </div>
        )}
      </div>

      {showAddModal && <AddEntryModal onClose={() => setShowAddModal(false)} />}
    </div>
  )
}
