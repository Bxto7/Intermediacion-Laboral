import { useIntl } from 'react-intl'
import { SkillTag } from '../shared/SkillTag'
import type { JobMatch } from '../hooks/useMatches'

interface Props {
  match: JobMatch
  workerType?: string
}

const labelColors = {
  Alta: 'bg-green-100 text-green-800 border-green-200',
  Media: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  Baja: 'bg-red-100 text-red-800 border-red-200',
}

const scoreBar = (score: number) => {
  const pct = Math.round(score * 100)
  const color = pct >= 70 ? 'bg-green-500' : pct >= 45 ? 'bg-yellow-400' : 'bg-red-400'
  return { pct, color }
}

export const JobMatchCard: React.FC<Props> = ({ match }) => {
  const intl = useIntl()
  const { pct, color } = scoreBar(match.combined_score)
  const label = match.explanation.compatibility_label as keyof typeof labelColors

  return (
    <div className="bg-white rounded-xl border border-gray-200 hover:border-primary-300 hover:shadow-md transition-all p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 text-sm truncate">{match.title}</h3>
          {match.district && (
            <p className="text-xs text-gray-500 mt-0.5">📍 {match.district}</p>
          )}
        </div>
        <div className="flex flex-col items-end gap-1 flex-shrink-0">
          <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${labelColors[label]}`}>
            {label}
          </span>
          <span className="text-sm font-bold text-gray-800">{pct}%</span>
        </div>
      </div>

      {/* Score bar */}
      <div className="mt-3 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>

      {/* Skills */}
      {match.explanation.matching_skills.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {match.explanation.matching_skills.slice(0, 4).map((skill) => (
            <SkillTag key={skill} label={skill} color="green" />
          ))}
          {match.explanation.missing_skills.slice(0, 2).map((skill) => (
            <SkillTag key={skill} label={skill} color="gray" />
          ))}
        </div>
      )}

      {/* Message */}
      <p className="text-xs text-gray-500 mt-2 italic">{match.explanation.message}</p>

      <div className="mt-3 flex items-center justify-between">
        <span className="text-xs text-gray-400">Rank #{match.rank}</span>
        <button className="text-xs bg-primary-600 hover:bg-primary-700 text-white px-3 py-1.5 rounded-lg font-medium transition-colors">
          {intl.formatMessage({ id: 'match.select' })}
        </button>
      </div>
    </div>
  )
}
