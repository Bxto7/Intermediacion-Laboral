import { lazy, Suspense, Component, ReactNode } from 'react'
import { useIntl } from 'react-intl'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import { useAdminKPIs } from '../hooks/useAdminKPIs'
import { LoadingSpinner } from '../shared/LoadingSpinner'

const KPIGlobe = lazy(() => import('./KPIGlobe').then(m => ({ default: m.KPIGlobe })))

const TYPE_LABELS: Record<string, string> = {
  primer_empleo: 'Primer empleo',
  experiencia: 'Experiencia',
  oficio: 'Oficio',
}

const TYPE_COLORS: Record<string, string> = {
  primer_empleo: '#2d9a9a',
  experiencia: '#5d6b46',
  oficio: '#e0a32e',
}

class GlobeBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false }
  static getDerivedStateFromError() { return { failed: true } }
  render() {
    if (this.state.failed) return (
      <div style={{ height: 340, display: 'grid', placeItems: 'center', background: 'linear-gradient(160deg, #150d06 0%, #241910 100%)', borderRadius: 16 }}>
        <p style={{ color: 'rgba(255,255,255,0.55)', fontSize: 13 }}>Vista 3D no disponible en este entorno</p>
      </div>
    )
    return this.props.children
  }
}

interface KPICardProps { label: string; value: string | number; subtitle: string; color: string }
const KPICard: React.FC<KPICardProps> = ({ label, value, subtitle, color }) => (
  <div className="card-warm p-5" style={{ borderLeft: `4px solid ${color}` }}>
    <p className="text-xs font-semibold uppercase tracking-wide" style={{ color: 'var(--ink-muted)' }}>{label}</p>
    <p className="text-3xl font-bold mt-1" style={{ color: 'var(--ink-strong)' }}>{value}</p>
    <p className="text-xs mt-1" style={{ color: 'var(--ink-muted)' }}>{subtitle}</p>
  </div>
)

export const AdminDashboard: React.FC = () => {
  const intl = useIntl()
  const { kpis, isLoading } = useAdminKPIs()

  if (isLoading) return <LoadingSpinner fullScreen />

  const vilData = Object.entries(kpis?.vil || {}).map(([type, d]) => ({
    label: TYPE_LABELS[type] || type,
    dias: Math.round(d.avg_days),
    fill: TYPE_COLORS[type] || '#888',
  }))

  const tfData = Object.entries(kpis?.tf || {}).map(([type, pct]) => ({
    label: TYPE_LABELS[type] || type,
    porcentaje: Math.round(typeof pct === 'number' ? pct : 0),
  }))

  const tccData = Object.entries(kpis?.tcc || {}).map(([type, pct]) => ({
    label: TYPE_LABELS[type] || type,
    porcentaje: Math.round(typeof pct === 'number' ? pct : 0),
  }))

  const tcssData = Object.entries(kpis?.tcss || {}).map(([type, pct]) => ({
    label: TYPE_LABELS[type] || type,
    porcentaje: Math.round(typeof pct === 'number' ? pct : 0),
  }))

  const avgFormalization = tfData.length > 0
    ? Math.round(tfData.reduce((a, d) => a + d.porcentaje, 0) / tfData.length)
    : 0

  const ivm = kpis?.ivm
  const totalOficio = ivm?.total_oficio ?? 0
  const ivmPct = ivm?.ivm_pct ?? 0

  return (
    <div className="space-y-6">
      <div>
        <div className="mb-7">
          <h1 className="text-2xl font-bold" style={{ color: 'var(--ink-strong)', letterSpacing: '-0.02em' }}>
            {intl.formatMessage({ id: 'admin.dashboard.title' })}
          </h1>
          <p className="text-sm mt-1" style={{ color: 'var(--ink-muted)' }}>
            Indicadores de investigación en tiempo real · DRTPE-Junín 2026
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-7">
          <KPICard
            label={intl.formatMessage({ id: 'admin.kpi.workers_total' })}
            value={totalOficio}
            subtitle="Trabajadores OFICIO registrados"
            color="#e0a32e"
          />
          <KPICard
            label={intl.formatMessage({ id: 'admin.kpi.formalization' })}
            value={`${avgFormalization}%`}
            subtitle="Tasa promedio de formalización"
            color="#5d6b46"
          />
          <KPICard
            label={intl.formatMessage({ id: 'admin.kpi.ivm' })}
            value={`${ivmPct.toFixed(1)}%`}
            subtitle={`Índice Visibilidad Marketplace OFICIO`}
            color="#c9961f"
          />
        </div>

        <div className="card-warm p-4 space-y-3 mb-5">
          <h3 className="font-semibold text-sm" style={{ color: 'var(--ink-strong)' }}>
            Vista de red — KPIs del sistema
          </h3>
          <GlobeBoundary>
            <Suspense fallback={<div style={{ height: 340, display: 'grid', placeItems: 'center' }}><span style={{ color: 'var(--ink-muted)' }}>Cargando...</span></div>}>
              <KPIGlobe />
            </Suspense>
          </GlobeBoundary>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <div className="card-warm p-5">
            <h3 className="font-bold text-sm mb-1" style={{ color: 'var(--ink-strong)' }}>
              {intl.formatMessage({ id: 'admin.kpi.vil.title' })}
            </h3>
            <p className="text-xs mb-4" style={{ color: 'var(--ink-muted)' }}>Días desde registro hasta primer contrato</p>
            {vilData.length > 0 ? (
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={vilData} barSize={40}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(42,29,20,0.06)" />
                  <XAxis dataKey="label" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis unit=" d" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip formatter={(v: number) => [`${v} días`, 'Promedio VIL']} />
                  <Bar dataKey="dias" radius={[6, 6, 0, 0]} fill="#2d9a9a" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-40 flex items-center justify-center text-sm" style={{ color: 'var(--ink-muted)' }}>Sin contratos registrados aún</div>
            )}
          </div>

          <div className="card-warm p-5">
            <h3 className="font-bold text-sm mb-1" style={{ color: 'var(--ink-strong)' }}>
              {intl.formatMessage({ id: 'admin.kpi.tf.title' })}
            </h3>
            <p className="text-xs mb-4" style={{ color: 'var(--ink-muted)' }}>% trabajadores con al menos un contrato</p>
            {tfData.length > 0 ? (
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={tfData} barSize={40}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(42,29,20,0.06)" />
                  <XAxis dataKey="label" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis unit="%" domain={[0, 100]} tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip formatter={(v: number) => [`${v}%`, 'Tasa formalización']} />
                  <Bar dataKey="porcentaje" radius={[6, 6, 0, 0]} fill="#5d6b46" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-40 flex items-center justify-center text-sm" style={{ color: 'var(--ink-muted)' }}>Sin datos aún</div>
            )}
          </div>

          <div className="card-warm p-5">
            <h3 className="font-bold text-sm mb-1" style={{ color: 'var(--ink-strong)' }}>
              {intl.formatMessage({ id: 'admin.kpi.tcc.title' })}
            </h3>
            <p className="text-xs mb-4" style={{ color: 'var(--ink-muted)' }}>% perfiles con CV generado</p>
            {tccData.length > 0 ? (
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={tccData} barSize={40}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(42,29,20,0.06)" />
                  <XAxis dataKey="label" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis unit="%" domain={[0, 100]} tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip formatter={(v: number) => [`${v}%`, 'Tasa completitud CV']} />
                  <Bar dataKey="porcentaje" radius={[6, 6, 0, 0]} fill="#e0a32e" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-40 flex items-center justify-center text-sm" style={{ color: 'var(--ink-muted)' }}>Sin datos aún</div>
            )}
          </div>

          <div className="card-warm p-5">
            <h3 className="font-bold text-sm mb-1" style={{ color: 'var(--ink-strong)' }}>Tasa Cold-Start Superado</h3>
            <p className="text-xs mb-4" style={{ color: 'var(--ink-muted)' }}>% usuarios con al menos 1 match generado</p>
            {tcssData.length > 0 ? (
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={tcssData} barSize={40}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(42,29,20,0.06)" />
                  <XAxis dataKey="label" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis unit="%" domain={[0, 100]} tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip formatter={(v: number) => [`${v}%`, 'Cold-start superado']} />
                  <Bar dataKey="porcentaje" radius={[6, 6, 0, 0]} fill="#6c4fa3" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-40 flex items-center justify-center text-sm" style={{ color: 'var(--ink-muted)' }}>Sin matches registrados aún</div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
