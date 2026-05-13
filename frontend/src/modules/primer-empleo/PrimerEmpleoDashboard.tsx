import { Link } from 'react-router-dom'
import { FileText, Lightbulb, BookOpen, ChevronRight, Edit, Briefcase } from 'lucide-react'
import { useIntl } from 'react-intl'
import { useMatches } from '../../hooks/useMatches'
import { JobMatchCard } from '../../matching/JobMatchCard'
import { LoadingSpinner } from '../../shared/LoadingSpinner'
import { useWorkerContext } from '../../context/WorkerContext'

const TIPS = [
  { Icon: Lightbulb, title: '¿Cómo ir a una entrevista?',      desc: 'Viste de forma limpia y ordenada. Llega 10 minutos antes.' },
  { Icon: FileText,  title: '¿Cómo negociar mi primer sueldo?', desc: 'Investiga el sueldo promedio del sector antes de la entrevista.' },
  { Icon: BookOpen,  title: '¿Cómo presentar mi CV?',           desc: 'Sé breve y honesto. Destaca tus habilidades y disposición para aprender.' },
]

export const PrimerEmpleoDashboard: React.FC = () => {
  const intl = useIntl()
  const { matches, isLoading } = useMatches(6)
  const { worker } = useWorkerContext()
  const completeness = worker?.profile_completeness ?? 0
  const name = worker?.display_name?.split(' ')[0] ?? ''

  return (
    <div className="space-y-5">

      {/* ── Welcome dark card ── */}
      <div className="card-dark relative overflow-hidden p-6 md:p-7">
        <div className="absolute top-0 right-0 w-64 h-64 rounded-full blur-3xl opacity-20 pointer-events-none" style={{ background: 'var(--terra-500)' }} />
        <div className="absolute bottom-0 left-0 w-40 h-40 rounded-full blur-3xl opacity-10 pointer-events-none" style={{ background: 'var(--olive)' }} />
        <div className="relative z-10">
          <p className="kicker mb-2" style={{ color: 'rgba(253,246,234,0.45)' }}>Tu primer empleo</p>
          <h1 className="text-2xl md:text-3xl font-bold leading-tight mb-4" style={{ letterSpacing: '-0.03em', color: 'var(--on-dark)' }}>
            {name ? `Hola ${name}, ` : ''}
            <span className="serif-it" style={{ color: 'var(--coral)' }}>
              {completeness < 50 ? 'completa tu perfil' : completeness < 100 ? 'casi estás listo' : 'tu perfil está completo'}
            </span>
          </h1>
          {/* Completeness bar */}
          <div className="flex items-center gap-3">
            <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: 'rgba(253,246,234,0.16)' }}>
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{ width: `${completeness}%`, background: 'linear-gradient(90deg, var(--terra-400), var(--gold-light))' }}
              />
            </div>
            <span className="text-sm font-bold" style={{ color: 'var(--on-dark)' }}>{completeness}%</span>
          </div>
          <p className="text-xs mt-1.5" style={{ color: 'rgba(253,246,234,0.45)' }}>completitud del perfil</p>
        </div>
      </div>

      {/* ── 2-col grid ── */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-5">

        {/* ── Izquierda: empleos ── */}
        <div className="space-y-5">

          {/* Empleos recomendados */}
          <div className="card-warm p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="kicker">Para ti</p>
                <h2 className="text-[15px] font-semibold mt-0.5" style={{ color: 'var(--ink-strong)' }}>
                  Empleos donde <span className="serif-it" style={{ color: 'var(--terra-500)' }}>encajas</span>
                </h2>
              </div>
              <Link to="/matches" className="text-[12px] font-medium flex items-center gap-1" style={{ color: 'var(--terra-500)' }}>
                Ver todos <ChevronRight size={12} />
              </Link>
            </div>
            {isLoading ? (
              <LoadingSpinner size="sm" />
            ) : matches.length > 0 ? (
              <div className="space-y-3">
                {matches.map(m => <JobMatchCard key={m.job_id} match={m} workerType="primer_empleo" />)}
              </div>
            ) : (
              <div className="text-center py-8">
                <Briefcase size={28} className="mx-auto mb-2" strokeWidth={1.4} style={{ color: 'var(--ink-muted)' }} />
                <p className="text-sm mb-3" style={{ color: 'var(--ink-muted)' }}>
                  Aún no hay coincidencias. <span className="serif-it">Completa tu perfil</span> para aparecer en las búsquedas.
                </p>
                <Link to="/wizard/step/1" className="btn-primary text-xs px-4 py-2 inline-flex items-center gap-1.5">
                  <Edit size={13} /> Completar perfil
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* ── Derecha: CV + tips ── */}
        <div className="space-y-4">

          {/* Mi CV */}
          <div className="card-warm p-5">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-9 h-9 rounded-[10px] flex items-center justify-center flex-shrink-0" style={{ background: 'var(--terra-100)' }}>
                <FileText size={16} style={{ color: 'var(--terra-500)' }} />
              </div>
              <div>
                <p className="kicker">Mi CV</p>
                <p className="text-[13px] font-semibold" style={{ color: 'var(--ink-strong)' }}>
                  {completeness < 100 ? 'En construcción' : 'Listo para descargar'}
                </p>
              </div>
            </div>
            <div className="space-y-2">
              <Link to="/wizard/step/1" className="btn-primary block w-full text-center py-2.5 text-xs">
                {intl.formatMessage({ id: 'primer_empleo.dashboard.continue_wizard' })}
              </Link>
              {worker?.id && (
                <a
                  href={`/api/v1/cv/download/${worker.id}`}
                  target="_blank"
                  rel="noreferrer"
                  className="btn-secondary block w-full text-center py-2.5 text-xs"
                >
                  Descargar CV (PDF)
                </a>
              )}
            </div>
          </div>

          {/* Orientación laboral */}
          <div className="card-warm p-5">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-9 h-9 rounded-[10px] flex items-center justify-center flex-shrink-0" style={{ background: 'rgba(122,140,92,0.14)' }}>
                <BookOpen size={16} style={{ color: 'var(--olive-deep)' }} />
              </div>
              <div>
                <p className="kicker">Tips</p>
                <p className="text-[13px] font-semibold" style={{ color: 'var(--ink-strong)' }}>
                  Orientación <span className="serif-it">laboral</span>
                </p>
              </div>
            </div>
            <div className="space-y-2">
              {TIPS.map(t => (
                <div
                  key={t.title}
                  className="flex gap-2.5 p-3 rounded-xl transition-colors cursor-default"
                  style={{ background: 'var(--bg-soft)' }}
                  onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.background = 'var(--bg-warm)' }}
                  onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.background = 'var(--bg-soft)' }}
                >
                  <div className="w-6 h-6 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5" style={{ background: 'var(--terra-100)' }}>
                    <t.Icon size={11} style={{ color: 'var(--terra-500)' }} />
                  </div>
                  <div>
                    <p className="text-[12.5px] font-semibold leading-snug" style={{ color: 'var(--ink-strong)' }}>{t.title}</p>
                    <p className="text-[11.5px] mt-0.5 leading-relaxed" style={{ color: 'var(--ink-muted)' }}>{t.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
