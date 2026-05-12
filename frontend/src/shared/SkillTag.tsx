interface Props {
  label: string
  removable?: boolean
  onRemove?: (label: string) => void
  color?: 'primary' | 'success' | 'warm' | 'neutral'
}

const colorMap = {
  primary: 'bg-primary-100 text-primary-700 border-primary-200',
  success: 'bg-secondary-500/10 text-secondary-600 border-secondary-500/20',
  warm:    'bg-bark-100 text-bark-700 border-warm-300',
  neutral: 'bg-warm-100 text-bark-500 border-warm-200',
}

export const SkillTag: React.FC<Props> = ({ label, removable, onRemove, color = 'warm' }) => (
  <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border ${colorMap[color]}`}>
    {label}
    {removable && (
      <button
        onClick={() => onRemove?.(label)}
        className="ml-0.5 hover:opacity-70 leading-none"
        aria-label="Quitar habilidad"
      >
        ×
      </button>
    )}
  </span>
)
