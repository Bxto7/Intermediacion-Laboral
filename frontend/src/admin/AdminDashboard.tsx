import { useIntl } from 'react-intl'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import { useAdminKPIs } from '../hooks/useAdminKPIs'
import { LoadingSpinner } from '../shared/LoadingSpinner'

const TYPE_LABELS: Record<string, string> = {
  primer_empleo: 'Primer empleo',
  experiencia: 'Experiencia',
  oficio: 'Oficio',
}

const TYPE_COLORS: Record<string, string> = {
  primer_empleo: '#4299e1',
  experiencia: '#48bb78',
  oficio: '#ed8936',
}

interface KPICardProps { label: string; value: string | number; subtitle: string; color: string }
const KPICard: React.FC<KPICardProps> = ({ label, value, subtitle, color }) => (
  <div className={`bg-bg-elevated rounded-2xl shadow-md border border-[rgba(61,40,24,0.08)] p-5 border-l-4 border-l-${color}-500`}>
    <p className="text-xs font-semibold text-ink-muted uppercase tracking-wide">{label}</p>
    <p className="text-3xl font-bold text-ink-strong mt-1">{value}</p>
    <p className="text-xs text-ink-muted mt-1">{subtitle}</p>
  </div>
)

export const AdminDashboard: React.FC = () => {
  const intl = useIntl()
  const { kpis, isLoading } = useAdminKPIs()

  if (isLoading) return <LoadingSpinner fullScreen />

  const vilData = Object.entries(kpis?.vil || {}).map(([type, d]: [string, { avg_days: number }]) => ({
    label: TYPE_LABELS[type] || type,
    dias: Math.round(d.avg_days),
    fill: TYPE_COLORS[type] || '#888',
  }))

  const tfData = Object.entries(kpis?.tf || {}).map(([type, d]: [string, { tasa_percent: number; total: number }]) => ({
    label: TYPE_LABELS[type] || type,
    porcentaje: Math.round(d.tasa_percent),
    total: d.total,
  }))

  const tccData = Object.entries(kpis?.tcc || {}).map(([type, d]: [string, { tcc_percent: number }]) => ({
    label: TYPE_LABELS[type] || type,
    porcentaje: Math.round(d.tcc_percent),
  }))

  const totalWorkers = Object.values(kpis?.tf || {}).reduce((a, d) => a + (d as { total: number }).total, 0)
  const avgFormalization = tfData.length > 0
    ? Math.round(tfData.reduce((a, d) => a + d.porcentaje, 0) / tfData.length)
    : 0

  return (
    <div className="space-y-6">
      <div>
        <div className="mb-7">
          <h1 className="text-2xl font-bold text-ink-strong">{intl.formatMessage({ id: 'admin.dashboard.title' })}</h1>
          <p className="text-ink-muted text-sm mt-1">Indicadores de investigación en tiempo real · DRTPE-Junín 2026</p>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-7">
          <KPICard
            label={intl.formatMessage({ id: 'admin.kpi.workers_total' })}
            value={totalWorkers}
            subtitle="Trabajadores registrados en total"
            color="blue"
          />
          <KPICard
            label={intl.formatMessage({ id: 'admin.kpi.formalization' })}
            value={`${avgFormalization}%`}
            subtitle="Tasa promedio de formalización"
            color="green"
          />
          <KPICard
            label={intl.formatMessage({ id: 'admin.kpi.ivm' })}
            value={`${kpis?.ivm?.ivm_percent?.toFixed(1) ?? '—'}%`}
            subtitle={`${kpis?.ivm?.active_listings ?? 0} listados activos en marketplace`}
            color="amber"
          />
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* VIL */}
          <div className="bg-bg-elevated rounded-2xl shadow-md border border-[rgba(61,40,24,0.08)] p-5">
            <h3 className="font-bold text-ink-strong mb-1">{intl.formatMessage({ id: 'admin.kpi.vil.title' })}</h3>
            <p className="text-xs text-ink-muted mb-4">Promedio de días desde registro hasta primer contrato</p>
            {vilData.length > 0 ? (
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={vilData} barSize={40}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                  <XAxis dataKey="label" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis unit=" d" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip formatter={(v: number) => [`${v} días`, 'Promedio VIL']} />
                  <Bar dataKey="dias" radius={[6, 6, 0, 0]} fill="#4299e1" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-40 flex items-center justify-center text-ink-muted text-sm">Sin datos aún</div>
            )}
          </div>

          {/* TF */}
          <div className="bg-bg-elevated rounded-2xl shadow-md border border-[rgba(61,40,24,0.08)] p-5">
            <h3 className="font-bold text-ink-strong mb-1">{intl.formatMessage({ id: 'admin.kpi.tf.title' })}</h3>
            <p className="text-xs text-ink-muted mb-4">% de trabajadores con al menos un contrato</p>
            {tfData.length > 0 ? (
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={tfData} barSize={40}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                  <XAxis dataKey="label" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis unit="%" domain={[0, 100]} tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip formatter={(v: number) => [`${v}%`, 'Tasa formalización']} />
                  <Bar dataKey="porcentaje" radius={[6, 6, 0, 0]} fill="#48bb78" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-40 flex items-center justify-center text-ink-muted text-sm">Sin datos aún</div>
            )}
          </div>

          {/* TCC */}
          <div className="bg-bg-elevated rounded-2xl shadow-md border border-[rgba(61,40,24,0.08)] p-5">
            <h3 className="font-bold text-ink-strong mb-1">{intl.formatMessage({ id: 'admin.kpi.tcc.title' })}</h3>
            <p className="text-xs text-ink-muted mb-4">% de perfiles con CV generado</p>
            {tccData.length > 0 ? (
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={tccData} barSize={40}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                  <XAxis dataKey="label" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis unit="%" domain={[0, 100]} tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip formatter={(v: number) => [`${v}%`, 'Tasa completitud']} />
                  <Bar dataKey="porcentaje" radius={[6, 6, 0, 0]} fill="#ed8936" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-40 flex items-center justify-center text-ink-muted text-sm">Sin datos aún</div>
            )}
          </div>

          {/* Cold-start */}
          <div className="bg-bg-elevated rounded-2xl shadow-md border border-[rgba(61,40,24,0.08)] p-5">
            <h3 className="font-bold text-ink-strong mb-1">Tasa Cold-Start Superado</h3>
            <p className="text-xs text-ink-muted mb-4">% de usuarios con al menos 1 match generado</p>
            {kpis?.cold_start && Object.keys(kpis.cold_start).length > 0 ? (
              <ResponsiveContainer width="100%" height={180}>
                <BarChart
                  data={Object.entries(kpis.cold_start).map(([t, d]: [string, { rate_percent: number }]) => ({
                    label: TYPE_LABELS[t] || t,
                    porcentaje: Math.round(d.rate_percent),
                  }))}
                  barSize={40}
                >
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                  <XAxis dataKey="label" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis unit="%" domain={[0, 100]} tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip formatter={(v: number) => [`${v}%`, 'Cold-start superado']} />
                  <Bar dataKey="porcentaje" radius={[6, 6, 0, 0]} fill="#9b59b6" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-40 flex items-center justify-center text-ink-muted text-sm">Sin datos aún</div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
