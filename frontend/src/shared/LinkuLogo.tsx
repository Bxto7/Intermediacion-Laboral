// LinkuLogo — logo real de Linku con variantes de color
// Variante default: sobre fondos claros
// Variante white: sobre fondos oscuros (auth, footer, hero oscuro)
// Variante mono-terra: sobre fondos de color medio
// Variante contained: con contenedor terracota (favicon, avatar)

export type LogoVariant = 'default' | 'white' | 'mono-terra' | 'contained'

interface Colors {
  l: string
  dot: string
  blob: string
}

function getColors(variant: LogoVariant): Colors {
  switch (variant) {
    case 'white':
      return { l: '#ffffff', dot: 'rgba(255,255,255,0.65)', blob: 'rgba(255,255,255,0.55)' }
    case 'mono-terra':
      return { l: '#ffffff', dot: 'rgba(255,255,255,0.55)', blob: 'rgba(255,255,255,0.45)' }
    case 'contained':
      return { l: '#ffffff', dot: 'rgba(255,255,255,0.75)', blob: 'rgba(255,255,255,0.65)' }
    default:
      return { l: '#c2562e', dot: '#3d2818', blob: '#3d2818' }
  }
}

interface MarkProps {
  size?: number
  variant?: LogoVariant
}

// Solo el símbolo del logo (sin texto ni contenedor)
export const LinkuMark: React.FC<MarkProps> = ({ size = 32, variant = 'default' }) => {
  const c = getColors(variant)
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* L — trazo vertical */}
      <rect x="18" y="10" width="22" height="65" rx="11" fill={c.l} />
      {/* L — trazo horizontal */}
      <rect x="18" y="55" width="52" height="22" rx="11" fill={c.l} />
      {/* Círculo marrón — parte superior derecha */}
      <circle cx="68" cy="36" r="10" fill={c.dot} />
      {/* Gota/blob marrón — esquina inferior derecha */}
      <ellipse cx="62" cy="72" rx="18" ry="16" fill={c.blob} />
    </svg>
  )
}

interface LogoProps {
  size?: number
  variant?: LogoVariant
}

// Logo con contenedor cuadrado redondeado (modo "app icon")
export const LinkuLogo: React.FC<LogoProps> = ({ size = 36, variant = 'contained' }) => {
  const isContained = variant === 'contained' || variant === 'default'
  return (
    <span
      style={{
        width: size,
        height: size,
        borderRadius: size * 0.28,
        background: isContained
          ? 'linear-gradient(135deg, #d97757 0%, #c2562e 100%)'
          : 'transparent',
        border: variant === 'white' ? '1px solid rgba(255,255,255,0.18)' : 'none',
        display: 'grid',
        placeItems: 'center',
        flexShrink: 0,
        boxShadow: isContained
          ? '0 4px 14px -4px rgba(194,86,46,0.45), inset 0 1px 0 rgba(255,255,255,0.18)'
          : 'none',
        overflow: 'hidden',
      }}
    >
      <LinkuMark
        size={Math.round(size * 0.70)}
        variant={isContained ? 'contained' : variant}
      />
    </span>
  )
}

interface FullProps {
  size?: number
  variant?: LogoVariant
  showSubtitle?: boolean
}

// Wordmark completo: ícono + "Linku" + subtítulo DRTPE
export const LinkuLogoFull: React.FC<FullProps> = ({
  size = 36,
  variant = 'default',
  showSubtitle = true,
}) => {
  const nameColor = variant === 'white' || variant === 'mono-terra'
    ? '#ffffff'
    : 'var(--ink-strong)'
  const subtitleColor = variant === 'white' || variant === 'mono-terra'
    ? 'rgba(255,255,255,0.66)'
    : 'var(--ink-muted)'

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <LinkuLogo size={size} variant={variant} />
      <div>
        <div
          style={{
            fontSize: size * 0.47,
            fontWeight: 700,
            letterSpacing: '-0.025em',
            color: nameColor,
            lineHeight: 1.15,
          }}
        >
          Linku
        </div>
        {showSubtitle && (
          <div
            style={{
              fontSize: 10,
              color: subtitleColor,
              fontFamily: 'Geist Mono, monospace',
              letterSpacing: '0.055em',
              textTransform: 'uppercase',
              lineHeight: 1.2,
              marginTop: 1,
            }}
          >
            DRTPE Junín · Empleo formal
          </div>
        )}
      </div>
    </div>
  )
}

// Solo el ícono sin texto — alias conveniente
export const LinkuLogoIcon: React.FC<LogoProps> = ({ size = 36, variant = 'contained' }) => (
  <LinkuLogo size={size} variant={variant} />
)

// Alias para compatibilidad con código existente que usa LinkuLogoOnDark
export const LinkuLogoOnDark: React.FC<{ size?: number }> = ({ size = 36 }) => (
  <LinkuLogoFull size={size} variant="white" />
)
