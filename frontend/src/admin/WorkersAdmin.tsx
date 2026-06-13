import { useEffect, useState } from 'react'
import { HardHat, TrendingUp } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import apiClient from '../api/client'
import { LoadingSpinner } from '../shared/LoadingSpinner'

interface StatRow { worker_type: string; district: string | null; total: number; avg_completeness: number; available: number }
interface WorkerRow { id: string; email: string; name: string; worker_type: string; district: string; trade_category: string; profile_completeness: number; is_available: boolean; created_at: string | null }

const TYPE_LABELS: Record<string, string> = { primer_empleo: 'Primer empleo', experiencia: 'Experiencia', oficio: 'Oficio' }
const TYPE_COLORS: Record<string, string> = { primer_empleo: '#2d9a9a', experiencia: '#5d6b46', oficio: '#e0a32e' }

export const WorkersAdmin: React.FC = () => {
  const [stats, setStats] = useState<StatRow[]>([])
  const [workers, setWorkers] = useState<WorkerRow[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      apiClient.get('/admin/workers/stats').then(({ data }) => setStats(data?.stats ?? [])).catch(() => {}),
      apiClient.get('/admin/workers').then(({ data }) => { setWorkers(data?.workers ?? []); setTotal(data?.total ?? 0) }).catch(() => {}),
    ]).finally(() => setLoading(false))
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

  if (loading) return <LoadingSpinner />

  return (
    <div className="space-y-5">
      <div>
        <h2 className="font-bold text-lg" style={{ color: 'var(--ink-strong)', letterSpacing: '-0.02em' }}>Trabajadores registrados</h2>
        <p className="text-sm mt-0.5" style={{ color: 'var(--ink-muted)' }}>Estadísticas por tipo de perfil · DRTPE-Junín</p>
      </div>

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
              <span className="text-xs" style={{ color: 'var(--ink-muted)' }}>Completitud: <strong>{d.completitud}%</strong></span>
            </div>
          </div>
        )) : (
          <div className="col-span-3 card-warm p-8 text-center text-sm" style={{ color: 'var(--ink-muted)' }}>Sin datos de estadísticas</div>
        )}
      </div>

      {chartData.length > 0 && (
        <div className="card-warm p-5">
          <h3 className="font-semibold text-sm mb-4" style={{ color: 'var(--ink-strong)' }}>Distribución por tipo</h3>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={chartData} barSize={48}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(42,29,20,0.06)" />
              <XAxis dataKey="label" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip />
              <Bar dataKey="total" radius={[6, 6, 0, 0]} fill="#b8442a" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="card-warm overflow-hidden">
        <div className="px-5 py-4 flex items-center justify-between" style={{ borderBottom: '1px solid var(--line)' }}>
          <h3 className="font-semibold text-sm" style={{ color: 'var(--ink-strong)' }}>Registro de trabajadores</h3>
          <span className="text-xs" style={{ color: 'var(--ink-muted)' }}>{total} registros</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr style={{ background: 'var(--bg-soft)' }}>
                {['Nombre', 'Email', 'Tipo', 'Distrito', 'Completitud', 'Estado'].map(h => (
                  <th key={h} className="px-4 py-2.5 text-left text-xs font-semibold" style={{ color: 'var(--ink-muted)' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {workers.map(w => (
                <tr key={w.id} style={{ borderTop: '1px solid var(--line)' }}>
                  <td className="px-4 py-3 text-sm font-medium" style={{ color: 'var(--ink-strong)' }}>{w.name}</td>
                  <td className="px-4 py-3 text-xs" style={{ color: 'var(--ink-muted)' }}>{w.email}</td>
                  <td className="px-4 py-3">
                    <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: (TYPE_COLORS[w.worker_type] ?? '#888') + '22', color: TYPE_COLORS[w.worker_type] ?? '#888' }}>
                      {TYPE_LABELS[w.worker_type] ?? w.worker_type}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm" style={{ color: 'var(--ink-muted)' }}>{w.district}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--bg-warm)' }}>
                        <div className="h-full rounded-full" style={{ width: `${w.profile_completeness}%`, background: w.profile_completeness >= 80 ? 'var(--olive-deep)' : w.profile_completeness >= 50 ? 'var(--gold)' : 'var(--terra-500)' }} />
                      </div>
                      <span className="text-xs" style={{ color: 'var(--ink-muted)' }}>{w.profile_completeness}%</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: w.is_available ? 'rgba(122,140,92,0.14)' : 'rgba(42,29,20,0.07)', color: w.is_available ? 'var(--olive-deep)' : 'var(--ink-muted)' }}>
                      {w.is_available ? 'Disponible' : 'No disponible'}
                    </span>
                  </td>
                </tr>
              ))}
              {workers.length === 0 && (
                <tr><td colSpan={6} className="px-4 py-10 text-center text-sm" style={{ color: 'var(--ink-muted)' }}>Sin trabajadores registrados</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
