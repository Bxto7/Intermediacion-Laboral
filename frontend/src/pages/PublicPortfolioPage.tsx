import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Star, MapPin, Briefcase, Clock, MessageCircle, Search, Shield } from 'lucide-react'
import { SkillTag } from '../shared/SkillTag'
import { ContactModal } from '../shared/ContactModal'
import { LoadingSpinner } from '../shared/LoadingSpinner'
import apiClient from '../api/client'

interface PublicPortfolio {
  worker: {
    display_name: string
    trade_category: string
    district: string
    avg_rating: number
    years_experience: number
  }
  entries: Array<{
    id: string
    title: string
    description: string
    extracted_skills: string[]
    photos: string[]
    client_rating: number | null
  }>
}

export const PublicPortfolioPage: React.FC = () => {
  const { slug } = useParams()
  const [data, setData] = useState<PublicPortfolio | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [contactOpen, setContactOpen] = useState(false)

  const isAuthenticated = !!localStorage.getItem('access_token')

  useEffect(() => {
    apiClient.get(`/portfolio/${slug}`)
      .then(({ data }) => setData(data))
      .catch(() => null)
      .finally(() => setIsLoading(false))
  }, [slug])

  if (isLoading) return <LoadingSpinner fullScreen />

  if (!data) return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--bg-base)' }}>
      <div className="text-center space-y-3">
        <div
          className="w-16 h-16 rounded-3xl mx-auto flex items-center justify-center"
          style={{ background: 'rgba(42,29,20,0.06)' }}
        >
          <Search size={28} style={{ color: 'var(--ink-muted)' }} />
        </div>
        <p className="font-semibold" style={{ color: 'var(--ink-strong)' }}>Perfil no encontrado</p>
        <p className="text-sm" style={{ color: 'var(--ink-muted)' }}>El enlace puede haber expirado</p>
      </div>
    </div>
  )

  const { worker, entries } = data
  const allSkills = [...new Set(entries.flatMap((e) => e.extracted_skills))]

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg-base)' }}>
      {/* Hero header */}
      <div
        className="relative overflow-hidden py-12 px-4"
        style={{
          background: 'linear-gradient(160deg, var(--dark-deep) 0%, var(--dark) 60%, var(--dark-2) 100%)',
        }}
      >
        <div className="absolute top-0 right-0 w-80 h-80 rounded-full blur-3xl opacity-15 pointer-events-none" style={{ background: 'var(--terra-500)' }} />
        <div className="absolute bottom-0 left-0 w-60 h-60 rounded-full blur-3xl opacity-10 pointer-events-none" style={{ background: 'var(--olive)' }} />

        <div className="max-w-3xl mx-auto text-center relative z-10">
          {/* Avatar */}
          <div
            className="w-20 h-20 rounded-full mx-auto mb-4 flex items-center justify-center text-3xl font-bold"
            style={{ background: 'linear-gradient(135deg, var(--terra-400), var(--terra-500))', color: '#fff' }}
          >
            {worker.display_name[0]}
          </div>

          <h1 className="text-2xl font-bold tracking-tight mb-1" style={{ color: 'var(--on-dark)', letterSpacing: '-0.025em' }}>
            {worker.display_name}
          </h1>
          <p className="text-sm mb-3" style={{ color: 'var(--on-dark-muted)' }}>
            {worker.trade_category} · {worker.district}
          </p>

          {/* Stats row */}
          <div className="flex items-center justify-center gap-5 text-sm mb-4">
            <span className="flex items-center gap-1.5" style={{ color: 'var(--on-dark-muted)' }}>
              <Star size={14} style={{ color: 'var(--gold-light)' }} />
              <span style={{ color: 'var(--on-dark)' }}>{worker.avg_rating.toFixed(1)}</span>/5.0
            </span>
            <span style={{ color: 'rgba(244,236,224,0.3)' }}>·</span>
            <span className="flex items-center gap-1.5" style={{ color: 'var(--on-dark-muted)' }}>
              <Clock size={14} />
              {worker.years_experience} años de exp.
            </span>
            <span style={{ color: 'rgba(244,236,224,0.3)' }}>·</span>
            <span className="flex items-center gap-1.5" style={{ color: 'var(--on-dark-muted)' }}>
              <MapPin size={14} />
              {worker.district}
            </span>
          </div>

          {/* Skills preview */}
          {allSkills.length > 0 && (
            <div className="flex flex-wrap justify-center gap-1.5">
              {allSkills.slice(0, 8).map((s) => (
                <span
                  key={s}
                  className="text-xs px-2.5 py-1 rounded-full"
                  style={{ background: 'rgba(244,236,224,0.12)', color: 'var(--on-dark)', border: '1px solid rgba(244,236,224,0.15)' }}
                >
                  {s}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Trabajos realizados */}
      <div className="max-w-3xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-bold text-lg" style={{ color: 'var(--ink-strong)', letterSpacing: '-0.02em' }}>
            Trabajos <span className="serif-accent" style={{ color: 'var(--terra-500)' }}>realizados</span>{' '}
            <span className="text-base font-normal" style={{ color: 'var(--ink-muted)' }}>({entries.length})</span>
          </h2>
        </div>

        {entries.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {entries.map((entry) => (
              <div key={entry.id} className="card-warm overflow-hidden transition-all duration-200 hover:-translate-y-0.5">
                {entry.photos[0] && (
                  <div className="h-44 overflow-hidden">
                    <img src={entry.photos[0]} alt={entry.title} className="w-full h-full object-cover" />
                  </div>
                )}
                <div className="p-4 space-y-2.5">
                  <h3 className="font-semibold text-sm" style={{ color: 'var(--ink-strong)' }}>{entry.title}</h3>
                  <p className="text-xs leading-relaxed line-clamp-3" style={{ color: 'var(--ink-muted)' }}>{entry.description}</p>
                  <div className="flex flex-wrap gap-1">
                    {entry.extracted_skills.slice(0, 4).map((s) => (
                      <SkillTag key={s} label={s} color="amber" />
                    ))}
                  </div>
                  {entry.client_rating && (
                    <div className="flex items-center gap-1 pt-1">
                      {Array.from({ length: Math.round(entry.client_rating) }).map((_, i) => (
                        <Star key={i} size={12} fill="currentColor" style={{ color: 'var(--gold)' }} />
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 space-y-3">
            <div className="w-14 h-14 rounded-2xl mx-auto flex items-center justify-center" style={{ background: 'rgba(42,29,20,0.06)' }}>
              <Briefcase size={22} style={{ color: 'var(--ink-muted)' }} />
            </div>
            <p className="text-sm" style={{ color: 'var(--ink-muted)' }}>Sin trabajos publicados aún</p>
          </div>
        )}

        {/* CTA contacto */}
        <div className="mt-10 text-center space-y-3">
          {isAuthenticated ? (
            <button onClick={() => setContactOpen(true)} className="btn-primary px-8 py-3.5 text-sm gap-2">
              <MessageCircle size={16} />
              Contactar a {worker.display_name.split(' ')[0]}
            </button>
          ) : (
            <button
              onClick={() => {
                sessionStorage.setItem('login_return_url', window.location.pathname)
                window.location.href = '/login'
              }}
              className="btn-primary inline-flex items-center gap-2 px-8 py-3.5 text-sm cursor-pointer"
            >
              <MessageCircle size={16} />
              Inicia sesión para contactar
            </button>
          )}
          <div className="flex items-center justify-center gap-1.5 text-xs" style={{ color: 'var(--ink-muted)' }}>
            <Shield size={12} style={{ color: 'var(--blue)' }} />
            Plataforma Linku · DRTPE-Junín · Identidad verificada
          </div>
        </div>
      </div>

      {contactOpen && (
        <ContactModal
          workerUsername={slug}
          workerName={worker.display_name}
          listingTitle={`Portfolio — ${worker.trade_category}`}
          onClose={() => setContactOpen(false)}
        />
      )}
    </div>
  )
}
