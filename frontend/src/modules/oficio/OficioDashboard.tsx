import { useIntl } from 'react-intl'
import { Link } from 'react-router-dom'
import { useWorkerContext } from '../../context/WorkerContext'
import { useMatches } from '../../hooks/useMatches'
import { JobMatchCard } from '../../matching/JobMatchCard'
import { LoadingSpinner } from '../../shared/LoadingSpinner'

export const OficioDashboard: React.FC = () => {
  const intl = useIntl()
  const { worker } = useWorkerContext()
  const { matches, isLoading } = useMatches(5)

  return (
    <div className="min-h-screen bg-amber-50">
      <div className="max-w-5xl mx-auto px-4 py-6 space-y-5">

        {/* Banner */}
        <div className="bg-gradient-to-r from-amber-700 to-amber-500 rounded-2xl p-5 text-white shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold">{worker?.trade_category || 'Mi oficio'}</h1>
              <p className="text-amber-100 text-sm">{worker?.district} · {worker?.avg_rating?.toFixed(1) || '—'}/5.0 ⭐</p>
            </div>
            <Link
              to="/oficio/portfolio"
              className="bg-white text-amber-700 font-semibold text-sm px-4 py-2 rounded-xl hover:bg-amber-50 transition-colors"
            >
              Mi Portfolio →
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {/* Portfolio */}
          <div className="bg-white rounded-2xl shadow-md border border-amber-100 p-5">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-amber-100 rounded-xl flex items-center justify-center"><span className="text-xl">📸</span></div>
              <h2 className="font-bold text-gray-800">{intl.formatMessage({ id: 'worker.oficio.profile.title' })}</h2>
            </div>
            <p className="text-sm text-gray-500 mb-4">Muestra tus mejores trabajos y genera tu CV automático</p>
            <Link
              to="/oficio/portfolio"
              className="block w-full text-center py-2.5 bg-amber-500 hover:bg-amber-600 text-white rounded-xl font-medium text-sm transition-colors"
            >
              Ver mi portfolio
            </Link>
          </div>

          {/* Marketplace */}
          <div className="bg-white rounded-2xl shadow-md border border-amber-100 p-5">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-orange-100 rounded-xl flex items-center justify-center"><span className="text-xl">🏪</span></div>
              <h2 className="font-bold text-gray-800">Marketplace de servicios</h2>
            </div>
            <p className="text-sm text-gray-500 mb-4">Publica tu disponibilidad y recibe solicitudes de trabajo</p>
            <Link
              to="/marketplace"
              className="block w-full text-center py-2.5 bg-orange-500 hover:bg-orange-600 text-white rounded-xl font-medium text-sm transition-colors"
            >
              Ir al marketplace
            </Link>
          </div>
        </div>

        {/* Matches */}
        <div className="bg-white rounded-2xl shadow-md border border-amber-100 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-bold text-gray-800">Ofertas compatibles</h2>
            <Link to="/matches" className="text-xs text-amber-600 font-medium hover:underline">Ver todos →</Link>
          </div>
          {isLoading ? <LoadingSpinner size="sm" /> : matches.length > 0 ? (
            <div className="space-y-3">
              {matches.map((m) => <JobMatchCard key={m.job_id} match={m} workerType="oficio" />)}
            </div>
          ) : (
            <p className="text-sm text-gray-500 text-center py-4">{intl.formatMessage({ id: 'match.no_results' })}</p>
          )}
        </div>
      </div>
    </div>
  )
}
