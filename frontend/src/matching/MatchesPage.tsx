import { useIntl } from 'react-intl'
import { NavBar } from '../shared/NavBar'
import { useMatches } from '../hooks/useMatches'
import { JobMatchCard } from './JobMatchCard'
import { LoadingSpinner } from '../shared/LoadingSpinner'

export const MatchesPage: React.FC = () => {
  const intl = useIntl()
  const { matches, isLoading, error } = useMatches(20)

  return (
    <div className="min-h-screen bg-gray-50">
      <NavBar />
      <div className="max-w-3xl mx-auto px-4 py-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">{intl.formatMessage({ id: 'match.title' })}</h1>
          <p className="text-gray-500 text-sm mt-1">
            Empleos ordenados por compatibilidad con tu perfil
          </p>
        </div>

        {isLoading ? (
          <LoadingSpinner />
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm">{error}</div>
        ) : matches.length === 0 ? (
          <div className="text-center py-16">
            <span className="text-5xl block mb-4">🔍</span>
            <p className="text-gray-500">{intl.formatMessage({ id: 'match.no_results' })}</p>
          </div>
        ) : (
          <div className="space-y-3">
            {matches.map((m) => <JobMatchCard key={m.job_id} match={m} />)}
          </div>
        )}
      </div>
    </div>
  )
}
