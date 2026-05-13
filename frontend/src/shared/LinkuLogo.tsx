// LinkuLogo — marca Linku (L + dot de "link")
// Variantes: mark solo, mark en container terracota, wordmark completo

interface MarkProps { size?: number; color?: string }

export const LinkuMark: React.FC<MarkProps> = ({ size = 18, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <path
      d="M8 5 L8 16 Q8 19 11 19 L17 19"
      stroke={color} strokeWidth="2.6" strokeLinecap="round" fill="none"
    />
    <circle cx="17" cy="19" r="1.7" fill={color} />
  </svg>
)

interface LogoProps { size?: number }

export const LinkuLogo: React.FC<LogoProps> = ({ size = 34 }) => (
  <span style={{
    width: size,
    height: size,
    borderRadius: size * 0.27,
    background: 'linear-gradient(135deg, #d97757, #c2562e)',
    display: 'grid',
    placeItems: 'center',
    color: '#fff',
    flexShrink: 0,
    boxShadow: '0 4px 12px -4px rgba(194,86,46,0.5), inset 0 1px 0 rgba(255,255,255,0.2)',
  }}>
    <LinkuMark size={Math.round(size * 0.53)} color="#fff" />
  </span>
)

interface FullProps { size?: number; showSubtitle?: boolean }

export const LinkuLogoFull: React.FC<FullProps> = ({ size = 34, showSubtitle = true }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
    <LinkuLogo size={size} />
    <div>
      <div style={{
        fontSize: size * 0.47,
        fontWeight: 600,
        letterSpacing: '-0.02em',
        color: 'var(--ink-strong)',
        lineHeight: 1.2,
      }}>
        Linku
      </div>
      {showSubtitle && (
        <div style={{
          fontSize: 10.5,
          color: 'var(--ink-muted)',
          fontFamily: 'Geist Mono, monospace',
          letterSpacing: '0.06em',
          textTransform: 'uppercase',
          lineHeight: 1.2,
        }}>
          DRTPE Junín · Empleo formal
        </div>
      )}
    </div>
  </div>
)

// Variante sobre fondo oscuro (sidenav oscuro, headers dark)
export const LinkuLogoOnDark: React.FC<LogoProps> = ({ size = 34 }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
    <span style={{
      width: size,
      height: size,
      borderRadius: size * 0.27,
      background: 'rgba(255,255,255,0.10)',
      border: '1px solid rgba(255,255,255,0.14)',
      display: 'grid',
      placeItems: 'center',
      flexShrink: 0,
    }}>
      <LinkuMark size={Math.round(size * 0.53)} color="#fff" />
    </span>
    <div>
      <div style={{ fontSize: size * 0.47, fontWeight: 600, letterSpacing: '-0.02em', color: '#fff', lineHeight: 1.2 }}>
        Linku
      </div>
      <div style={{ fontSize: 10.5, color: 'rgba(253,246,234,0.55)', letterSpacing: '0.06em', textTransform: 'uppercase', lineHeight: 1.2 }}>
        DRTPE Junín
      </div>
    </div>
  </div>
)

// Alias de compatibilidad para código existente que usa LinkuLogoIcon / LinkuLogoFull
export const LinkuLogoIcon: React.FC<{ size?: number; variant?: string }> = ({ size = 34 }) => (
  <LinkuLogo size={size} />
)
