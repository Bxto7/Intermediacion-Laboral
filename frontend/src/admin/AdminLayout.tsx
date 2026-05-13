import { Routes, Route, Navigate, Link, useLocation } from 'react-router-dom'
import { BarChart2, HardHat, Building, Briefcase, type LucideIcon } from 'lucide-react'
import { AdminDashboard } from './AdminDashboard'

const NAV_ITEMS = [
  { path: '/admin',          label: 'KPIs',          Icon: BarChart2,  exact: true },
  { path: '/admin/workers',  label: 'Trabajadores',  Icon: HardHat              },
  { path: '/admin/employers',label: 'Empleadores',   Icon: Building             },
  { path: '/admin/jobs',     label: 'Ofertas',       Icon: Briefcase            },
]

export const AdminLayout: React.FC = () => {
  const location = useLocation()

  return (
    <div className="max-w-6xl mx-auto space-y-0">
        {/* Submenu */}
        <div
          className="flex gap-1 rounded-xl p-1 mb-5 overflow-x-auto"
          style={{ background: 'var(--bg-elevated)', border: '1px solid var(--line)' }}
        >
          {NAV_ITEMS.map((item) => {
            const active = item.exact ? location.pathname === item.path : location.pathname.startsWith(item.path)
            return (
              <Link
                key={item.path}
                to={item.path}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium transition-all whitespace-nowrap"
                style={{
                  background: active ? 'var(--terra-500)' : 'transparent',
                  color: active ? '#fff' : 'var(--ink-warm)',
                }}
              >
                <item.Icon size={14} />
                {item.label}
              </Link>
            )
          })}
        </div>
        <Routes>
          <Route index element={<AdminDashboard />} />
          <Route path="workers"   element={<WorkersAdmin />} />
          <Route path="employers" element={<EmployersAdmin />} />
          <Route path="jobs"      element={<JobsAdmin />} />
          <Route path="*"         element={<Navigate to="/admin" replace />} />
        </Routes>
    </div>
  )
}

const PlaceholderAdmin: React.FC<{ Icon: LucideIcon; label: string }> = ({ Icon, label }) => (
  <div className="card-warm p-8 text-center">
    <div className="w-16 h-16 rounded-2xl mx-auto mb-4 flex items-center justify-center" style={{ background: 'rgba(61,40,24,0.05)' }}>
      <Icon size={28} strokeWidth={1.5} style={{ color: 'var(--ink-muted)' }} />
    </div>
    <p className="font-medium" style={{ color: 'var(--ink-warm)' }}>{label}</p>
    <p className="text-sm mt-1" style={{ color: 'var(--ink-muted)' }}>Disponible en Sprint 6</p>
  </div>
)

const WorkersAdmin:  React.FC = () => <PlaceholderAdmin Icon={HardHat}  label="Gestión de trabajadores" />
const EmployersAdmin: React.FC = () => <PlaceholderAdmin Icon={Building} label="Gestión de empleadores" />
const JobsAdmin:     React.FC = () => <PlaceholderAdmin Icon={Briefcase} label="Gestión de ofertas laborales" />
