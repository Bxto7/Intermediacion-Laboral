import { useState } from 'react'
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { useAuthContext } from '../context/AuthContext'
import { useWorkerContext } from '../context/WorkerContext'
import { NotificationBell } from './NotificationBell'
import { LinkuLogoFull, LinkuMark } from './LinkuLogo'
import { LoadingSpinner } from './LoadingSpinner'
import {
  Home, Folder, Store, Briefcase, FileText, BarChart2,
  Settings, Edit, Users, Building, HardHat,
  Plus, Search, ShieldCheck, ChevronDown, MessageCircle,
  type LucideIcon,
} from 'lucide-react'

interface NavItemDef {
  to: string
  label: string
  Icon: LucideIcon
  exact?: boolean
}

function getNavItems(workerType: string | null, role: string): { primary: NavItemDef[]; account: NavItemDef[] } {
  if (role === 'admin') return {
    primary: [
      { to: '/admin',             label: 'KPIs',          Icon: BarChart2, exact: true },
      { to: '/admin/workers',     label: 'Trabajadores',  Icon: HardHat },
      { to: '/admin/employers',   label: 'Empleadores',   Icon: Building },
      { to: '/admin/jobs',        label: 'Ofertas',       Icon: Briefcase },
    ],
    account: [],
  }
  if (role === 'employer') return {
    primary: [
      { to: '/employer/dashboard', label: 'Dashboard',        Icon: Home, exact: true },
      { to: '/employer/publish',   label: 'Publicar empleo',  Icon: Plus },
      { to: '/employer/candidates',label: 'Candidatos',       Icon: Users },
      { to: '/employer/messages',  label: 'Mensajes',         Icon: MessageCircle },
    ],
    account: [
      { to: '/settings', label: 'Configuración', Icon: Settings },
    ],
  }
  if (workerType === 'oficio') return {
    primary: [
      { to: '/dashboard',         label: 'Inicio',          Icon: Home, exact: true },
      { to: '/oficio/portfolio',  label: 'Mi portfolio',    Icon: Folder },
      { to: '/marketplace',       label: 'Marketplace',     Icon: Store },
      { to: '/matches',           label: 'Empleos para mí', Icon: Briefcase },
      { to: '/applications',      label: 'Postulaciones',   Icon: FileText },
    ],
    account: [
      { to: '/survey/economic', label: 'Mi progreso', Icon: BarChart2 },
      { to: '/settings',        label: 'Configuración', Icon: Settings },
    ],
  }
  if (workerType === 'primer_empleo') return {
    primary: [
      { to: '/dashboard',       label: 'Inicio',           Icon: Home, exact: true },
      { to: '/wizard/step/1',   label: 'Completar perfil', Icon: Edit },
      { to: '/matches',         label: 'Empleos para mí',  Icon: Briefcase },
      { to: '/applications',    label: 'Postulaciones',    Icon: FileText },
    ],
    account: [
      { to: '/survey/economic', label: 'Mi progreso',   Icon: BarChart2 },
      { to: '/settings',        label: 'Configuración', Icon: Settings },
    ],
  }
  return {
    primary: [
      { to: '/dashboard',       label: 'Inicio',           Icon: Home, exact: true },
      { to: '/matches',         label: 'Bolsa de empleos', Icon: Briefcase },
      { to: '/applications',    label: 'Postulaciones',    Icon: FileText },
    ],
    account: [
      { to: '/survey/economic', label: 'Mi progreso',   Icon: BarChart2 },
      { to: '/settings',        label: 'Configuración', Icon: Settings },
    ],
  }
}

// ─── Sidenav item ───────────────────────────────────────────────────────────
const SideItem: React.FC<{ item: NavItemDef }> = ({ item }) => {
  const location = useLocation()
  const active = item.exact
    ? location.pathname === item.to
    : location.pathname.startsWith(item.to)

  return (
    <NavLink
      to={item.to}
      className={`nav-item ${active ? 'active' : ''}`}
    >
      <item.Icon size={16} strokeWidth={active ? 2 : 1.7} />
      <span className="flex-1 text-[13.5px]">{item.label}</span>
    </NavLink>
  )
}

// ─── Sidenav completeness card (dark nudge) ──────────────────────────────────
const CompletenessCard: React.FC = () => {
  const { worker } = useWorkerContext()
  const { user } = useAuthContext()
  const navigate = useNavigate()
  const pct = worker?.profile_completeness ?? 0
  // Solo para trabajadores con perfil; nunca para empleador/admin
  if (user?.role !== 'worker' || !worker || pct >= 100) return null
  return (
    <div
      className="mx-2 mb-3 rounded-[14px] p-3.5 cursor-pointer"
      style={{
        background: 'radial-gradient(200px 120px at 80% 0%, rgba(217,119,87,0.35), transparent 60%), linear-gradient(140deg, var(--dark-deep), var(--dark))',
        boxShadow: '0 0 0 1px rgba(253,246,234,0.08), 0 0 24px -8px rgba(194,86,46,0.25)',
      }}
      onClick={() => navigate('/wizard/step/1')}
    >
      <p className="text-[11px] font-mono uppercase tracking-widest mb-1.5" style={{ color: 'rgba(253,246,234,0.5)' }}>
        Perfil
      </p>
      <p className="text-[13px] font-medium leading-snug mb-2.5" style={{ color: 'var(--on-dark)' }}>
        Estás casi <span className="serif-it" style={{ color: 'var(--coral)' }}>listo</span> · {pct}%
      </p>
      <div className="h-1.5 rounded-full overflow-hidden mb-2.5" style={{ background: 'rgba(253,246,234,0.12)' }}>
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, background: 'linear-gradient(90deg, var(--terra-400), var(--gold-light))' }}
        />
      </div>
      <span className="text-[11.5px] font-medium" style={{ color: 'var(--terra-400)' }}>
        Completar perfil →
      </span>
    </div>
  )
}

// ─── Sidenav ────────────────────────────────────────────────────────────────
const SideNav: React.FC<{ onClose?: () => void }> = ({ onClose }) => {
  const { user, logout } = useAuthContext()
  const { workerType, worker } = useWorkerContext()
  const navigate = useNavigate()
  const { primary, account } = getNavItems(workerType, user?.role ?? '')

  const displayName =
    (user?.role === 'worker' && worker?.display_name) || user?.email?.split('@')[0] || 'Usuario'

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <aside
      className="flex flex-col h-full"
      style={{ background: 'var(--bg-soft)', borderRight: '1px solid var(--line)', width: 240 }}
    >
      {/* Brand */}
      <div className="px-4 py-4" style={{ borderBottom: '1px solid var(--line)' }}>
        <NavLink to="/dashboard" onClick={onClose}>
          <LinkuLogoFull size={32} showSubtitle />
        </NavLink>
      </div>

      {/* Nav items */}
      <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
        {primary.length > 0 && (
          <>
            <p className="kicker px-2.5 pb-1.5 pt-0.5">Principal</p>
            {primary.map(item => <SideItem key={item.to} item={item} />)}
          </>
        )}
        {account.length > 0 && (
          <>
            <p className="kicker px-2.5 pb-1.5 pt-4">Cuenta</p>
            {account.map(item => <SideItem key={item.to} item={item} />)}
          </>
        )}
      </nav>

      {/* Completeness nudge */}
      <CompletenessCard />

      {/* User row */}
      <div
        className="px-3 py-3 flex items-center gap-2.5"
        style={{ borderTop: '1px solid var(--line)' }}
      >
        <div
          className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
          style={{ background: 'linear-gradient(135deg, var(--terra-400), var(--terra-500))' }}
        >
          {displayName.charAt(0).toUpperCase()}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-[12px] font-medium truncate" style={{ color: 'var(--ink-strong)' }}>
            {displayName}
          </p>
          <p className="text-[10.5px] truncate" style={{ color: 'var(--ink-muted)' }}>
            {user?.role === 'worker' ? workerType?.replace('_', ' ') : user?.role}
          </p>
        </div>
        <button
          onClick={handleLogout}
          className="text-[11px] px-2 py-1 rounded-lg transition-colors"
          style={{ color: 'var(--ink-muted)' }}
          onMouseEnter={e => { (e.currentTarget as HTMLElement).style.color = 'var(--terra-500)' }}
          onMouseLeave={e => { (e.currentTarget as HTMLElement).style.color = 'var(--ink-muted)' }}
          title="Cerrar sesión"
        >
          Salir
        </button>
      </div>
    </aside>
  )
}

// ─── TopBar ─────────────────────────────────────────────────────────────────
const TopBar: React.FC<{ onMenuToggle: () => void }> = ({ onMenuToggle }) => {
  const { user } = useAuthContext()
  const { worker } = useWorkerContext()
  const navigate = useNavigate()
  const displayName =
    (user?.role === 'worker' && worker?.display_name) || user?.email?.split('@')[0] || 'Usuario'

  return (
    <header
      className="sticky top-0 z-40 flex items-center justify-between px-4 md:px-6 h-[60px]"
      style={{
        background: 'rgba(247,241,232,0.88)',
        backdropFilter: 'blur(12px)',
        borderBottom: '1px solid var(--line)',
      }}
    >
      {/* Left: hamburger (mobile) + logo (mobile) */}
      <div className="flex items-center gap-3">
        <button
          className="md:hidden p-1.5 rounded-lg"
          style={{ color: 'var(--ink-muted)' }}
          onClick={onMenuToggle}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>
        <NavLink to="/dashboard" className="md:hidden flex items-center gap-2">
          <LinkuMark size={20} variant="default" />
          <span className="font-semibold text-sm" style={{ color: 'var(--ink-strong)', letterSpacing: '-0.02em' }}>Linku</span>
        </NavLink>
      </div>

      {/* Search pill */}
      <button
        className="hidden md:flex items-center gap-2 px-3.5 py-2 rounded-full text-sm transition-all"
        style={{
          background: 'white',
          border: '1px solid var(--line)',
          color: 'var(--ink-muted)',
          boxShadow: 'var(--shadow-sm)',
          minWidth: 220,
        }}
        onMouseEnter={e => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--line-strong)' }}
        onMouseLeave={e => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--line)' }}
      >
        <Search size={14} />
        <span className="flex-1 text-left text-[13px]">Buscar empleos…</span>
        <kbd className="text-[10px] font-mono px-1.5 py-0.5 rounded" style={{ background: 'var(--bg-warm)', color: 'var(--ink-muted)' }}>⌘K</kbd>
      </button>

      {/* Right: DRTPE + bell + user */}
      <div className="flex items-center gap-2">
        <span className="verified hidden sm:inline-flex">
          <ShieldCheck size={12} />
          DRTPE Junín
        </span>
        <NotificationBell />
        <button
          className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full transition-all"
          style={{ border: '1px solid var(--line)', background: 'white', boxShadow: 'var(--shadow-sm)' }}
          onClick={() => navigate('/settings')}
        >
          <div
            className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold text-white"
            style={{ background: 'linear-gradient(135deg, var(--terra-400), var(--terra-500))' }}
          >
            {displayName.charAt(0).toUpperCase()}
          </div>
          <span className="text-[12.5px] font-medium max-w-[120px] truncate" style={{ color: 'var(--ink-strong)' }}>
            {displayName}
          </span>
          <ChevronDown size={12} style={{ color: 'var(--ink-muted)' }} />
        </button>
      </div>
    </header>
  )
}

// ─── Mobile bottom nav ───────────────────────────────────────────────────────
const BottomNav: React.FC = () => {
  const { user } = useAuthContext()
  const { workerType } = useWorkerContext()
  const location = useLocation()
  const { primary } = getNavItems(workerType, user?.role ?? '')
  const items = primary.slice(0, 5)

  return (
    <nav
      className="md:hidden fixed bottom-0 left-0 right-0 z-40 flex"
      style={{
        background: 'rgba(247,241,232,0.95)',
        backdropFilter: 'blur(16px)',
        borderTop: '1px solid var(--line)',
        paddingBottom: 'env(safe-area-inset-bottom)',
      }}
    >
      {items.map(item => {
        const active = item.exact
          ? location.pathname === item.to
          : location.pathname.startsWith(item.to)
        return (
          <NavLink
            key={item.to}
            to={item.to}
            className="flex-1 flex flex-col items-center justify-center gap-0.5 py-2.5 text-[10px] font-medium transition-colors"
            style={{ color: active ? 'var(--terra-500)' : 'var(--ink-muted)' }}
          >
            <item.Icon size={20} strokeWidth={active ? 2.2 : 1.6} />
            <span className="leading-none">{item.label.split(' ')[0]}</span>
          </NavLink>
        )
      })}
    </nav>
  )
}

// ─── AppShell — componente raíz del layout autenticado ───────────────────────
export const AppShell: React.FC = () => {
  const { isLoading: authLoading } = useAuthContext()
  const { isLoading: workerLoading } = useWorkerContext()
  const [sideOpen, setSideOpen] = useState(false)

  if (authLoading || workerLoading) return <LoadingSpinner fullScreen />

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: 'var(--bg-base)' }}>
      {/* ── Desktop sidenav ── */}
      <div className="hidden md:flex flex-col flex-shrink-0" style={{ width: 240 }}>
        <SideNav />
      </div>

      {/* ── Mobile sidenav overlay ── */}
      {sideOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          <div
            className="absolute inset-0"
            style={{ background: 'rgba(26,15,10,0.45)', backdropFilter: 'blur(4px)' }}
            onClick={() => setSideOpen(false)}
          />
          <div className="relative z-10 flex flex-col" style={{ width: 240 }}>
            <SideNav onClose={() => setSideOpen(false)} />
          </div>
        </div>
      )}

      {/* ── Main column ── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <TopBar onMenuToggle={() => setSideOpen(v => !v)} />
        <main
          className="flex-1 overflow-y-auto pb-20 md:pb-8"
          style={{ background: 'var(--bg-base)' }}
        >
          <div className="max-w-[1280px] mx-auto px-4 md:px-8 py-6">
            <Outlet />
          </div>
        </main>
      </div>

      {/* ── Mobile bottom nav ── */}
      <BottomNav />
    </div>
  )
}
