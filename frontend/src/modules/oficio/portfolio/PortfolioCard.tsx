import { SkillTag } from '../../../shared/SkillTag'
import type { PortfolioEntry } from '../../../hooks/usePortfolio'

interface Props {
  entry: PortfolioEntry
  onDelete?: (id: string) => void
}

export const PortfolioCard: React.FC<Props> = ({ entry, onDelete }) => (
  <div className="bg-white rounded-2xl border border-amber-100 shadow-sm hover:shadow-md transition-all overflow-hidden">
    {entry.photos.length > 0 ? (
      <div className="h-40 bg-gray-100 overflow-hidden">
        <img src={entry.photos[0]} alt={entry.title} className="w-full h-full object-cover" />
      </div>
    ) : (
      <div className="h-40 bg-gradient-to-br from-amber-100 to-amber-50 flex items-center justify-center">
        <span className="text-4xl">🛠️</span>
      </div>
    )}
    <div className="p-4">
      <h3 className="font-semibold text-gray-900 text-sm mb-1">{entry.title}</h3>
      <p className="text-xs text-gray-500 line-clamp-2 mb-3">{entry.description}</p>
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
            <span className="text-yellow-400 text-sm">{'★'.repeat(Math.round(entry.client_rating))}</span>
            <span className="text-xs text-gray-500">{entry.client_rating.toFixed(1)}</span>
          </div>
        )}
        {onDelete && (
          <button
            onClick={() => onDelete(entry.id)}
            className="text-xs text-red-400 hover:text-red-600 transition-colors ml-auto"
          >
            Eliminar
          </button>
        )}
      </div>
    </div>
  </div>
)
