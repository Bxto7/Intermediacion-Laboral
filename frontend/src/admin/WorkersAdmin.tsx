import { useEffect, useState } from 'react'
import { HardHat, TrendingUp } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import apiClient from '../api/client'
import { LoadingSpinner } from '../shared/LoadingSpinner'

interface StatRow { worker_type: string; district: string | null; total: number; avg_completeness: number; available: number }

const TYPE_LABELS: Record<string, string> = {
  primer_empleo: 'Primer empleo',
  experiencia:   'Experiencia',
  oficio:        'Oficio',
}

const TYPE_COLORS: Record<string, string> = {
  primer_empleo: '#4299e1',
  experiencia:   '#48bb78',
  oficio:        '#ed8936',
}

const MOCK_WORKERS = [
  { id: 1, name: 'Lucía Flores',   type: 'primer_empleo', district: 'Huancayo', completeness: 85,  status: 'Activa'   },
  { id: 2, name: 'Roberto Cano',   type: 'experiencia',   district: 'El Tambo', completeness: 100, status: 'Activa'   },
  { id: 3, name: 'Pedro Sulca',    type: 'oficio',        district: 'Chilca',   completeness: 72,  status: 'Activa'   },
  { id: 4, name: 'Elena Quispe',   type: 'primer_empleo', district: 'Huancayo', completeness: 40,  status: 'Activa'   },
  { id: 5, name: 'Hugo Paucar',    type: 'oficio',        district: 'El Tambo', completeness: 95,  status: 'Activa'   },
  { id: 6, name: 'Sofía Mendoza',  type: 'experiencia',   district: 'Huancayo', completeness: 100, status: 'Inactiva' },
  { id: 7, name: 'Luis Chipana',   type: 'oficio',        district: 'Chilca',   completeness: 60,  status: 'Activa'   },
  { id: 8, name: 'Carmen Palian',  type: 'primer_empleo', district: 'Huancayo', completeness: 55,  status: 'Activa'   },
]

export const WorkersAdmin: React.FC = () => {
  const [stats, setStats] = useState<StatRow[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiClient.get('/admin/workers/stats')
      .then(({ data }) => setStats(data?.rows ?? data ?? []))
      .catch(() => setStats([]))
      .finally(() => setLoading(false))
  }, [])

  const aggregated = stats.reduce<Record<string, { total: number; avg: number; count: number }>>((acc, row) => {
    const key = row.worker_type
    if (!acc[key]) acc[key] = { total: 0, avg: 0, count: 0 }
    acc[key].total += row.total
    acc[key].avg += row.avg_completeness * row.total
    acc[key].count += row.total
    return acc
  }, {})

  const chartData = Object.entries(aggregated).map(([type, d]) => ({
    label: TYPE_LABELS[type] ?? type,
    total: d.total,
    completitud: d.count > 0 ? Math.round(d.avg / d.count) : 0,
    fill: TYPE_COLORS[type] ?? '#888',
  }))

  const totalReal = chartData.reduce((a, d) => a + d.total, 0)
  const displayWorkers = totalReal > 0 ? MOCK_WORKERS.slice(0, 0) : MOCK_WORKERS

  return (
    <div className="space-y-5">
      <div>
        <h2 className="font-bold text-lg" style={{ color: 'var(--ink-strong)', letterSpacing: '-0.02em' }}>Trabajadores registrados</h2>
        <p className="text-sm mt-0.5" style={{ color: 'var(--ink-muted)' }}>Estadísticas por tipo de perfil · DRTPE-Junín</p>
      </div>

      {loading ? <LoadingSpinner /> : (
        <>
          {/* Stats grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {chartData.length > 0 ? chartData.map(d => (
              <div key={d.label} className="card-warm p-5">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ background: d.fill + '22' }}>
                    <HardHat size={18} style={{ color: d.fill }} />
                  </div>
                  <div>
                    <p className="text-xs font-semibold" style={{ color: 'var(--ink-muted)' }}>{d.label}</p>
                    <p className="text-2xl font-bold" style={{ color: 'var(--ink-strong)' }}>{d.total}</p>
                  </div>
                </div>
                <div className="flex items-center gap-1.5">
                  <TrendingUp size={12} style={{ color: 'var(--olive-deep)' }} />
                  <span className="text-xs" style={{ color: 'var(--ink-muted)' }}>Completitud promedio: <strong>{d.completitud}%</strong></span>
                </div>
              </div>
            )) : (
              [{ label: 'Primer empleo', color: '#4299e1' }, { label: 'Experiencia', color: '#48bb78' }, { label: 'Oficio', color: '#ed8936' }].map(d => (
                <div key={d.label} className="card-warm p-5">
                  <p className="text-xs font-semibold" style={{ color: 'var(--ink-muted)' }}>{d.label}</p>
                  <p className="text-2xl font-bold mt-1" style={{ color: 'var(--ink-strong)' }}>—</p>
                  <p className="text-xs mt-1" style={{ color: 'var(--ink-muted)' }}>Sin datos aún</p>
                </div>
              ))
            )}
          </div>

          {/* Chart */}
          {chartData.length > 0 && (
            <div className="card-warm p-5">
              <h3 className="font-semibold text-sm mb-4" style={{ color: 'var(--ink-strong)' }}>Distribución por tipo</h3>
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={chartData} barSize={48}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(61,40,24,0.06)" />
                  <XAxis dataKey="label" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip />
                  <Bar dataKey="total" radius={[6, 6, 0, 0]}>
                    {chartData.map((d, i) => (
                      <rect key={i} fill={d.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Table */}
          <div className="card-warm overflow-hidden">
            <div className="px-5 py-4 flex items-center justify-between" style={{ borderBottom: '1px solid var(--line)' }}>
              <h3 className="font-semibold text-sm" style={{ color: 'var(--ink-strong)' }}>
                Registro de trabajadores
                {displayWorkers.length > 0 && <span className="text-xs font-normal ml-2 px-2 py-0.5 rounded-full" style={{ background: 'var(--terra-100)', color: 'var(--terra-600)' }}>Datos de ejemplo</span>}
              </h3>
              <span className="text-xs" style={{ color: 'var(--ink-muted)' }}>{totalReal > 0 ? totalReal : MOCK_WORKERS.length} registros</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr style={{ background: 'var(--bg-soft)' }}>
                    {['Nombre', 'Tipo', 'Distrito', 'Completitud', 'Estado'].map(h => (
                      <th key={h} className="px-4 py-2.5 text-left text-xs font-semibold" style={{ color: 'var(--ink-muted)' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(totalReal > 0 ? [] : MOCK_WORKERS).map(w => (
                    <tr key={w.id} style={{ borderTop: '1px solid var(--line)' }}>
                      <td className="px-4 py-3 text-sm font-medium" style={{ color: 'var(--ink-strong)' }}>{w.name}</td>
                      <td className="px-4 py-3">
                        <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: TYPE_COLORS[w.type] + '22', color: TYPE_COLORS[w.type] }}>
                          {TYPE_LABELS[w.type]}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm" style={{ color: 'var(--ink-muted)' }}>{w.district}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--bg-warm)' }}>
                            <div className="h-full rounded-full" style={{ width: `${w.completeness}%`, background: w.completeness >= 80 ? 'var(--olive-deep)' : w.completeness >= 50 ? 'var(--gold)' : 'var(--terra-500)' }} />
                          </div>
                          <span className="text-xs" style={{ color: 'var(--ink-muted)' }}>{w.completeness}%</span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: w.status === 'Activa' ? 'rgba(122,140,92,0.14)' : 'rgba(61,40,24,0.07)', color: w.status === 'Activa' ? 'var(--olive-deep)' : 'var(--ink-muted)' }}>
                          {w.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {totalReal > 0 && (
                    <tr>
                      <td colSpan={5} className="px-4 py-8 text-center text-sm" style={{ color: 'var(--ink-muted)' }}>
                        Vista detallada de trabajadores disponible con datos de producción
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
