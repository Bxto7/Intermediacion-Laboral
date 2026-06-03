interface Props {
  label: string
  removable?: boolean
  onRemove?: (label: string) => void
  color?: 'amber' | 'green' | 'gray' | 'blue' | 'primary'
}

const colorMap: Record<string, string> = {
  amber:   'bg-[rgba(201,150,31,0.12)] text-gold border-[rgba(201,150,31,0.22)]',
  green:   'bg-[rgba(122,140,92,0.13)] text-olive-deep border-[rgba(122,140,92,0.22)]',
  gray:    'bg-[rgba(42,29,20,0.07)] text-ink-warm border-[rgba(42,29,20,0.12)]',
  blue:    'bg-[rgba(15,110,110,0.10)] text-[#0f6e6e] border-[rgba(15,110,110,0.18)]',
  primary: 'bg-[rgba(184,68,42,0.10)] text-terra-500 border-[rgba(184,68,42,0.20)]',
}

export const SkillTag: React.FC<Props> = ({ label, removable, onRemove, color = 'amber' }) => (
  <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border ${colorMap[color] ?? colorMap.amber}`}>
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
