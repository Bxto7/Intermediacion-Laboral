import { MapPin } from 'lucide-react'
import { useIntl } from 'react-intl'
import { SkillTag } from '../shared/SkillTag'
import type { JobMatch } from '../hooks/useMatches'

interface Props {
  match: JobMatch
  workerType?: string
  compact?: boolean
}

const labelColors = {
  Alta:  'bg-[rgba(122,140,92,0.14)] text-olive-deep border-[rgba(122,140,92,0.20)]',
  Media: 'bg-[rgba(184,137,58,0.14)] text-gold border-[rgba(184,137,58,0.20)]',
  Baja:  'bg-[rgba(194,86,46,0.10)] text-terra-500 border-[rgba(194,86,46,0.20)]',
}

const scoreBar = (score: number) => {
  const pct = Math.round(score * 100)
  const color = pct >= 70 ? 'bg-olive' : pct >= 45 ? 'bg-gold' : 'bg-terra-500'
  return { pct, color }
}

export const JobMatchCard: React.FC<Props> = ({ match, compact = false }) => {
  const intl = useIntl()
  const { pct, color } = scoreBar(match.combined_score)
  const label = match.explanation.compatibility_label as keyof typeof labelColors

  return (
    <div
      className="card-warm hover:-translate-y-0.5 transition-all duration-200"
      style={{ cursor: 'default', padding: compact ? '12px' : '16px' }}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-sm truncate" style={{ color: 'var(--ink-strong)' }}>{match.title}</h3>
          {match.district && (
            <p className="text-xs mt-0.5 flex items-center gap-1" style={{ color: 'var(--ink-muted)' }}>
              <MapPin size={10} /> {match.district}
            </p>
          )}
        </div>
        <div className="flex flex-col items-end gap-1 flex-shrink-0">
          <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${labelColors[label] ?? ''}`}>
            {label}
          </span>
          <span className="text-sm font-bold" style={{ color: 'var(--ink-strong)' }}>{pct}%</span>
        </div>
      </div>

      {/* Score bar */}
      <div className="mt-3 h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--bg-warm)' }}>
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>

      {/* Skills */}
      {!compact && match.explanation.matching_skills.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {match.explanation.matching_skills.slice(0, 4).map((skill) => (
            <SkillTag key={skill} label={skill} color="green" />
          ))}
          {match.explanation.missing_skills.slice(0, 2).map((skill) => (
            <SkillTag key={skill} label={skill} color="amber" />
          ))}
        </div>
      )}

      {!compact && <p className="text-xs mt-2 italic" style={{ color: 'var(--ink-muted)' }}>{match.explanation.message}</p>}

      <div className="mt-3 flex items-center justify-between">
        <span className="text-xs" style={{ color: 'var(--ink-muted)' }}>Rank #{match.rank}</span>
        <button
          className="btn-primary text-xs px-3 py-1.5"
          style={{ borderRadius: '999px' }}
        >
          {intl.formatMessage({ id: 'match.select' })}
        </button>
      </div>
    </div>
  )
}
