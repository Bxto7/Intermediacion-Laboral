import { Link } from 'react-router-dom'
import { Star, ChevronRight, Search, Bell, Briefcase, TrendingUp, Eye, FileText } from 'lucide-react'
import { useIntl } from 'react-intl'
import { useMatches } from '../../hooks/useMatches'
import { useApplications } from '../../hooks/useApplications'
import { JobMatchCard } from '../../matching/JobMatchCard'
import { LoadingSpinner } from '../../shared/LoadingSpinner'
import { useWorkerContext } from '../../context/WorkerContext'

export const ExperienciaDashboard: React.FC = () => {
  const intl = useIntl()
  const { matches, isLoading } = useMatches(10)
  const { applications } = useApplications()
  const { worker } = useWorkerContext()
  const completeness = worker?.profile_completeness ?? 0
  const rating = Number(worker?.avg_rating ?? 0)
  const visible = completeness >= 40
  const name = worker?.display_name?.split(' ')[0] ?? ''

  return (
    <div className="space-y-5">

      {/* ── Welcome dark card ── */}
      <div className="card-dark relative overflow-hidden p-6 md:p-7">
        <div className="absolute top-0 right-0 w-56 h-56 rounded-full blur-3xl opacity-20 pointer-events-none" style={{ background: 'var(--terra-500)' }} />
        <div className="absolute bottom-0 left-1/4 w-48 h-48 rounded-full blur-3xl opacity-15 pointer-events-none" style={{ background: 'var(--blue)' }} />

        <div className="relative z-10">
          <div className="flex items-start gap-4">
            <div
              className="w-12 h-12 rounded-xl flex items-center justify-center text-lg font-bold text-white flex-shrink-0"
              style={{ background: 'rgba(244,236,224,0.12)', border: '1px solid rgba(244,236,224,0.15)' }}
            >
              {worker?.display_name?.[0]?.toUpperCase() ?? 'U'}
            </div>
            <div>
              <p className="kicker mb-1" style={{ color: 'rgba(244,236,224,0.7)' }}>Profesional con experiencia</p>
              <h1 className="text-xl md:text-2xl font-bold leading-tight" style={{ letterSpacing: '-0.03em', color: 'var(--on-dark)' }}>
                {name ? `Hola ${name}, ` : ''}
                <span className="serif-it" style={{ color: 'var(--coral)' }}>
                  {matches.length > 0 ? `${matches.length} ofertas te esperan` : 'bienvenido'}
                </span>
              </h1>
              {worker?.district && (
                <p className="text-xs mt-1" style={{ color: 'rgba(244,236,224,0.7)' }}>{worker.district}</p>
              )}
            </div>
          </div>

          {/* Stats row */}
          <div className="flex flex-wrap items-center gap-4 md:gap-8 mt-5 pt-4" style={{ borderTop: '1px solid rgba(244,236,224,0.10)' }}>
            {[
              { Icon: Star,        label: 'Rating',         value: rating > 0 ? `${rating.toFixed(1)} ★` : '—',   color: 'var(--gold-light)' },
              { Icon: Eye,         label: 'Completitud',    value: `${completeness}%`, color: 'var(--coral)' },
              { Icon: TrendingUp,  label: 'Visibilidad',    value: visible ? 'Visible' : 'Oculta',  color: 'var(--olive)' },
              { Icon: FileText,    label: 'Postulaciones',  value: `${applications.length}`,  color: 'var(--blue)' },
            ].map(s => (
              <div key={s.label} className="flex items-center gap-1.5">
                <s.Icon size={13} style={{ color: s.color }} />
                <span className="text-sm font-semibold" style={{ color: 'var(--on-dark)' }}>{s.value}</span>
                <span className="text-xs" style={{ color: 'rgba(244,236,224,0.7)' }}>{s.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── 2-col layout ── */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-5">

        {/* ── Izquierda: bolsa de empleos ── */}
        <div className="card-warm p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="kicker">Bolsa formal</p>
              <h2 className="text-[15px] font-semibold mt-0.5" style={{ color: 'var(--ink-strong)' }}>
                Empleos donde <span className="serif-it" style={{ color: 'var(--terra-500)' }}>encajas</span>
              </h2>
            </div>
            <Link to="/matches" className="text-[12px] font-medium flex items-center gap-1" style={{ color: 'var(--terra-500)' }}>
              Ver todos <ChevronRight size={12} />
            </Link>
          </div>
          {isLoading ? (
            <LoadingSpinner />
          ) : matches.length > 0 ? (
            <div className="space-y-3">
              {matches.map(m => <JobMatchCard key={m.job_id} match={m} workerType="experiencia" />)}
            </div>
          ) : (
            <div className="text-center py-12 space-y-3">
              <div className="w-12 h-12 mx-auto rounded-xl flex items-center justify-center" style={{ background: 'rgba(42,29,20,0.05)' }}>
                <Search size={22} style={{ color: 'var(--ink-muted)' }} strokeWidth={1.5} />
              </div>
              <p className="text-sm font-semibold" style={{ color: 'var(--ink-warm)' }}>
                {intl.formatMessage({ id: 'match.no_results' })}
              </p>
              <p className="text-xs" style={{ color: 'var(--ink-muted)' }}>
                Completa tu perfil para mejorar tus recomendaciones
              </p>
            </div>
          )}
        </div>

        {/* ── Derecha: sidebar ── */}
        <div className="space-y-4">

          {/* Progreso del perfil */}
          <div className="card-warm p-4">
            <p className="kicker mb-3">Perfil</p>
            <div className="grid grid-cols-3 gap-2 mb-4">
              {[
                { label: 'Completitud',    value: `${completeness}%`, color: completeness >= 60 ? 'var(--olive-deep)' : 'var(--terra-500)' },
                { label: 'Visibilidad',    value: visible ? 'Sí' : 'No',  color: 'var(--ink-muted)' },
                { label: 'Postulaciones', value: `${applications.length}`,  color: 'var(--ink-strong)' },
              ].map(s => (
                <div key={s.label} className="text-center rounded-xl p-2.5" style={{ background: 'var(--bg-soft)', border: '1px solid var(--line)' }}>
                  <p className="text-base font-bold" style={{ color: s.color }}>{s.value}</p>
                  <p className="text-[10.5px] mt-0.5" style={{ color: 'var(--ink-muted)' }}>{s.label}</p>
                </div>
              ))}
            </div>
            <div className="space-y-1">
              <div className="flex justify-between text-[11px]" style={{ color: 'var(--ink-muted)' }}>
                <span>Completitud del perfil</span>
                <span className="font-semibold">{completeness}%</span>
              </div>
              <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--bg-warm)' }}>
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{ width: `${completeness}%`, background: 'linear-gradient(90deg, var(--terra-400), var(--terra-500))' }}
                />
              </div>
            </div>
          </div>

          {/* Alertas de empleo */}
          <div className="card-warm p-4">
            <div className="flex items-center gap-2.5 mb-3">
              <div className="w-8 h-8 rounded-[10px] flex items-center justify-center" style={{ background: 'var(--terra-100)' }}>
                <Bell size={14} style={{ color: 'var(--terra-500)' }} />
              </div>
              <div>
                <p className="kicker">Alertas</p>
                <p className="text-[13px] font-semibold leading-tight" style={{ color: 'var(--ink-strong)' }}>Empleo por keyword</p>
              </div>
            </div>
            <p className="text-[11.5px] mb-3" style={{ color: 'var(--ink-muted)' }}>
              Te avisamos cuando aparezca algo compatible con tu perfil.
            </p>
            <button
              className="w-full py-2 text-[12px] font-medium rounded-xl transition-all"
              style={{ border: '1.5px dashed rgba(184,68,42,0.25)', color: 'var(--ink-muted)' }}
              onMouseEnter={e => {
                (e.currentTarget as HTMLElement).style.borderColor = 'var(--terra-500)'
                ;(e.currentTarget as HTMLElement).style.color = 'var(--terra-500)'
                ;(e.currentTarget as HTMLElement).style.background = 'rgba(184,68,42,0.04)'
              }}
              onMouseLeave={e => {
                (e.currentTarget as HTMLElement).style.borderColor = 'rgba(184,68,42,0.25)'
                ;(e.currentTarget as HTMLElement).style.color = 'var(--ink-muted)'
                ;(e.currentTarget as HTMLElement).style.background = 'transparent'
              }}
            >
              + Crear nueva alerta
            </button>
          </div>

          {/* Accesos rápidos */}
          <div className="card-warm p-4">
            <p className="kicker mb-3">Accesos rápidos</p>
            {[
              { to: '/applications',    Icon: Briefcase,   label: 'Mis postulaciones',  color: 'var(--blue)' },
              { to: '/survey/economic', Icon: TrendingUp,  label: 'Mi progreso',         color: 'var(--olive-deep)' },
            ].map(item => (
              <Link
                key={item.to}
                to={item.to}
                className="flex items-center gap-3 p-2.5 rounded-xl mb-1.5 transition-colors"
                style={{ background: 'var(--bg-soft)' }}
                onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'var(--bg-warm)' }}
                onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'var(--bg-soft)' }}
              >
                <item.Icon size={13} style={{ color: item.color }} />
                <span className="text-[12.5px] font-medium flex-1" style={{ color: 'var(--ink-warm)' }}>{item.label}</span>
                <ChevronRight size={12} style={{ color: 'var(--ink-muted)' }} />
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
