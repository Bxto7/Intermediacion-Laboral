import { Building, Briefcase, Users } from 'lucide-react'

const MOCK_EMPLOYERS = [
  { id: 1, name: 'Constructora Andina SAC',       ruc: '20123456789', district: 'Huancayo', jobs: 4, candidates: 23, status: 'Verificado' },
  { id: 2, name: 'Servicios Eléctricos Junín',    ruc: '20987654321', district: 'El Tambo', jobs: 2, candidates: 11, status: 'Verificado' },
  { id: 3, name: 'Corporación Maderera del Centro', ruc: '20456789123', district: 'Chilca', jobs: 1, candidates: 5,  status: 'Pendiente' },
  { id: 4, name: 'Instalaciones Hidráulicas HYO',  ruc: '20321654987', district: 'Huancayo', jobs: 3, candidates: 18, status: 'Verificado' },
  { id: 5, name: 'Pinturas y Acabados JR',          ruc: '20654321987', district: 'El Tambo', jobs: 1, candidates: 7,  status: 'Pendiente' },
  { id: 6, name: 'Carpintería Los Andes',           ruc: '20789123456', district: 'Huancayo', jobs: 2, candidates: 9,  status: 'Verificado' },
]

export const EmployersAdmin: React.FC = () => {
  const totalJobs   = MOCK_EMPLOYERS.reduce((a, e) => a + e.jobs, 0)
  const totalCandidates = MOCK_EMPLOYERS.reduce((a, e) => a + e.candidates, 0)
  const verified    = MOCK_EMPLOYERS.filter(e => e.status === 'Verificado').length

  return (
    <div className="space-y-5">
      <div>
        <h2 className="font-bold text-lg" style={{ color: 'var(--ink-strong)', letterSpacing: '-0.02em' }}>Empleadores registrados</h2>
        <p className="text-sm mt-0.5" style={{ color: 'var(--ink-muted)' }}>Empresas y personas con ofertas activas en la plataforma</p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { label: 'Total empleadores',  val: MOCK_EMPLOYERS.length, Icon: Building,  color: 'var(--blue)',       bg: 'var(--blue-100)'   },
          { label: 'Ofertas publicadas', val: totalJobs,             Icon: Briefcase, color: 'var(--terra-500)', bg: 'var(--terra-100)'  },
          { label: 'Postulaciones',      val: totalCandidates,       Icon: Users,     color: 'var(--olive-deep)', bg: 'var(--olive-100)'  },
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
          <h3 className="font-semibold text-sm" style={{ color: 'var(--ink-strong)' }}>
            Listado de empleadores
            <span className="text-xs font-normal ml-2 px-2 py-0.5 rounded-full" style={{ background: 'var(--terra-100)', color: 'var(--terra-600)' }}>
              Datos de ejemplo
            </span>
          </h3>
          <span className="text-xs" style={{ color: 'var(--ink-muted)' }}>{verified} verificados</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr style={{ background: 'var(--bg-soft)' }}>
                {['Empresa', 'RUC', 'Distrito', 'Ofertas', 'Candidatos', 'Estado'].map(h => (
                  <th key={h} className="px-4 py-2.5 text-left text-xs font-semibold" style={{ color: 'var(--ink-muted)' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {MOCK_EMPLOYERS.map(emp => (
                <tr key={emp.id} style={{ borderTop: '1px solid var(--line)' }}>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2.5">
                      <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: 'rgba(45,90,130,0.1)' }}>
                        <Building size={14} style={{ color: 'var(--blue)' }} />
                      </div>
                      <span className="text-sm font-medium line-clamp-1" style={{ color: 'var(--ink-strong)' }}>{emp.name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-xs font-mono" style={{ color: 'var(--ink-muted)' }}>{emp.ruc}</td>
                  <td className="px-4 py-3 text-sm" style={{ color: 'var(--ink-muted)' }}>{emp.district}</td>
                  <td className="px-4 py-3 text-sm font-semibold" style={{ color: 'var(--ink-strong)' }}>{emp.jobs}</td>
                  <td className="px-4 py-3 text-sm" style={{ color: 'var(--ink-muted)' }}>{emp.candidates}</td>
                  <td className="px-4 py-3">
                    <span
                      className="text-xs px-2 py-0.5 rounded-full"
                      style={{
                        background: emp.status === 'Verificado' ? 'rgba(122,140,92,0.14)' : 'rgba(184,137,58,0.14)',
                        color: emp.status === 'Verificado' ? 'var(--olive-deep)' : 'var(--gold)',
                      }}
                    >
                      {emp.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
