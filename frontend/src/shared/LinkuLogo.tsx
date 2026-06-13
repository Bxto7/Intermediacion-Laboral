// LinkuLogo — logo REAL de Linku (imagen) con variantes según el fondo.
// Fondos claros  -> /institucional/linku.png        (logo a color, fondo claro)
// Fondos oscuros -> /institucional/linku-blanco.png (logo blanco, fondo navy)
// La imagen ya incluye el wordmark "Linku".

export type LogoVariant = 'default' | 'white' | 'mono-terra' | 'contained'

const LIGHT_SRC = '/institucional/linku.png'
const DARK_SRC = '/institucional/linku-blanco.png'

const isDark = (v: LogoVariant) => v === 'white' || v === 'mono-terra'
const srcFor = (v: LogoVariant) => (isDark(v) ? DARK_SRC : LIGHT_SRC)

interface MarkProps {
  size?: number
  variant?: LogoVariant
}

// Solo el logo cuadrado (tile), sin subtítulo.
export const LinkuMark: React.FC<MarkProps> = ({ size = 32, variant = 'default' }) => (
  <img
    src={srcFor(variant)}
    alt="Linku"
    width={size}
    height={size}
    style={{
      borderRadius: size * 0.22,
      objectFit: 'cover',
      display: 'block',
      flexShrink: 0,
    }}
  />
)

interface LogoProps {
  size?: number
  variant?: LogoVariant
}

// Logo en tile redondeado (modo "app icon").
export const LinkuLogo: React.FC<LogoProps> = ({ size = 36, variant = 'contained' }) => (
  <img
    src={srcFor(variant)}
    alt="Linku"
    width={size}
    height={size}
    style={{
      borderRadius: size * 0.24,
      objectFit: 'cover',
      display: 'block',
      flexShrink: 0,
      boxShadow:
        variant === 'contained' || variant === 'default'
          ? '0 4px 14px -6px rgba(42,29,20,0.4)'
          : 'none',
    }}
  />
)

interface FullProps {
  size?: number
  variant?: LogoVariant
  showSubtitle?: boolean
}

// Lockup: logo real (incluye "Linku") + subtítulo institucional.
export const LinkuLogoFull: React.FC<FullProps> = ({
  size = 36,
  variant = 'default',
  showSubtitle = true,
}) => {
  const dark = isDark(variant)
  const subtitleColor = dark ? 'rgba(255,255,255,0.7)' : 'var(--ink-muted)'
  const dividerColor = dark ? 'rgba(255,255,255,0.22)' : 'var(--line-strong)'

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <img
        src={srcFor(variant)}
        alt="Linku · Empleo formal DRTPE Junín"
        style={{
          height: Math.round(size * 1.2),
          width: Math.round(size * 1.2),
          borderRadius: size * 0.22,
          objectFit: 'cover',
          display: 'block',
          flexShrink: 0,
        }}
      />
      {showSubtitle && (
        <div style={{ paddingLeft: 10, borderLeft: `1px solid ${dividerColor}` }}>
          <div
            style={{
              fontSize: 10,
              color: subtitleColor,
              fontFamily: 'Geist Mono, monospace',
              letterSpacing: '0.07em',
              textTransform: 'uppercase',
              lineHeight: 1.3,
            }}
          >
            DRTPE Junín
            <br />
            Empleo formal
          </div>
        </div>
      )}
    </div>
  )
}

// Solo el ícono sin subtítulo — alias conveniente.
export const LinkuLogoIcon: React.FC<LogoProps> = ({ size = 36, variant = 'contained' }) => (
  <LinkuLogo size={size} variant={variant} />
)

// Alias para fondos oscuros.
export const LinkuLogoOnDark: React.FC<{ size?: number }> = ({ size = 36 }) => (
  <LinkuLogoFull size={size} variant="white" />
)
