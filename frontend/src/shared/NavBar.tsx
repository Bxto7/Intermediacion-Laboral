import { Link, useNavigate } from 'react-router-dom'
import { useIntl } from 'react-intl'
import { useAuthContext } from '../context/AuthContext'
import { useWorkerContext } from '../context/WorkerContext'
import { LinkuLogoIcon } from './LinkuLogo'
import { NotificationBell } from './NotificationBell'

export const NavBar: React.FC = () => {
  const intl = useIntl()
  const navigate = useNavigate()
  const { user, isAuthenticated, logout } = useAuthContext()
  const { workerType } = useWorkerContext()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  const initials = user?.email?.charAt(0).toUpperCase() ?? 'U'

  return (
    <nav
      className="sticky top-0 z-40 transition-all duration-300 border-b"
      style={{ background: 'rgba(247,241,232,0.92)', backdropFilter: 'blur(12px)', borderColor: 'var(--line)' }}
    >
      <div className="max-w-6xl mx-auto px-5 h-14 flex items-center justify-between">

        {/* Logo */}
        <Link to="/dashboard" className="flex items-center gap-2.5 group">
          <LinkuLogoIcon size={30} variant="contained" />
          <div className="hidden sm:block leading-tight">
            <span className="font-bold text-sm tracking-tight block" style={{ color: 'var(--ink-strong)' }}>Linku</span>
            <span className="font-mono text-[9px] uppercase tracking-widest" style={{ color: 'var(--ink-muted)' }}>DRTPE-Junín</span>
          </div>
        </Link>

        {/* Nav links */}
        <div className="flex items-center gap-1">
          {isAuthenticated && (
            <Link to="/servicios" className="btn-ghost text-xs px-3 py-2" style={{ color: 'var(--ink-warm)' }}>
              Buscar servicios
            </Link>
          )}
          {isAuthenticated && workerType && (
            <>
              <Link to="/dashboard" className="btn-ghost text-xs px-3 py-2" style={{ color: 'var(--ink-warm)' }}>
                {intl.formatMessage({ id: 'nav.dashboard' })}
              </Link>
              {workerType !== 'primer_empleo' && (
                <Link to="/matches" className="btn-ghost text-xs px-3 py-2" style={{ color: 'var(--ink-warm)' }}>
                  {intl.formatMessage({ id: 'nav.matching' })}
                </Link>
              )}
              {workerType === 'oficio' && (
                <Link to="/oficio/portfolio" className="btn-ghost text-xs px-3 py-2" style={{ color: 'var(--ink-warm)' }}>
                  Portfolio
                </Link>
              )}
              {workerType && (
                <Link to="/marketplace" className="btn-ghost text-xs px-3 py-2" style={{ color: 'var(--ink-warm)' }}>
                  Buscar servicios
                </Link>
              )}
              {workerType !== 'primer_empleo' && (
                <Link to="/applications" className="btn-ghost text-xs px-3 py-2" style={{ color: 'var(--ink-warm)' }}>
                  Postulaciones
                </Link>
              )}
            </>
          )}

          {user?.role === 'admin' && (
            <Link to="/admin" className="btn-ghost text-xs px-3 py-2 font-semibold" style={{ color: 'var(--terra-500)' }}>
              Admin
            </Link>
          )}

          {isAuthenticated ? (
            <div className="flex items-center gap-2 ml-2">
              <NotificationBell />
              <div
                className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
                style={{ background: 'linear-gradient(135deg, var(--terra-400), var(--terra-500))' }}
              >
                {initials}
              </div>
              <button onClick={handleLogout} className="btn-ghost text-xs px-3 py-2" style={{ color: 'var(--ink-muted)' }}>
                {intl.formatMessage({ id: 'nav.logout' })}
              </button>
            </div>
          ) : (
            <Link to="/login" className="btn-primary text-xs px-4 py-2 ml-2">
              {intl.formatMessage({ id: 'nav.login' })}
            </Link>
          )}
        </div>
      </div>
    </nav>
  )
}
