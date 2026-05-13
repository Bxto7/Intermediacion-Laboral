import { useIntl } from 'react-intl'
import { Search, AlertCircle } from 'lucide-react'
import { useMatches } from '../hooks/useMatches'
import { JobMatchCard } from './JobMatchCard'
import { LoadingSpinner } from '../shared/LoadingSpinner'

export const MatchesPage: React.FC = () => {
  const intl = useIntl()
  const { matches, isLoading, error } = useMatches(20)

  return (
    <div className="space-y-5">
        <div className="mb-6">
          <h1 className="text-2xl font-bold" style={{ color: 'var(--ink-strong)', letterSpacing: '-0.02em' }}>
            {intl.formatMessage({ id: 'match.title' })}
          </h1>
          <p className="text-sm mt-1" style={{ color: 'var(--ink-muted)' }}>
            Empleos ordenados por compatibilidad con tu perfil
          </p>
        </div>

        {isLoading ? (
          <LoadingSpinner />
        ) : error ? (
          <div
            className="rounded-xl p-4 flex items-start gap-3"
            style={{ background: 'rgba(194,86,46,0.08)', border: '1px solid rgba(194,86,46,0.20)' }}
          >
            <AlertCircle size={16} style={{ color: 'var(--terra-500)' }} className="flex-shrink-0 mt-0.5" />
            <p className="text-sm" style={{ color: 'var(--terra-700)' }}>{error}</p>
          </div>
        ) : matches.length === 0 ? (
          <div className="text-center py-16 space-y-3">
            <div className="w-16 h-16 rounded-3xl mx-auto flex items-center justify-center" style={{ background: 'rgba(61,40,24,0.06)' }}>
              <Search size={28} style={{ color: 'var(--ink-muted)' }} strokeWidth={1.5} />
            </div>
            <p style={{ color: 'var(--ink-muted)' }}>{intl.formatMessage({ id: 'match.no_results' })}</p>
          </div>
        ) : (
          <div className="space-y-3">
            {matches.map((m) => <JobMatchCard key={m.job_id} match={m} />)}
          </div>
        )}
    </div>
  )
}
