import { useState } from 'react'
import { Users, Briefcase, ChevronRight, CheckCircle, XCircle, Clock, Star, ArrowRight, type LucideIcon } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useEmployerJobs, useJobApplications } from '../../hooks/useEmployer'
import { LoadingSpinner } from '../../shared/LoadingSpinner'

const STATUS_CFG: Record<string, { label: string; color: string; bg: string }> = {
  PENDING:    { label: 'Enviada',      color: 'var(--gold)',       bg: 'rgba(184,137,58,0.14)' },
  enviada:    { label: 'Enviada',      color: 'var(--gold)',       bg: 'rgba(184,137,58,0.14)' },
  en_revision:{ label: 'En revisión',  color: 'var(--blue)',       bg: 'var(--blue-100)' },
  entrevista: { label: 'Entrevista',   color: 'var(--olive-deep)', bg: 'var(--olive-100)' },
  contratada: { label: 'Contratado',   color: '#fff',              bg: 'var(--olive-deep)' },
  descartada: { label: 'Descartado',   color: 'var(--terra-500)',  bg: 'var(--terra-100)' },
  WITHDRAWN:  { label: 'Retirado',     color: 'var(--ink-muted)',  bg: 'rgba(61,40,24,0.07)' },
}

const NEXT_STATUS: Record<string, { label: string; value: string; icon: LucideIcon }[]> = {
  PENDING:    [{ label: 'Revisar',    value: 'en_revision', icon: Clock       }, { label: 'Descartar', value: 'descartada', icon: XCircle }],
  enviada:    [{ label: 'Revisar',    value: 'en_revision', icon: Clock       }, { label: 'Descartar', value: 'descartada', icon: XCircle }],
  en_revision:[{ label: 'Entrevista', value: 'entrevista',  icon: Star        }, { label: 'Descartar', value: 'descartada', icon: XCircle }],
  entrevista: [{ label: 'Contratar',  value: 'contratada',  icon: CheckCircle }, { label: 'Descartar', value: 'descartada', icon: XCircle }],
}

interface Candidate {
  id: string
  worker_id: string
  status: string
  match_score: number | null
  cover_note: string | null
  applied_at: string
  worker_name?: string
}

interface CandidateRowProps {
  candidate: Candidate
  onStatus: (id: string, next: string) => void
}

const CandidateRow: React.FC<CandidateRowProps> = ({ candidate, onStatus }) => {
  const cfg = STATUS_CFG[candidate.status] ?? { label: candidate.status, color: 'var(--ink-muted)', bg: 'rgba(61,40,24,0.07)' }
  const transitions = NEXT_STATUS[candidate.status] ?? []
  const name = candidate.worker_name || `Trabajador ${candidate.worker_id.slice(0, 8)}`
  const initials = name.slice(0, 2).toUpperCase()
  const pct = candidate.match_score ? Math.round(candidate.match_score * 100) : null

  return (
    <div className="card-warm p-4 flex flex-col gap-3">
      <div className="flex items-start gap-3">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center text-sm font-bold text-white flex-shrink-0"
          style={{ background: 'linear-gradient(135deg, var(--terra-400), var(--terra-500))' }}
        >
          {initials}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="font-semibold text-sm" style={{ color: 'var(--ink-strong)' }}>
              {name}
            </p>
            {pct !== null && (
              <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full" style={{ background: pct >= 70 ? 'var(--olive-100)' : 'rgba(184,137,58,0.14)', color: pct >= 70 ? 'var(--olive-deep)' : 'var(--gold)' }}>
                {pct}% compatibilidad
              </span>
            )}
          </div>
          <p className="text-xs mt-0.5" style={{ color: 'var(--ink-muted)' }}>
            {new Date(candidate.applied_at).toLocaleDateString('es-PE', { day: 'numeric', month: 'short', year: 'numeric' })}
          </p>
        </div>
        <span className="text-xs font-medium px-2.5 py-1 rounded-full flex-shrink-0" style={{ background: cfg.bg, color: cfg.color }}>
          {cfg.label}
        </span>
      </div>

      {candidate.cover_note && (
        <p className="text-xs italic px-3 py-2 rounded-xl" style={{ background: 'var(--bg-soft)', color: 'var(--ink-muted)' }}>
          "{candidate.cover_note}"
        </p>
      )}

      {transitions.length > 0 && (
        <div className="flex gap-2 pt-1">
          {transitions.map(t => {
            const isPositive = t.value !== 'descartada'
            return (
              <button
                key={t.value}
                onClick={() => onStatus(candidate.id, t.value)}
                className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-xl transition-all"
                style={{
                  background: isPositive ? 'var(--olive-100)' : 'var(--terra-100)',
                  color: isPositive ? 'var(--olive-deep)' : 'var(--terra-500)',
                  border: `1px solid ${isPositive ? 'rgba(122,140,92,0.25)' : 'rgba(194,86,46,0.2)'}`,
                }}
              >
                <t.icon size={12} />
                {t.label}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}

const JobCandidatesPanel: React.FC<{ jobId: string; jobTitle: string }> = ({ jobId, jobTitle }) => {
  const { applications, isLoading, updateStatus } = useJobApplications(jobId)

  const handleStatus = async (id: string, next: string) => {
    try { await updateStatus(id, next) } catch { /* show silently */ }
  }

  return (
    <div className="flex-1 min-w-0 space-y-4">
      <div>
        <h2 className="font-bold text-base" style={{ color: 'var(--ink-strong)', letterSpacing: '-0.02em' }}>
          Candidatos
        </h2>
        <p className="text-xs mt-0.5" style={{ color: 'var(--ink-muted)' }}>
          {jobTitle} · {applications.length} {applications.length === 1 ? 'postulante' : 'postulantes'}
        </p>
      </div>

      {isLoading ? (
        <LoadingSpinner />
      ) : applications.length === 0 ? (
        <div className="card-warm p-10 text-center space-y-3">
          <div className="w-14 h-14 mx-auto rounded-2xl flex items-center justify-center" style={{ background: 'rgba(61,40,24,0.05)', border: '1px solid var(--line)' }}>
            <Users size={24} style={{ color: 'var(--ink-muted)' }} strokeWidth={1.5} />
          </div>
          <p className="font-semibold text-sm" style={{ color: 'var(--ink-warm)' }}>Aún no hay candidatos</p>
          <p className="text-xs" style={{ color: 'var(--ink-muted)' }}>Cuando un trabajador postule a esta oferta, aparecerá aquí.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {applications.map(c => (
            <CandidateRow key={c.id} candidate={c as Candidate} onStatus={handleStatus} />
          ))}
        </div>
      )}
    </div>
  )
}

export const EmployerCandidatesPage: React.FC = () => {
  const navigate = useNavigate()
  const { jobs, isLoading } = useEmployerJobs()
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null)

  const selectedJob = jobs.find(j => j.id === selectedJobId)

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-bold" style={{ color: 'var(--ink-strong)', letterSpacing: '-0.02em' }}>
          Gestión de candidatos
        </h1>
        <p className="text-sm mt-0.5" style={{ color: 'var(--ink-muted)' }}>
          Selecciona una oferta para ver y gestionar sus postulantes
        </p>
      </div>

      {isLoading ? (
        <LoadingSpinner />
      ) : jobs.length === 0 ? (
        <div className="card-warm p-12 text-center space-y-4">
          <div className="w-16 h-16 mx-auto rounded-2xl flex items-center justify-center" style={{ background: 'rgba(61,40,24,0.05)', border: '1px solid var(--line)' }}>
            <Users size={28} style={{ color: 'var(--ink-muted)' }} strokeWidth={1.5} />
          </div>
          <div>
            <p className="font-semibold text-sm" style={{ color: 'var(--ink-warm)' }}>No tienes ofertas publicadas</p>
            <p className="text-xs mt-1" style={{ color: 'var(--ink-muted)' }}>Publica una oferta para recibir candidatos</p>
          </div>
          <button onClick={() => navigate('/employer/publish')} className="btn-primary text-sm px-6 py-2.5 inline-flex items-center gap-2">
            <Briefcase size={14} /> Publicar oferta
          </button>
        </div>
      ) : (
        <div className="flex gap-5 items-start">
          {/* Job list */}
          <div className="w-72 flex-shrink-0 space-y-2">
            <p className="kicker px-1">Tus ofertas</p>
            {jobs.map(job => (
              <button
                key={job.id}
                onClick={() => setSelectedJobId(job.id)}
                className="w-full text-left p-4 rounded-2xl transition-all"
                style={{
                  background: selectedJobId === job.id ? 'var(--terra-100)' : 'var(--bg-elevated)',
                  border: `1.5px solid ${selectedJobId === job.id ? 'var(--terra-500)' : 'var(--line)'}`,
                }}
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="font-semibold text-sm leading-tight line-clamp-2" style={{ color: selectedJobId === job.id ? 'var(--terra-700)' : 'var(--ink-strong)' }}>
                    {job.title}
                  </p>
                  <ChevronRight size={14} className="flex-shrink-0 mt-0.5" style={{ color: selectedJobId === job.id ? 'var(--terra-500)' : 'var(--ink-muted)' }} />
                </div>
                <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                  {job.district && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full" style={{ background: 'rgba(61,40,24,0.07)', color: 'var(--ink-muted)' }}>
                      {job.district}
                    </span>
                  )}
                  <span className="text-[10px] font-medium" style={{ color: 'var(--ink-muted)' }}>
                    {job.applications_count ?? 0} postulantes
                  </span>
                  {!job.is_active && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full" style={{ background: 'var(--terra-100)', color: 'var(--terra-500)' }}>
                      Inactiva
                    </span>
                  )}
                </div>
              </button>
            ))}
          </div>

          {/* Candidates panel */}
          {selectedJob ? (
            <JobCandidatesPanel jobId={selectedJob.id} jobTitle={selectedJob.title} />
          ) : (
            <div className="flex-1 card-warm p-12 text-center">
              <div className="w-16 h-16 mx-auto rounded-2xl flex items-center justify-center" style={{ background: 'rgba(61,40,24,0.05)', border: '1px solid var(--line)' }}>
                <ArrowRight size={28} style={{ color: 'var(--ink-muted)' }} strokeWidth={1.5} />
              </div>
              <p className="font-semibold text-sm mt-4" style={{ color: 'var(--ink-warm)' }}>
                Selecciona una oferta
              </p>
              <p className="text-xs mt-1" style={{ color: 'var(--ink-muted)' }}>
                Elige una oferta de la lista para ver sus candidatos
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
