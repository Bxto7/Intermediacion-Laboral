import { useEffect, useState } from 'react'
import { Building, Briefcase, Users } from 'lucide-react'
import apiClient from '../api/client'
import { LoadingSpinner } from '../shared/LoadingSpinner'

interface AdminEmployer {
  id: string
  email: string
  company_name: string
  district: string
  sector: string
  is_verified: boolean
  jobs: number
  candidates: number
}

export const EmployersAdmin: React.FC = () => {
  const [employers, setEmployers] = useState<AdminEmployer[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiClient.get('/admin/employers')
      .then(({ data }) => setEmployers(data?.employers ?? []))
      .catch(() => setEmployers([]))
      .finally(() => setLoading(false))
  }, [])

  const totalJobs = employers.reduce((a, e) => a + e.jobs, 0)
  const totalCandidates = employers.reduce((a, e) => a + e.candidates, 0)
  const verified = employers.filter(e => e.is_verified).length

  return (
    <div className="space-y-5">
      <div>
        <h2 className="font-bold text-lg" style={{ color: 'var(--ink-strong)', letterSpacing: '-0.02em' }}>Empleadores registrados</h2>
        <p className="text-sm mt-0.5" style={{ color: 'var(--ink-muted)' }}>Empresas y personas con ofertas activas en la plataforma</p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { label: 'Total empleadores',  val: employers.length, Icon: Building,  color: 'var(--blue)',       bg: 'var(--blue-100)'   },
          { label: 'Ofertas publicadas', val: totalJobs,        Icon: Briefcase, color: 'var(--terra-500)', bg: 'var(--terra-100)'  },
          { label: 'Postulaciones',      val: totalCandidates,  Icon: Users,     color: 'var(--olive-deep)', bg: 'var(--olive-100)'  },
        ].map(({ label, val, Icon, color, bg }) => (
          <div key={label} className="card-warm p-5 flex items-center gap-4">
            <div className="p-3 rounded-xl flex-shrink-0" style={{ background: bg }}>
              <Icon size={20} style={{ color }} />
            </div>
            <div>
              <p className="text-xs font-semibold" style={{ color: 'var(--ink-muted)' }}>{label}</p>
              <p className="text-2xl font-bold" style={{ color: 'var(--ink-strong)' }}>{val}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Table */}
      <div className="card-warm overflow-hidden">
        <div className="px-5 py-4 flex items-center justify-between" style={{ borderBottom: '1px solid var(--line)' }}>
          <h3 className="font-semibold text-sm" style={{ color: 'var(--ink-strong)' }}>Listado de empleadores</h3>
          <span className="text-xs" style={{ color: 'var(--ink-muted)' }}>{verified} verificados</span>
        </div>

        {loading ? (
          <div className="p-8"><LoadingSpinner /></div>
        ) : employers.length === 0 ? (
          <div className="p-10 text-center">
            <Building size={26} className="mx-auto mb-2" strokeWidth={1.5} style={{ color: 'var(--ink-muted)' }} />
            <p className="text-sm font-semibold" style={{ color: 'var(--ink-warm)' }}>Aún no hay empleadores registrados</p>
            <p className="text-xs mt-1" style={{ color: 'var(--ink-muted)' }}>Las empresas que se registren aparecerán aquí.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr style={{ background: 'var(--bg-soft)' }}>
                  {['Empresa', 'Sector', 'Distrito', 'Ofertas', 'Candidatos', 'Estado'].map(h => (
                    <th key={h} className="px-4 py-2.5 text-left text-xs font-semibold" style={{ color: 'var(--ink-muted)' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {employers.map(emp => (
                  <tr key={emp.id} style={{ borderTop: '1px solid var(--line)' }}>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: 'rgba(15,110,110,0.1)' }}>
                          <Building size={14} style={{ color: 'var(--blue)' }} />
                        </div>
                        <span className="text-sm font-medium line-clamp-1" style={{ color: 'var(--ink-strong)' }}>{emp.company_name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm" style={{ color: 'var(--ink-muted)' }}>{emp.sector}</td>
                    <td className="px-4 py-3 text-sm" style={{ color: 'var(--ink-muted)' }}>{emp.district}</td>
                    <td className="px-4 py-3 text-sm font-semibold" style={{ color: 'var(--ink-strong)' }}>{emp.jobs}</td>
                    <td className="px-4 py-3 text-sm" style={{ color: 'var(--ink-muted)' }}>{emp.candidates}</td>
                    <td className="px-4 py-3">
                      <span
                        className="text-xs px-2 py-0.5 rounded-full"
                        style={{
                          background: emp.is_verified ? 'rgba(122,140,92,0.14)' : 'rgba(201,150,31,0.14)',
                          color: emp.is_verified ? 'var(--olive-deep)' : 'var(--gold)',
                        }}
                      >
                        {emp.is_verified ? 'Verificado' : 'Pendiente'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
