import { useState } from 'react'
import { Link } from 'react-router-dom'
import { LinkuLogoIcon } from '../../shared/LinkuLogo'

interface Props { onLoginClick: () => void; scrolled: boolean }

export const LandingNav: React.FC<Props> = ({ onLoginClick, scrolled }) => {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <header
      className="fixed top-0 left-0 right-0 z-40 transition-all duration-300"
      style={{
        background: scrolled ? 'rgba(247,241,232,0.88)' : 'transparent',
        backdropFilter: scrolled ? 'blur(12px)' : 'none',
        borderBottom: scrolled ? '1px solid rgba(61,40,24,0.10)' : '1px solid transparent',
      }}
    >
      <div className="max-w-6xl mx-auto px-5 h-16 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-2.5">
          <LinkuLogoIcon size={36} variant="default" />
          <div className="leading-tight">
            <p className="text-sm font-bold" style={{ color: '#3d2818', letterSpacing: '-0.02em' }}>Linku</p>
            <p className="text-[10px] font-mono uppercase tracking-wider" style={{ color: '#8a6648' }}>DRTPE-Junín · Empleo formal</p>
          </div>
        </div>

        {/* Links desktop */}
        <nav className="hidden md:flex items-center gap-7">
          {['Descubrir', 'Empleadores', 'Recursos'].map((l) => (
            <a key={l} href={`#${l.toLowerCase()}`}
              className="text-sm font-medium transition-colors"
              style={{ color: '#6b4a35' }}
              onMouseEnter={e => (e.currentTarget.style.color = '#c2562e')}
              onMouseLeave={e => (e.currentTarget.style.color = '#6b4a35')}
            >{l}</a>
          ))}
          <Link
            to="/servicios"
            className="text-sm font-medium transition-colors"
            style={{ color: '#6b4a35' }}
            onMouseEnter={e => (e.currentTarget.style.color = '#c2562e')}
            onMouseLeave={e => (e.currentTarget.style.color = '#6b4a35')}
          >
            Buscar servicios
          </Link>
        </nav>

        {/* CTAs */}
        <div className="flex items-center gap-3">
          <button onClick={onLoginClick} className="btn-secondary text-sm px-4 py-2 hidden sm:inline-flex">
            Iniciar sesión
          </button>
          <Link to="/register" className="btn-primary text-sm px-4 py-2">
            Registrarse gratis
          </Link>
          <button onClick={() => setMenuOpen(!menuOpen)} className="md:hidden p-2 rounded-xl" style={{ color: '#6b4a35' }}>
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d={menuOpen ? 'M6 18L18 6M6 6l12 12' : 'M4 6h16M4 12h16M4 18h16'} />
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="md:hidden px-5 pb-4 space-y-2" style={{ background: 'rgba(247,241,232,0.96)', backdropFilter: 'blur(12px)' }}>
          {['Descubrir', 'Empleadores', 'Recursos'].map((l) => (
            <a key={l} href={`#${l.toLowerCase()}`} onClick={() => setMenuOpen(false)}
              className="block py-2 text-sm font-medium" style={{ color: '#6b4a35' }}>{l}</a>
          ))}
          <button onClick={() => { setMenuOpen(false); onLoginClick() }}
            className="block w-full text-left py-2 text-sm font-medium" style={{ color: '#c2562e' }}>
            Iniciar sesión
          </button>
        </div>
      )}
    </header>
  )
}
