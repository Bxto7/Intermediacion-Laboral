import { FileText, ArrowRight } from 'lucide-react'
import { LoadingSpinner } from '../shared/LoadingSpinner'
import { useApplications } from '../hooks/useApplications'

const STATUS_CONFIG: Record<string, { label: string; bg: string; color: string }> = {
  PENDING:   { label: 'En revisión',  bg: 'rgba(184,137,58,0.14)', color: 'var(--gold)'        },
  ACCEPTED:  { label: 'Aceptado',     bg: 'rgba(122,140,92,0.14)', color: 'var(--olive-deep)'  },
  REJECTED:  { label: 'Descartado',   bg: 'rgba(194,86,46,0.10)', color: 'var(--terra-500)'    },
  WITHDRAWN: { label: 'Retirado',     bg: 'rgba(61,40,24,0.07)',  color: 'var(--ink-muted)'    },
}

export const ApplicationsPage: React.FC = () => {
  const { applications, isLoading, withdraw } = useApplications()

  const handleWithdraw = async (id: string) => {
    if (window.confirm('¿Retirar esta postulación?')) {
      await withdraw(id)
    }
  }

  return (
    <div className="space-y-4">
        <div>
          <h1 className="text-xl font-bold" style={{ color: 'var(--ink-strong)' }}>Mis postulaciones</h1>
          <p className="text-sm mt-0.5" style={{ color: 'var(--ink-muted)' }}>Historial de ofertas a las que te has postulado</p>
        </div>

        {isLoading ? (
          <LoadingSpinner />
        ) : applications.length === 0 ? (
          <div
            className="rounded-2xl p-12 text-center"
            style={{ border: '2px dashed rgba(61,40,24,0.14)', background: 'var(--bg-elevated)' }}
          >
            <div className="w-16 h-16 rounded-2xl mx-auto mb-4 flex items-center justify-center" style={{ background: 'rgba(61,40,24,0.05)' }}>
              <FileText size={28} style={{ color: 'var(--ink-muted)' }} strokeWidth={1.5} />
            </div>
            <h3 className="font-bold text-sm mb-1" style={{ color: 'var(--ink-warm)' }}>Aún no tienes postulaciones</h3>
            <p className="text-sm mb-5" style={{ color: 'var(--ink-muted)' }}>Explora las ofertas disponibles y postúlate</p>
            <a href="/matches" className="btn-primary inline-flex items-center gap-2 text-sm px-6 py-2.5">
              Ver ofertas compatibles
              <ArrowRight size={14} />
            </a>
          </div>
        ) : (
          <div className="space-y-3">
            {applications.map(app => {
              const cfg = STATUS_CONFIG[app.status] ?? { label: app.status, bg: 'rgba(61,40,24,0.07)', color: 'var(--ink-warm)' }
              return (
                <div key={app.id} className="card-warm p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-sm leading-tight line-clamp-2" style={{ color: 'var(--ink-strong)' }}>
                        {app.offer_title || 'Oferta de empleo'}
                      </h3>
                      {app.employer_name && (
                        <p className="text-xs mt-0.5" style={{ color: 'var(--ink-muted)' }}>{app.employer_name}</p>
                      )}
                    </div>
                    <span
                      className="shrink-0 text-xs font-medium px-2.5 py-1 rounded-full"
                      style={{ background: cfg.bg, color: cfg.color }}
                    >
                      {cfg.label}
                    </span>
                  </div>

                  <div className="mt-3 flex items-center justify-between text-xs" style={{ color: 'var(--ink-muted)' }}>
                    <div className="flex items-center gap-3">
                      <span>{new Date(app.created_at).toLocaleDateString('es-PE', { day: 'numeric', month: 'short', year: 'numeric' })}</span>
                      {app.proposed_rate && (
                        <span className="font-medium" style={{ color: 'var(--ink-warm)' }}>S/. {Number(app.proposed_rate).toFixed(0)} propuesto</span>
                      )}
                    </div>
                    {app.status === 'PENDING' && (
                      <button
                        onClick={() => handleWithdraw(app.id)}
                        className="font-medium transition-colors"
                        style={{ color: 'var(--terra-500)' }}
                        onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.color = 'var(--terra-700)' }}
                        onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.color = 'var(--terra-500)' }}
                      >
                        Retirar
                      </button>
                    )}
                  </div>

                  {app.cover_message && (
                    <p
                      className="mt-2 text-xs rounded-xl px-3 py-2 line-clamp-2 italic"
                      style={{ color: 'var(--ink-muted)', background: 'var(--bg-soft)' }}
                    >
                      "{app.cover_message}"
                    </p>
                  )}
                </div>
              )
            })}
          </div>
        )}
    </div>
  )
}
