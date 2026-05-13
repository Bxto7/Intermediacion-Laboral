import { useEffect, useState } from 'react'
import { Briefcase, MapPin, Clock } from 'lucide-react'
import apiClient from '../api/client'
import { LoadingSpinner } from '../shared/LoadingSpinner'

interface JobFeedItem {
  id: string
  title: string
  description: string
  district: string | null
  modality: string | null
  worker_type_target: string | null
  salary_min: number | null
  salary_max: number | null
  is_active: boolean
  views_count: number
  applications_count: number
  created_at: string
  days_until_expiry: number | null
}

const WORKER_TYPE_LABELS: Record<string, string> = {
  primer_empleo: 'Primer empleo',
  experiencia:   'Experiencia',
  oficio:        'Oficio',
  all:           'Cualquier perfil',
}

const MODALITY_LABELS: Record<string, string> = {
  presencial: 'Presencial',
  remoto:     'Remoto',
  mixto:      'Mixto',
}

const MOCK_JOBS: JobFeedItem[] = [
  { id: 'm1', title: 'Electricista residencial', description: '', district: 'El Tambo',  modality: 'presencial', worker_type_target: 'oficio',        salary_min: 1000, salary_max: 1500, is_active: true,  views_count: 34,  applications_count: 8,  created_at: new Date(Date.now() - 86400000 * 3).toISOString(),  days_until_expiry: 27 },
  { id: 'm2', title: 'Asistente contable',       description: '', district: 'Huancayo',  modality: 'presencial', worker_type_target: 'experiencia',   salary_min: 1200, salary_max: 1800, is_active: true,  views_count: 56,  applications_count: 14, created_at: new Date(Date.now() - 86400000 * 5).toISOString(),  days_until_expiry: 25 },
  { id: 'm3', title: 'Operario de construcción', description: '', district: 'Chilca',    modality: 'presencial', worker_type_target: 'all',           salary_min: 900,  salary_max: null, is_active: true,  views_count: 22,  applications_count: 5,  created_at: new Date(Date.now() - 86400000 * 7).toISOString(),  days_until_expiry: 23 },
  { id: 'm4', title: 'Diseñador gráfico junior', description: '', district: 'Huancayo',  modality: 'remoto',     worker_type_target: 'primer_empleo', salary_min: 800,  salary_max: 1200, is_active: false, views_count: 91,  applications_count: 22, created_at: new Date(Date.now() - 86400000 * 15).toISOString(), days_until_expiry: null },
]

export const JobsAdmin: React.FC = () => {
  const [jobs, setJobs] = useState<JobFeedItem[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'active' | 'inactive'>('all')

  useEffect(() => {
    apiClient.get('/jobs/feed?limit=50')
      .then(({ data }) => setJobs(Array.isArray(data) ? data : data?.items ?? []))
      .catch(() => setJobs([]))
      .finally(() => setLoading(false))
  }, [])

  const source = jobs.length > 0 ? jobs : MOCK_JOBS
  const isMock = jobs.length === 0

  const filtered = source.filter(j =>
    filter === 'all' ? true : filter === 'active' ? j.is_active : !j.is_active
  )

  const totalViews    = source.reduce((a, j) => a + (j.views_count ?? 0), 0)
  const totalApps     = source.reduce((a, j) => a + (j.applications_count ?? 0), 0)
  const activeCount   = source.filter(j => j.is_active).length

  return (
    <div className="space-y-5">
      <div>
        <h2 className="font-bold text-lg" style={{ color: 'var(--ink-strong)', letterSpacing: '-0.02em' }}>Ofertas laborales</h2>
        <p className="text-sm mt-0.5" style={{ color: 'var(--ink-muted)' }}>
          Todas las vacantes publicadas en la plataforma
          {isMock && <span className="ml-2 text-xs px-2 py-0.5 rounded-full" style={{ background: 'var(--terra-100)', color: 'var(--terra-600)' }}>Datos de ejemplo</span>}
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Activas',         val: activeCount },
          { label: 'Visualizaciones', val: totalViews  },
          { label: 'Postulaciones',   val: totalApps   },
        ].map(({ label, val }) => (
          <div key={label} className="card-warm p-5">
            <p className="text-xs font-semibold" style={{ color: 'var(--ink-muted)' }}>{label}</p>
            <p className="text-3xl font-bold mt-1" style={{ color: 'var(--ink-strong)' }}>{val}</p>
          </div>
        ))}
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 p-1 rounded-xl w-fit" style={{ background: 'var(--bg-elevated)', border: '1px solid var(--line)' }}>
        {(['all', 'active', 'inactive'] as const).map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className="px-4 py-1.5 rounded-lg text-xs font-medium transition-all"
            style={{
              background: filter === f ? 'var(--terra-500)' : 'transparent',
              color: filter === f ? '#fff' : 'var(--ink-muted)',
            }}
          >
            {f === 'all' ? 'Todas' : f === 'active' ? 'Activas' : 'Inactivas'}
          </button>
        ))}
      </div>

      {/* Jobs list */}
      {loading ? (
        <LoadingSpinner />
      ) : (
        <div className="space-y-3">
          {filtered.map(job => (
            <div key={job.id} className="card-warm p-4">
              <div className="flex items-start gap-3 justify-between">
                <div className="flex items-start gap-3 flex-1 min-w-0">
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: job.is_active ? 'var(--terra-100)' : 'rgba(61,40,24,0.05)' }}>
                    <Briefcase size={18} style={{ color: job.is_active ? 'var(--terra-500)' : 'var(--ink-muted)' }} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="font-semibold text-sm" style={{ color: 'var(--ink-strong)' }}>{job.title}</p>
                      <span
                        className="text-[10px] px-1.5 py-0.5 rounded-full"
                        style={{
                          background: job.is_active ? 'rgba(122,140,92,0.14)' : 'rgba(61,40,24,0.07)',
                          color: job.is_active ? 'var(--olive-deep)' : 'var(--ink-muted)',
                        }}
                      >
                        {job.is_active ? 'Activa' : 'Inactiva'}
                      </span>
                      {job.worker_type_target && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded-full" style={{ background: 'rgba(184,137,58,0.14)', color: 'var(--gold)' }}>
                          {WORKER_TYPE_LABELS[job.worker_type_target] ?? job.worker_type_target}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 mt-1.5 flex-wrap">
                      {job.district && (
                        <span className="text-xs flex items-center gap-1" style={{ color: 'var(--ink-muted)' }}>
                          <MapPin size={10} /> {job.district}
                        </span>
                      )}
                      {job.modality && (
                        <span className="text-xs" style={{ color: 'var(--ink-muted)' }}>{MODALITY_LABELS[job.modality] ?? job.modality}</span>
                      )}
                      {job.salary_min && (
                        <span className="text-xs font-medium" style={{ color: 'var(--ink-warm)' }}>
                          S/. {job.salary_min}{job.salary_max ? ` – ${job.salary_max}` : '+'}
                        </span>
                      )}
                      {job.days_until_expiry !== null && job.days_until_expiry !== undefined && (
                        <span className="text-xs flex items-center gap-1" style={{ color: job.days_until_expiry <= 7 ? 'var(--terra-500)' : 'var(--ink-muted)' }}>
                          <Clock size={10} /> {job.days_until_expiry}d restantes
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="text-right flex-shrink-0 space-y-1">
                  <p className="text-xs" style={{ color: 'var(--ink-muted)' }}>{job.views_count ?? 0} vistas</p>
                  <p className="text-xs font-medium" style={{ color: 'var(--ink-warm)' }}>{job.applications_count ?? 0} postulantes</p>
                </div>
              </div>
            </div>
          ))}
          {filtered.length === 0 && (
            <div className="text-center py-12" style={{ color: 'var(--ink-muted)' }}>
              <p className="text-sm">No hay ofertas en esta categoría</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
