import { Routes, Route, Navigate, Link, useLocation } from 'react-router-dom'
import { BarChart2, HardHat, Building, Briefcase } from 'lucide-react'
import { AdminDashboard } from './AdminDashboard'
import { WorkersAdmin } from './WorkersAdmin'
import { EmployersAdmin } from './EmployersAdmin'
import { JobsAdmin } from './JobsAdmin'

const NAV_ITEMS = [
  { path: '/admin',           label: 'KPIs',         Icon: BarChart2, exact: true },
  { path: '/admin/workers',   label: 'Trabajadores', Icon: HardHat              },
  { path: '/admin/employers', label: 'Empleadores',  Icon: Building             },
  { path: '/admin/jobs',      label: 'Ofertas',      Icon: Briefcase            },
]

export const AdminLayout: React.FC = () => {
  const location = useLocation()

  return (
    <div className="max-w-6xl mx-auto space-y-0">
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
        <Route index           element={<AdminDashboard />} />
        <Route path="workers"  element={<WorkersAdmin />} />
        <Route path="employers" element={<EmployersAdmin />} />
        <Route path="jobs"     element={<JobsAdmin />} />
        <Route path="*"        element={<Navigate to="/admin" replace />} />
      </Routes>
    </div>
  )
}
