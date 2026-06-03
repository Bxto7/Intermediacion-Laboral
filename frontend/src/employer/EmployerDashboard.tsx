import { Briefcase, Users, TrendingUp, Info, Plus, MapPin, Clock } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useAuthContext } from '../context/AuthContext'
import { useEmployerJobs } from '../hooks/useEmployer'

const MODALITY_LABELS: Record<string, string> = {
  presencial: 'Presencial',
  remoto:     'Remoto',
  mixto:      'Mixto',
}

export const EmployerDashboard: React.FC = () => {
  const navigate = useNavigate()
  const { user } = useAuthContext()
  const { jobs } = useEmployerJobs()
  const initial = user?.email?.charAt(0).toUpperCase() ?? 'E'
  const activeJobs = jobs.filter(j => j.is_active)
  const totalCandidates = jobs.reduce((a, j) => a + (j.applications_count ?? 0), 0)
  const effectivity = jobs.length > 0
    ? Math.round((jobs.filter(j => (j.applications_count ?? 0) > 0).length / jobs.length) * 100)
    : null

  return (
    <div className="space-y-6">

      {/* Banner bienvenida */}
      <div
        className="relative overflow-hidden rounded-3xl flex flex-col sm:flex-row items-center justify-between p-6 sm:p-8"
        style={{ background: 'linear-gradient(135deg, var(--dark-deep) 0%, var(--dark) 60%, var(--dark-2) 100%)' }}
      >
        <div className="absolute top-0 right-0 w-72 h-72 rounded-full blur-3xl opacity-15 pointer-events-none" style={{ background: 'var(--terra-500)' }} />
        <div className="absolute bottom-0 left-1/3 w-48 h-48 rounded-full blur-3xl opacity-10 pointer-events-none" style={{ background: 'var(--olive)' }} />

        <div className="relative z-10 flex items-center gap-5">
          <div
            className="w-14 h-14 rounded-full flex items-center justify-center flex-shrink-0 text-white text-xl font-bold"
            style={{ background: 'rgba(244,236,224,0.15)', border: '1px solid rgba(244,236,224,0.2)' }}
          >
            {initial}
          </div>
          <div>
            <p className="text-sm" style={{ color: 'var(--on-dark-muted)' }}>Bienvenido de nuevo</p>
            <h1 className="text-xl font-bold tracking-tight" style={{ color: 'var(--on-dark)', letterSpacing: '-0.025em' }}>
              {user?.email}
            </h1>
          </div>
        </div>

        <button
          onClick={() => navigate('/employer/publish')}
          className="relative z-10 mt-5 sm:mt-0 flex items-center gap-2 font-medium text-sm px-5 py-2.5 rounded-full transition-colors"
          style={{ background: 'var(--on-dark)', color: 'var(--dark-deep)' }}
          onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'rgba(244,236,224,0.88)' }}
          onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'var(--on-dark)' }}
        >
          <Plus size={16} />
          Publicar empleo
        </button>
      </div>

      {/* Métricas */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { label: 'Ofertas activas',   val: activeJobs.length,                  Icon: Briefcase,  iconBg: 'var(--terra-100)', iconColor: 'var(--terra-500)' },
          { label: 'Candidatos totales', val: totalCandidates,                   Icon: Users,      iconBg: 'var(--blue-100)',  iconColor: 'var(--blue)'      },
          { label: 'Efectividad',        val: effectivity !== null ? `${effectivity}%` : '—', Icon: TrendingUp, iconBg: 'var(--olive-100)', iconColor: 'var(--olive-deep)' },
        ].map(({ label, val, Icon, iconBg, iconColor }) => (
          <div key={label} className="card-warm p-5 flex items-center gap-4">
            <div className="p-3 rounded-xl flex-shrink-0" style={{ background: iconBg }}>
              <Icon size={22} style={{ color: iconColor }} />
            </div>
            <div>
              <p className="text-sm font-medium" style={{ color: 'var(--ink-muted)' }}>{label}</p>
              <p className="text-2xl font-bold" style={{ color: 'var(--ink-strong)' }}>{val}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Ofertas publicadas */}
      <div className="card-warm p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-5">
          <div>
            <h2 className="font-bold text-base tracking-tight" style={{ color: 'var(--ink-strong)' }}>
              Ofertas <span className="serif-accent" style={{ color: 'var(--terra-500)' }}>publicadas</span>
            </h2>
            <p className="text-sm mt-0.5" style={{ color: 'var(--ink-muted)' }}>
              Gestiona tus vacantes y revisa candidatos postulados.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="tag">{activeJobs.length} activas</span>
            {jobs.length > 0 && (
              <button
                onClick={() => navigate('/employer/candidates')}
                className="btn-secondary text-xs px-3 py-1.5"
              >
                Ver candidatos
              </button>
            )}
          </div>
        </div>

        {jobs.length === 0 ? (
          <div className="text-center py-14 space-y-4">
            <div
              className="w-16 h-16 mx-auto rounded-2xl flex items-center justify-center"
              style={{ background: 'rgba(42,29,20,0.05)', border: '1px solid var(--line)' }}
            >
              <Briefcase size={28} style={{ color: 'var(--ink-muted)' }} strokeWidth={1.5} />
            </div>
            <div>
              <p className="font-semibold text-sm" style={{ color: 'var(--ink-warm)' }}>
                Aún no tienes ofertas publicadas
              </p>
              <p className="text-xs mt-1" style={{ color: 'var(--ink-muted)' }}>
                Publica tu primera oferta para comenzar a recibir postulantes
              </p>
            </div>
            <button
              onClick={() => navigate('/employer/publish')}
              className="btn-primary text-sm px-6 py-2.5 inline-flex items-center gap-2"
            >
              <Plus size={15} />
              Publicar primera oferta
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {jobs.slice(0, 5).map(job => (
              <div
                key={job.id}
                className="flex items-start justify-between gap-3 p-4 rounded-2xl cursor-pointer transition-all"
                style={{ background: 'var(--bg-soft)', border: '1px solid var(--line)' }}
                onClick={() => navigate('/employer/candidates')}
                onMouseEnter={e => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--line-strong)' }}
                onMouseLeave={e => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--line)' }}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="font-semibold text-sm" style={{ color: 'var(--ink-strong)' }}>{job.title}</p>
                    <span
                      className="text-[10px] px-1.5 py-0.5 rounded-full"
                      style={{
                        background: job.is_active ? 'rgba(122,140,92,0.14)' : 'rgba(42,29,20,0.07)',
                        color: job.is_active ? 'var(--olive-deep)' : 'var(--ink-muted)',
                      }}
                    >
                      {job.is_active ? 'Activa' : 'Inactiva'}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 mt-1 flex-wrap">
                    {job.district && (
                      <span className="text-xs flex items-center gap-1" style={{ color: 'var(--ink-muted)' }}>
                        <MapPin size={10} /> {job.district}
                      </span>
                    )}
                    {job.modality && (
                      <span className="text-xs" style={{ color: 'var(--ink-muted)' }}>
                        {MODALITY_LABELS[job.modality] ?? job.modality}
                      </span>
                    )}
                    {job.days_until_expiry !== null && job.days_until_expiry !== undefined && (
                      <span className="text-xs flex items-center gap-1" style={{ color: job.days_until_expiry <= 7 ? 'var(--terra-500)' : 'var(--ink-muted)' }}>
                        <Clock size={10} /> {job.days_until_expiry}d restantes
                      </span>
                    )}
                  </div>
                </div>
                <div className="text-right flex-shrink-0">
                  <p className="text-lg font-bold" style={{ color: 'var(--ink-strong)' }}>{job.applications_count ?? 0}</p>
                  <p className="text-xs" style={{ color: 'var(--ink-muted)' }}>candidatos</p>
                </div>
              </div>
            ))}
            {jobs.length > 5 && (
              <button
                onClick={() => navigate('/employer/candidates')}
                className="w-full text-center text-sm py-2.5 rounded-xl transition-all"
                style={{ color: 'var(--terra-500)', border: '1.5px dashed rgba(184,68,42,0.3)' }}
              >
                Ver todas las ofertas ({jobs.length})
              </button>
            )}
          </div>
        )}
      </div>

      {/* Tip DRTPE */}
      <div
        className="rounded-2xl p-5 flex items-start gap-4"
        style={{ background: 'var(--blue-100)', border: '1px solid rgba(15,110,110,0.18)' }}
      >
        <div
          className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
          style={{ background: 'var(--blue)' }}
        >
          <Info size={16} style={{ color: '#fff' }} />
        </div>
        <div>
          <p className="font-semibold text-sm" style={{ color: 'var(--blue)' }}>Plataforma oficial DRTPE-Junín</p>
          <p className="text-xs mt-0.5 leading-relaxed" style={{ color: 'var(--blue)' }}>
            Al publicar aquí, tus ofertas quedan registradas en la Bolsa de Trabajo oficial de la Dirección Regional de Trabajo y Promoción del Empleo de Junín.
          </p>
        </div>
      </div>

    </div>
  )
}
