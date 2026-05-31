import { Link } from 'react-router-dom'
import { Star, Folder, Store, Briefcase, FileText, Plus, ChevronRight, Eye, TrendingUp } from 'lucide-react'
import { useWorkerContext } from '../../context/WorkerContext'
import { useMatches } from '../../hooks/useMatches'
import { usePortfolio } from '../../hooks/usePortfolio'
import { useApplications } from '../../hooks/useApplications'
import { JobMatchCard } from '../../matching/JobMatchCard'
import { LoadingSpinner } from '../../shared/LoadingSpinner'

// ── Checklist de progreso ────────────────────────────────────────────────────
const CHECKLIST = [
  { key: 'portfolio',    label: 'Agrega tu primer trabajo al portfolio' },
  { key: 'availability', label: 'Activa tu disponibilidad' },
  { key: 'marketplace',  label: 'Publica un servicio en el marketplace' },
  { key: 'cv',           label: 'Genera tu CV automático' },
  { key: 'contact',      label: 'Recibe tu primer contacto' },
]

export const OficioDashboard: React.FC = () => {
  const { worker } = useWorkerContext()
  const { matches, isLoading } = useMatches(4)
  const { entries } = usePortfolio()
  const { applications } = useApplications()
  const name = worker?.display_name?.split(' ')[0] || 'aquí'
  const pct  = worker?.profile_completeness ?? 0
  const rating = Number(worker?.avg_rating ?? 0)
  const photos = entries.flatMap((e) => e.photos).filter(Boolean).slice(0, 4)
  // Progreso real basado en señales de la cuenta
  const checklistState = [
    entries.length > 0,            // portfolio
    worker?.is_available ?? false, // disponibilidad
    false,                         // marketplace (sin señal aún)
    pct >= 80,                     // cv / perfil completo
    false,                         // primer contacto (sin señal aún)
  ]
  const done = checklistState.filter(Boolean).length

  return (
    <div className="space-y-5">

      {/* ── Welcome dark card ── */}
      <div
        className="card-dark relative overflow-hidden p-6 md:p-7"
      >
        <div className="absolute top-0 right-0 w-64 h-64 rounded-full blur-3xl opacity-20 pointer-events-none" style={{ background: 'var(--terra-500)' }} />
        <div className="absolute bottom-0 left-1/3 w-48 h-48 rounded-full blur-3xl opacity-15 pointer-events-none" style={{ background: 'var(--olive)' }} />

        <div className="relative z-10">
          <p className="kicker mb-2" style={{ color: 'rgba(253,246,234,0.45)' }}>
            {worker?.trade_category ?? 'Trabajador de oficio'}
          </p>
          <h1 className="text-2xl md:text-3xl font-bold leading-tight mb-5" style={{ letterSpacing: '-0.03em', color: 'var(--on-dark)' }}>
            Hola {name},{' '}
            <span className="serif-it" style={{ color: 'var(--coral)' }}>
              {matches.length > 0 ? `${matches.length} empleos te esperan` : 'bienvenido de vuelta'}
            </span>
          </h1>

          {/* Stats row */}
          <div className="flex flex-wrap items-center gap-4 md:gap-6">
            {[
              { icon: Star,       label: 'Rating',        value: rating > 0 ? `${rating.toFixed(1)} ★` : '—',   color: 'var(--gold-light)' },
              { icon: Folder,     label: 'Trabajos',      value: `${entries.length}`,  color: 'var(--coral)' },
              { icon: Eye,        label: 'Visibilidad',   value: `${pct}%`, color: 'var(--olive)' },
              { icon: FileText,   label: 'Postulaciones', value: `${applications.length}`,  color: 'var(--blue)' },
            ].map(s => (
              <div key={s.label} className="flex items-center gap-2">
                <s.icon size={14} style={{ color: s.color }} />
                <span className="text-sm font-semibold" style={{ color: 'var(--on-dark)' }}>{s.value}</span>
                <span className="text-xs" style={{ color: 'rgba(253,246,234,0.45)' }}>{s.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── 2-col grid ── */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-5">

        {/* ── Columna izquierda ── */}
        <div className="space-y-5">

          {/* Empleos compatibles */}
          <div className="card-warm p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="kicker">Empleos compatibles</p>
                <h2 className="text-[15px] font-semibold mt-0.5" style={{ color: 'var(--ink-strong)' }}>
                  Trabajos donde <span className="serif-it" style={{ color: 'var(--terra-500)' }}>encajas</span>
                </h2>
              </div>
              <Link to="/matches" className="text-[12px] font-medium flex items-center gap-1" style={{ color: 'var(--terra-500)' }}>
                Ver todos <ChevronRight size={12} />
              </Link>
            </div>

            {isLoading ? (
              <LoadingSpinner size="sm" />
            ) : matches.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {matches.map(m => <JobMatchCard key={m.job_id} match={m} workerType="oficio" compact />)}
              </div>
            ) : (
              <div className="text-center py-8">
                <Briefcase size={28} className="mx-auto mb-2" strokeWidth={1.4} style={{ color: 'var(--ink-muted)' }} />
                <p className="text-sm" style={{ color: 'var(--ink-muted)' }}>
                  Aún no tienes empleos compatibles.{' '}
                  <Link to="/oficio/portfolio" className="font-medium" style={{ color: 'var(--terra-500)' }}>
                    <span className="serif-it">Completa tu portfolio</span> →
                  </Link>
                </p>
              </div>
            )}
          </div>

          {/* Postulaciones recientes — timeline */}
          <div className="card-warm p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-[15px] font-semibold" style={{ color: 'var(--ink-strong)' }}>
                Postulaciones <span className="serif-it" style={{ color: 'var(--ink-muted)' }}>recientes</span>
              </h2>
              <Link to="/applications" className="text-[12px] font-medium flex items-center gap-1" style={{ color: 'var(--terra-500)' }}>
                Ver todas <ChevronRight size={12} />
              </Link>
            </div>
            <div className="text-center py-6">
              <FileText size={24} className="mx-auto mb-2" strokeWidth={1.4} style={{ color: 'var(--ink-muted)' }} />
              <p className="text-sm" style={{ color: 'var(--ink-muted)' }}>
                Aún no te has postulado.{' '}
                <span className="serif-it">Empieza acá</span>{' '}
                <Link to="/matches" style={{ color: 'var(--terra-500)' }}>→</Link>
              </p>
            </div>
          </div>
        </div>

        {/* ── Columna derecha ── */}
        <div className="space-y-4">

          {/* Portfolio status */}
          <div
            className="rounded-[18px] p-5 relative overflow-hidden"
            style={{
              background: 'linear-gradient(140deg, var(--bg-warm), var(--bg-soft))',
              border: '1px solid var(--line)',
              boxShadow: '0 0 0 1px rgba(194,86,46,0.06), var(--shadow-md)',
            }}
          >
            <div className="absolute top-0 right-0 w-32 h-32 rounded-full blur-2xl opacity-30 pointer-events-none" style={{ background: 'var(--terra-400)' }} />
            <div className="relative z-10">
              <div className="flex items-center justify-between mb-3">
                <p className="kicker">Mi portfolio</p>
                <Link
                  to="/oficio/portfolio"
                  className="text-[11px] font-medium px-2.5 py-1 rounded-full"
                  style={{ background: 'var(--terra-100)', color: 'var(--terra-500)' }}
                >
                  Abrir
                </Link>
              </div>
              {worker?.slug && (
                <p className="text-[11px] mb-3 truncate" style={{ color: 'var(--ink-muted)' }}>
                  linku.pe/p/{worker.slug}
                </p>
              )}
              {/* Thumbnails reales del portafolio */}
              <div className="grid grid-cols-4 gap-1.5 mb-4">
                {[...Array(4)].map((_, i) => {
                  const photo = photos[i]
                  return (
                    <Link
                      key={i}
                      to="/oficio/portfolio"
                      className="aspect-square rounded-[8px] overflow-hidden flex items-center justify-center"
                      style={{ background: photo ? 'transparent' : (i === photos.length ? 'var(--terra-100)' : 'rgba(61,40,24,0.06)') }}
                    >
                      {photo
                        ? <img src={photo} alt="" className="w-full h-full object-cover" />
                        : i === photos.length ? <Plus size={12} style={{ color: 'var(--terra-500)' }} /> : null}
                    </Link>
                  )
                })}
              </div>
              <Link to="/oficio/portfolio" className="btn-primary w-full text-xs py-2 block text-center">
                + Agregar trabajo
              </Link>
            </div>
          </div>

          {/* Accesos rápidos */}
          <div className="card-warm p-4 space-y-2">
            <p className="kicker mb-3">Accesos rápidos</p>
            {[
              { to: '/marketplace', Icon: Store,    label: 'Marketplace de servicios', color: 'var(--gold)' },
              { to: '/oficio/portfolio', Icon: Folder, label: 'Mi portfolio completo',  color: 'var(--terra-500)' },
              { to: '/survey/economic',  Icon: TrendingUp, label: 'Ver mi progreso',      color: 'var(--olive-deep)' },
            ].map(item => (
              <Link
                key={item.to}
                to={item.to}
                className="flex items-center gap-3 p-2.5 rounded-xl transition-colors"
                style={{ background: 'var(--bg-soft)' }}
                onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'var(--bg-warm)' }}
                onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'var(--bg-soft)' }}
              >
                <div className="w-7 h-7 rounded-[8px] flex items-center justify-center flex-shrink-0" style={{ background: 'rgba(61,40,24,0.06)' }}>
                  <item.Icon size={13} style={{ color: item.color }} />
                </div>
                <span className="text-[12.5px] font-medium flex-1" style={{ color: 'var(--ink-warm)' }}>{item.label}</span>
                <ChevronRight size={12} style={{ color: 'var(--ink-muted)' }} />
              </Link>
            ))}
          </div>

          {/* Progreso checklist */}
          <div className="card-warm p-4">
            <div className="flex items-center justify-between mb-3">
              <p className="kicker">Progreso</p>
              <span className="text-[11px] font-semibold" style={{ color: 'var(--olive-deep)' }}>{done}/{CHECKLIST.length} listos</span>
            </div>
            <div className="space-y-2">
              {CHECKLIST.map((item, i) => {
                const complete = i < done
                return (
                  <div key={item.key} className="flex items-start gap-2.5">
                    <div
                      className="w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
                      style={{
                        border: complete ? 'none' : '1.5px dashed var(--line-strong)',
                        background: complete ? 'var(--olive)' : 'transparent',
                      }}
                    >
                      {complete && (
                        <svg width="8" height="6" viewBox="0 0 8 6" fill="none">
                          <path d="M1 3L3 5L7 1" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                      )}
                    </div>
                    <p
                      className="text-[12px] leading-snug"
                      style={{
                        color: complete ? 'var(--ink-muted)' : 'var(--ink-warm)',
                        textDecoration: complete ? 'line-through' : 'none',
                      }}
                    >
                      {item.label}
                    </p>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
