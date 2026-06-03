import { useState } from 'react'
import { MapPin, CheckCircle } from 'lucide-react'
import { useIntl } from 'react-intl'
import { SkillTag } from '../shared/SkillTag'
import type { JobMatch } from '../hooks/useMatches'
import apiClient from '../api/client'

interface Props {
  match: JobMatch
  workerType?: string
  compact?: boolean
}

const labelColors = {
  Alta:  'bg-[rgba(122,140,92,0.14)] text-olive-deep border-[rgba(122,140,92,0.20)]',
  Media: 'bg-[rgba(201,150,31,0.14)] text-gold border-[rgba(201,150,31,0.20)]',
  Baja:  'bg-[rgba(184,68,42,0.10)] text-terra-500 border-[rgba(184,68,42,0.20)]',
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

  const [showApply, setShowApply] = useState(false)
  const [coverMsg, setCoverMsg] = useState('')
  const [applying, setApplying] = useState(false)
  const [applied, setApplied] = useState(false)
  const [applyError, setApplyError] = useState('')

  const handleApply = async (e: React.FormEvent) => {
    e.preventDefault()
    setApplying(true)
    setApplyError('')
    try {
      await apiClient.post('/applications', {
        job_offer_id: match.job_id,
        cover_message: coverMsg || null,
        proposed_rate: null,
      })
      setApplied(true)
      setShowApply(false)
      setCoverMsg('')
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status
      if (status === 409) {
        setApplied(true)
        setShowApply(false)
      } else {
        setApplyError('Error al postular. Intenta de nuevo.')
      }
    } finally {
      setApplying(false)
    }
  }

  return (
    <div
      className="card-warm hover:-translate-y-0.5 transition-all duration-200"
      style={{ padding: compact ? '12px' : '16px' }}
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

      {/* Apply section */}
      {applied ? (
        <div className="mt-3 flex items-center justify-between">
          <span className="text-xs" style={{ color: 'var(--ink-muted)' }}>Rank #{match.rank}</span>
          <span className="text-xs font-semibold flex items-center gap-1" style={{ color: 'var(--olive-deep)' }}>
            <CheckCircle size={13} /> {intl.formatMessage({ id: 'match.applied' })}
          </span>
        </div>
      ) : showApply ? (
        <form onSubmit={handleApply} className="mt-3 space-y-2">
          <textarea
            value={coverMsg}
            onChange={e => setCoverMsg(e.target.value)}
            placeholder="Mensaje breve al empleador (opcional)..."
            rows={2}
            maxLength={500}
            className="w-full px-3 py-2 rounded-xl text-xs resize-none focus:outline-none"
            style={{ border: '1px solid var(--line-strong)', background: 'var(--bg-soft)', color: 'var(--ink-strong)' }}
            onFocus={e => { e.currentTarget.style.borderColor = 'var(--terra-500)'; e.currentTarget.style.boxShadow = '0 0 0 2px rgba(184,68,42,0.12)' }}
            onBlur={e => { e.currentTarget.style.borderColor = 'var(--line-strong)'; e.currentTarget.style.boxShadow = 'none' }}
          />
          {applyError && <p role="alert" className="text-[11px]" style={{ color: 'var(--terra-500)' }}>{applyError}</p>}
          <div className="flex gap-2">
            <button type="button" onClick={() => { setShowApply(false); setApplyError('') }} className="btn-secondary flex-1 py-1.5 text-xs">
              Cancelar
            </button>
            <button type="submit" disabled={applying} className="btn-primary flex-1 py-1.5 text-xs">
              {applying ? 'Enviando...' : 'Confirmar'}
            </button>
          </div>
        </form>
      ) : (
        <div className="mt-3 flex items-center justify-between">
          <span className="text-xs" style={{ color: 'var(--ink-muted)' }}>Rank #{match.rank}</span>
          <button
            onClick={() => setShowApply(true)}
            className="btn-primary text-xs px-3 py-1.5"
            style={{ borderRadius: '999px' }}
          >
            {intl.formatMessage({ id: 'match.select' })}
          </button>
        </div>
      )}
    </div>
  )
}
