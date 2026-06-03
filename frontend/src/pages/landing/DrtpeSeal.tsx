// Sello oficial Linku · DRTPE-Junín — emblema circular giratorio.
// Anillo de texto en curva + marcas tipo moneda + marca Linku al centro.
interface Props {
  size?: number
  /** 'navy' para fondos claros, 'light' para fondos oscuros, 'gold' acento */
  tone?: 'navy' | 'light' | 'gold'
  /** desactiva el giro lento del aro */
  spin?: boolean
  className?: string
}

export const DrtpeSeal: React.FC<Props> = ({ size = 120, tone = 'navy', spin = true, className }) => {
  const stroke =
    tone === 'light' ? 'rgba(244,236,224,0.9)' : tone === 'gold' ? '#e0a32e' : '#0f6e6e'
  const ink =
    tone === 'light' ? '#f4ece0' : tone === 'gold' ? '#b07d12' : '#0f6e6e'
  const gold = tone === 'light' ? '#eab84e' : '#e0a32e'
  const lMark = tone === 'light' ? '#f4ece0' : '#0f6e6e'

  // marcas radiales tipo canto de moneda (entre los aros, sin tocar el texto)
  const ticks = Array.from({ length: 72 }, (_, i) => {
    const a = (i * 5) * Math.PI / 180
    const long = i % 6 === 0
    const r1 = long ? 58 : 60
    const r2 = 64
    return (
      <line
        key={i}
        x1={100 + r1 * Math.cos(a)} y1={100 + r1 * Math.sin(a)}
        x2={100 + r2 * Math.cos(a)} y2={100 + r2 * Math.sin(a)}
        stroke={stroke}
        strokeWidth={long ? 1.4 : 0.7}
        opacity={long ? 0.9 : 0.5}
      />
    )
  })

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 200 200"
      fill="none"
      className={className}
      role="img"
      aria-label="Sello oficial Linku · DRTPE Junín"
    >
      <defs>
        {/* radio del texto: 73 (dentro del aro de 84, con margen) */}
        <path id="seal-top" d="M 100,100 m -73,0 a 73,73 0 1,1 146,0" />
        <path id="seal-bottom" d="M 100,100 m 73,0 a 73,73 0 1,1 -146,0" />
      </defs>

      {/* aros fijos exteriores */}
      <circle cx="100" cy="100" r="95" stroke={stroke} strokeWidth="1" opacity="0.4" />
      <circle cx="100" cy="100" r="84" stroke={stroke} strokeWidth="2" />

      {/* grupo giratorio: texto + marcas */}
      <g className={spin ? 'inst-seal-spin' : undefined}>
        <text fill={ink} style={{ fontFamily: 'Geist, system-ui, sans-serif', fontSize: 10.5, fontWeight: 600, letterSpacing: 3.6 }}>
          <textPath href="#seal-top" startOffset="50%" textAnchor="middle">
            DRTPE · JUNÍN · PERÚ
          </textPath>
        </text>
        <text fill={ink} style={{ fontFamily: 'Geist, system-ui, sans-serif', fontSize: 10.5, fontWeight: 600, letterSpacing: 3.6 }}>
          <textPath href="#seal-bottom" startOffset="50%" textAnchor="middle">
            BOLSA DE EMPLEO FORMAL
          </textPath>
        </text>
        {ticks}
      </g>

      {/* estrellas separadoras (fijas, a los lados) */}
      <g fill={gold}>
        <circle cx="15.5" cy="100" r="2.3" />
        <circle cx="184.5" cy="100" r="2.3" />
      </g>

      {/* aro interior + marca Linku al centro (fijo) */}
      <circle cx="100" cy="100" r="50" stroke={stroke} strokeWidth="1" opacity="0.45" />
      <circle cx="100" cy="100" r="50" fill={tone === 'light' ? 'rgba(255,255,255,0.04)' : 'rgba(15,110,110,0.04)'} />
      <g transform="translate(100,100)">
        {/* L de Linku */}
        <rect x="-18" y="-23" width="12.5" height="42" rx="6.2" fill={lMark} />
        <rect x="-18" y="6.5" width="30" height="12.5" rx="6.2" fill={lMark} />
        {/* punto dorado */}
        <circle cx="16" cy="-12" r="6.2" fill={gold} />
      </g>
    </svg>
  )
}
