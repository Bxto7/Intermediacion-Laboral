import { Link, useNavigate } from 'react-router-dom'
import { useIntl } from 'react-intl'
import { useAuthContext } from '../context/AuthContext'
import { useWorkerContext } from '../context/WorkerContext'
import { BriefcaseFilled } from './BriefcaseIcon'

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
    <nav className="sticky top-0 z-40 transition-all duration-300 border-b"
         style={{ background: 'rgba(247,241,232,0.88)', backdropFilter: 'blur(12px)', borderColor: 'rgba(61,40,24,0.10)' }}>
      <div className="max-w-6xl mx-auto px-5 h-14 flex items-center justify-between">

        {/* Logo */}
        <Link to="/dashboard" className="flex items-center gap-2.5 group">
          <div className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 shadow-warm-sm"
               style={{ background: 'linear-gradient(135deg, #d97757, #c2562e)' }}>
            <BriefcaseFilled className="w-4 h-4 text-white" />
          </div>
          <div className="hidden sm:block leading-tight">
            <span className="font-bold text-sm text-bark-900 tracking-tight block">DRTPE Junín</span>
            <span className="kicker" style={{ color: 'var(--ink-muted)', fontSize: '9px' }}>Bolsa Oficial</span>
          </div>
        </Link>

        {/* Nav links + acciones */}
        <div className="flex items-center gap-5">
          {isAuthenticated && workerType && (
            <>
              <Link
                to="/dashboard"
                className="text-sm text-bark-500 hover:text-bark-900 transition-colors font-medium"
              >
                {intl.formatMessage({ id: 'nav.dashboard' })}
              </Link>
              {workerType !== 'primer_empleo' && (
                <Link
                  to="/matches"
                  className="text-sm text-bark-500 hover:text-bark-900 transition-colors font-medium"
                >
                  {intl.formatMessage({ id: 'nav.matching' })}
                </Link>
              )}
              {workerType === 'oficio' && (
                <Link
                  to="/oficio/portfolio"
                  className="text-sm text-bark-500 hover:text-bark-900 transition-colors font-medium"
                >
                  Portfolio
                </Link>
              )}
            </>
          )}

          {user?.role === 'admin' && (
            <Link to="/admin" className="text-sm text-primary-600 font-semibold">Admin</Link>
          )}

          {isAuthenticated ? (
            <div className="flex items-center gap-3">
              {/* Avatar con inicial */}
              <div className="w-8 h-8 rounded-full bg-bark-100 border border-warm-300 flex items-center justify-center">
                <span className="text-xs font-bold text-bark-700">{initials}</span>
              </div>
              <button
                onClick={handleLogout}
                className="text-sm text-bark-400 hover:text-bark-700 transition-colors"
              >
                {intl.formatMessage({ id: 'nav.logout' })}
              </button>
            </div>
          ) : (
            <Link
              to="/login"
              className="btn-primary text-xs px-4 py-2"
            >
              {intl.formatMessage({ id: 'nav.login' })}
            </Link>
          )}
        </div>
      </div>
    </nav>
  )
}
