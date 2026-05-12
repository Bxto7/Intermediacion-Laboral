import { Routes, Route, Navigate, Link, useLocation } from 'react-router-dom'
import { AdminDashboard } from './AdminDashboard'
import { NavBar } from '../shared/NavBar'

const NAV_ITEMS = [
  { path: '/admin', label: 'KPIs', icon: '📊', exact: true },
  { path: '/admin/workers', label: 'Trabajadores', icon: '👷' },
  { path: '/admin/employers', label: 'Empleadores', icon: '🏢' },
  { path: '/admin/jobs', label: 'Ofertas', icon: '💼' },
]

export const AdminLayout: React.FC = () => {
  const location = useLocation()

  return (
    <div className="min-h-screen bg-gray-50">
      <NavBar />
      <div className="max-w-6xl mx-auto px-4 py-4">
        {/* Submenu */}
        <div className="flex gap-1 bg-white rounded-xl border border-gray-200 p-1 mb-5 overflow-x-auto">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${
                (item.exact ? location.pathname === item.path : location.pathname.startsWith(item.path))
                  ? 'bg-primary-600 text-white shadow-sm'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <span>{item.icon}</span> {item.label}
            </Link>
          ))}
        </div>
        <Routes>
          <Route index element={<AdminDashboard />} />
          <Route path="workers" element={<WorkersAdmin />} />
          <Route path="employers" element={<EmployersAdmin />} />
          <Route path="jobs" element={<JobsAdmin />} />
          <Route path="*" element={<Navigate to="/admin" replace />} />
        </Routes>
      </div>
    </div>
  )
}

const WorkersAdmin: React.FC = () => (
  <div className="bg-white rounded-2xl border border-gray-100 p-8 text-center text-gray-400">
    <span className="text-4xl block mb-3">👷</span>
    <p className="font-medium text-gray-600">Gestión de trabajadores</p>
    <p className="text-sm mt-1">Disponible en Sprint 5</p>
  </div>
)
const EmployersAdmin: React.FC = () => (
  <div className="bg-white rounded-2xl border border-gray-100 p-8 text-center text-gray-400">
    <span className="text-4xl block mb-3">🏢</span>
    <p className="font-medium text-gray-600">Gestión de empleadores</p>
    <p className="text-sm mt-1">Disponible en Sprint 5</p>
  </div>
)
const JobsAdmin: React.FC = () => (
  <div className="bg-white rounded-2xl border border-gray-100 p-8 text-center text-gray-400">
    <span className="text-4xl block mb-3">💼</span>
    <p className="font-medium text-gray-600">Gestión de ofertas laborales</p>
    <p className="text-sm mt-1">Disponible en Sprint 5</p>
  </div>
)
