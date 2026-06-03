import { useState } from 'react'
import { Link } from 'react-router-dom'
import { LinkuMark } from '../../shared/LinkuLogo'

interface Props { onLoginClick: () => void; onRegisterClick: () => void; scrolled: boolean }

// Marca Linku en caja navy (fallback si la imagen no carga)
const NavyMark: React.FC<{ size?: number }> = ({ size = 38 }) => (
  <span
    style={{
      width: size, height: size, borderRadius: size * 0.27,
      background: 'linear-gradient(150deg, #138585 0%, #0f6e6e 60%, #0c5a5a 100%)',
      display: 'grid', placeItems: 'center', flexShrink: 0,
      boxShadow: '0 4px 14px -5px rgba(42,29,20,0.6), inset 0 1px 0 rgba(255,255,255,0.14)',
      border: '1px solid rgba(255,255,255,0.06)',
    }}
  >
    <LinkuMark size={Math.round(size * 0.68)} variant="white" />
  </span>
)

// Marca de cabecera: logo Linku (imagen) + subtítulo institucional.
// Si la imagen falla, cae al símbolo dibujado + texto.
const HeaderBrand: React.FC = () => {
  const [err, setErr] = useState(false)
  if (err) {
    return (
      <div className="flex items-center gap-3">
        <NavyMark size={40} />
        <div className="leading-tight">
          <p className="text-[15px] font-bold" style={{ color: '#2a1d14', letterSpacing: '-0.02em' }}>Linku</p>
          <p className="text-[10px] font-medium uppercase tracking-[0.14em]" style={{ color: '#6e5d49', fontFamily: 'Geist Mono, monospace' }}>
            Plataforma oficial de empleo
          </p>
        </div>
      </div>
    )
  }
  return (
    <div className="flex items-center gap-3">
      <img
        src="/institucional/linku.png"
        alt="Linku · Plataforma oficial de empleo DRTPE Junín"
        onError={() => setErr(true)}
        className="h-11 w-auto block"
      />
      <span className="hidden sm:block pl-3" style={{ borderLeft: '1px solid rgba(42,29,20,0.12)' }}>
        <span className="block text-[10px] font-medium uppercase tracking-[0.14em] leading-snug" style={{ color: '#6e5d49', fontFamily: 'Geist Mono, monospace' }}>
          Plataforma oficial<br />de empleo
        </span>
      </span>
    </div>
  )
}

const LINKS = [
  { label: 'Empleos', href: '#empleos' },
  { label: 'Cómo funciona', href: '#como-funciona' },
  { label: 'Empresas', href: '#empresas' },
]

export const LandingNav: React.FC<Props> = ({ onLoginClick, onRegisterClick, scrolled }) => {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <header className="fixed top-0 left-0 right-0 z-40">
      {/* ── Barra utilitaria de gobierno ── */}
      <div
        className="hidden md:block text-[11px]"
        style={{
          background: '#2a1d14',
          color: 'rgba(244,236,224,0.72)',
          fontFamily: 'Geist Mono, monospace',
          letterSpacing: '0.06em',
        }}
      >
        <div className="max-w-6xl mx-auto px-5 h-8 flex items-center justify-between">
          <span className="flex items-center gap-2">
            <span style={{ color: '#eab84e' }}>●</span>
            GOBIERNO REGIONAL DE JUNÍN · DRTPE
          </span>
          <span className="flex items-center gap-5">
            <a href="#" className="hover:text-white transition-colors">Transparencia</a>
            <a href="#" className="hover:text-white transition-colors">Mesa de partes</a>
            <a href="#" className="hover:text-white transition-colors">Ayuda</a>
          </span>
        </div>
      </div>

      {/* ── Nav principal ── */}
      <div
        className="transition-all duration-300"
        style={{
          background: scrolled ? 'rgba(251,247,240,0.9)' : 'rgba(251,247,240,0.6)',
          backdropFilter: 'blur(14px)',
          borderBottom: scrolled ? '1px solid rgba(42,29,20,0.10)' : '1px solid rgba(42,29,20,0.05)',
        }}
      >
        <div className="max-w-6xl mx-auto px-5 h-[68px] flex items-center justify-between">
          {/* Logo */}
          <HeaderBrand />

          {/* Links desktop */}
          <nav className="hidden md:flex items-center gap-8">
            {LINKS.map((l) => (
              <a key={l.label} href={l.href}
                className="text-sm font-medium transition-colors"
                style={{ color: '#5a4a39' }}
                onMouseEnter={e => (e.currentTarget.style.color = '#147a7a')}
                onMouseLeave={e => (e.currentTarget.style.color = '#5a4a39')}
              >{l.label}</a>
            ))}
            <Link to="/servicios"
              className="text-sm font-medium transition-colors"
              style={{ color: '#5a4a39' }}
              onMouseEnter={e => (e.currentTarget.style.color = '#147a7a')}
              onMouseLeave={e => (e.currentTarget.style.color = '#5a4a39')}
            >Buscar servicios</Link>
          </nav>

          {/* CTAs */}
          <div className="flex items-center gap-2.5">
            <button onClick={onLoginClick} className="ibtn ibtn-outline !py-2 !px-4 !text-[13px]">
              Iniciar sesión
            </button>
            <button onClick={onRegisterClick} className="ibtn ibtn-gold !py-2 !px-4 !text-[13px]">
              Registrarse
            </button>
            <button onClick={() => setMenuOpen(!menuOpen)} className="md:hidden p-2 rounded-lg" style={{ color: '#0f6e6e' }}>
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d={menuOpen ? 'M6 18L18 6M6 6l12 12' : 'M4 6h16M4 12h16M4 18h16'} />
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {menuOpen && (
          <div className="md:hidden px-5 pb-4 space-y-1" style={{ background: 'rgba(251,247,240,0.97)', backdropFilter: 'blur(14px)' }}>
            {LINKS.map((l) => (
              <a key={l.label} href={l.href} onClick={() => setMenuOpen(false)}
                className="block py-2.5 text-sm font-medium" style={{ color: '#5a4a39' }}>{l.label}</a>
            ))}
            <Link to="/servicios" onClick={() => setMenuOpen(false)} className="block py-2.5 text-sm font-medium" style={{ color: '#5a4a39' }}>
              Buscar servicios
            </Link>
            <button onClick={() => { setMenuOpen(false); onLoginClick() }}
              className="block w-full text-left py-2.5 text-sm font-semibold" style={{ color: '#147a7a' }}>
              Iniciar sesión
            </button>
          </div>
        )}
      </div>
    </header>
  )
}
