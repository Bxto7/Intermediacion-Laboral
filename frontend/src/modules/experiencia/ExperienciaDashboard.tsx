import { useIntl } from 'react-intl'
import { Link } from 'react-router-dom'
import { useMatches } from '../../hooks/useMatches'
import { JobMatchCard } from '../../matching/JobMatchCard'
import { LoadingSpinner } from '../../shared/LoadingSpinner'
import { useWorkerContext } from '../../context/WorkerContext'

export const ExperienciaDashboard: React.FC = () => {
  const intl = useIntl()
  const { matches, isLoading } = useMatches(10)
  const { worker } = useWorkerContext()

  const completeness = worker?.profile_completeness ?? 0

  return (
    <div className="min-h-screen pb-16">
      <div className="max-w-5xl mx-auto px-5 py-8 space-y-6">

        {/* ── Header de perfil ── */}
        <div className="card-warm p-6 relative overflow-hidden">
          {/* Subtle glow inside card */}
          <div className="absolute right-0 top-0 w-64 h-64 opacity-20 rounded-full blur-3xl pointer-events-none"
               style={{ background: '#d97757', transform: 'translate(30%, -30%)' }} />
          <div className="flex items-start gap-4">
            {/* Avatar */}
            <div className="w-14 h-14 rounded-xl flex items-center justify-center flex-shrink-0 shadow-warm-sm"
                 style={{ background: 'linear-gradient(135deg, #4a3120, #3d2818)' }}>
              <span className="text-xl font-bold text-white">
                {worker?.display_name?.[0]?.toUpperCase() ?? 'U'}
              </span>
            </div>

            <div className="flex-1 min-w-0">
              <h1 className="text-lg font-bold text-bark-900 truncate">
                {worker?.display_name ?? 'Mi perfil profesional'}
              </h1>
              <p className="text-bark-500 text-sm">
                {worker?.district ? `${worker.district} · ` : ''}Profesional con experiencia
              </p>
              {worker?.avg_rating !== undefined && worker.avg_rating > 0 && (
                <p className="text-sm text-amber-600 font-medium mt-0.5">
                  {'★'.repeat(Math.round(worker.avg_rating))} {worker.avg_rating.toFixed(1)}/5.0
                </p>
              )}
            </div>

            <Link
              to="/matches"
              className="btn-primary text-xs px-4 py-2 flex-shrink-0"
            >
              Ver empleos
            </Link>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-3 mt-5">
            {[
              { label: 'Completitud', value: `${completeness}%`, color: completeness >= 60 ? 'text-secondary-500' : 'text-primary-600' },
              { label: 'Visibilidad',    value: '—',              color: 'text-bark-400' },
              { label: 'Postulaciones',  value: '0',              color: 'text-bark-900' },
            ].map((stat) => (
              <div key={stat.label} className="bg-warm-50 rounded-xl p-3.5 text-center border border-warm-200">
                <p className={`text-xl font-bold ${stat.color}`}>{stat.value}</p>
                <p className="text-xs text-bark-400 mt-0.5">{stat.label}</p>
              </div>
            ))}
          </div>

          {/* Barra de completitud */}
          <div className="mt-4 space-y-1.5">
            <div className="flex justify-between items-center">
              <span className="text-xs text-bark-500">Completitud del perfil</span>
              <span className="text-xs font-semibold text-bark-700">{completeness}%</span>
            </div>
            <div className="h-1.5 bg-warm-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-primary-500 rounded-full transition-all duration-500"
                style={{ width: `${completeness}%` }}
              />
            </div>
          </div>
        </div>

        {/* ── Bolsa de empleos ── */}
        <div className="card-warm p-6">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="font-bold text-bark-900">Bolsa formal de empleos</h2>
              <p className="text-xs text-bark-400 mt-0.5">Ordenado por compatibilidad con tu perfil</p>
            </div>
            <Link
              to="/matches"
              className="text-xs font-semibold text-primary-600 hover:text-primary-700 transition-colors flex items-center gap-1"
            >
              Ver todo
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>

          {isLoading ? (
            <LoadingSpinner />
          ) : matches.length > 0 ? (
            <div className="space-y-3">
              {matches.map((m) => (
                <JobMatchCard key={m.job_id} match={m} workerType="experiencia" />
              ))}
            </div>
          ) : (
            <div className="text-center py-12 space-y-3">
              <div className="w-12 h-12 mx-auto rounded-xl bg-warm-100 border border-warm-200 flex items-center justify-center">
                <svg className="w-6 h-6 text-bark-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                </svg>
              </div>
              <div>
                <p className="font-semibold text-bark-700 text-sm">{intl.formatMessage({ id: 'match.no_results' })}</p>
                <p className="text-bark-400 text-xs mt-1">Completa tu perfil para mejorar tus recomendaciones</p>
              </div>
            </div>
          )}
        </div>

        {/* ── Alertas de empleo ── */}
        <div className="card-warm p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-9 h-9 bg-warm-100 rounded-xl border border-warm-200 flex items-center justify-center">
              <svg className="w-4 h-4 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
            </div>
            <div>
              <h2 className="font-bold text-bark-900 text-sm">Alertas de empleo</h2>
              <p className="text-xs text-bark-400">Te notificamos cuando aparezca algo compatible</p>
            </div>
          </div>
          <button className="w-full py-2.5 border-2 border-dashed border-warm-300 hover:border-primary-400 hover:bg-primary-50/40 text-bark-400 hover:text-primary-600 rounded-xl text-sm font-medium transition-all">
            + Crear nueva alerta
          </button>
        </div>

      </div>
    </div>
  )
}
