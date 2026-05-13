import { Star, Wrench, Trash2 } from 'lucide-react'
import { SkillTag } from '../../../shared/SkillTag'
import type { PortfolioEntry } from '../../../hooks/usePortfolio'

interface Props {
  entry: PortfolioEntry
  onDelete?: (id: string) => void
}

export const PortfolioCard: React.FC<Props> = ({ entry, onDelete }) => (
  <div className="card-warm overflow-hidden hover:-translate-y-0.5 transition-all duration-200">
    {entry.photos.length > 0 ? (
      <div className="h-40 overflow-hidden">
        <img src={entry.photos[0]} alt={entry.title} className="w-full h-full object-cover" />
      </div>
    ) : (
      <div
        className="h-40 flex items-center justify-center"
        style={{ background: 'rgba(61,40,24,0.05)' }}
      >
        <Wrench size={32} style={{ color: 'var(--ink-muted)' }} strokeWidth={1.5} />
      </div>
    )}
    <div className="p-4">
      <h3 className="font-semibold text-sm mb-1" style={{ color: 'var(--ink-strong)' }}>{entry.title}</h3>
      <p className="text-xs leading-relaxed line-clamp-2 mb-3" style={{ color: 'var(--ink-muted)' }}>{entry.description}</p>
      {entry.extracted_skills.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {entry.extracted_skills.slice(0, 4).map((s) => (
            <SkillTag key={s} label={s} color="amber" />
          ))}
        </div>
      )}
      <div className="flex items-center justify-between">
        {entry.client_rating && (
          <div className="flex items-center gap-1">
            {Array.from({ length: Math.round(entry.client_rating) }).map((_, i) => (
              <Star key={i} size={12} fill="currentColor" style={{ color: 'var(--gold)' }} />
            ))}
            <span className="text-xs ml-0.5" style={{ color: 'var(--ink-muted)' }}>{entry.client_rating.toFixed(1)}</span>
          </div>
        )}
        {onDelete && (
          <button
            onClick={() => onDelete(entry.id)}
            className="ml-auto flex items-center gap-1 text-xs transition-colors"
            style={{ color: 'var(--ink-muted)' }}
            onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.color = 'var(--terra-500)' }}
            onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.color = 'var(--ink-muted)' }}
          >
            <Trash2 size={12} />
            Eliminar
          </button>
        )}
      </div>
    </div>
  </div>
)
