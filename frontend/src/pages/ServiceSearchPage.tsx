import { useState, useEffect } from 'react'
import { Search, MapPin, Clock, Star, Briefcase, Shield, MessageCircle, Zap, Wrench, Hammer, Building2, Paintbrush, Car, Home, Flame, Leaf, SprayCan, ChefHat, Scissors } from 'lucide-react'
import { NavBar } from '../shared/NavBar'
import { ContactModal } from '../shared/ContactModal'
import { LoadingSpinner } from '../shared/LoadingSpinner'
import { ServiceListing, useMarketplaceSearch } from '../hooks/useMarketplace'

const TRADE_CATEGORIES = [
  { value: 'Electricidad',            label: 'Electricidad',       Icon: Zap },
  { value: 'Gasfitería',             label: 'Gasfitería',          Icon: Wrench },
  { value: 'Carpintería',            label: 'Carpintería',         Icon: Hammer },
  { value: 'Albañilería',            label: 'Albañilería',         Icon: Building2 },
  { value: 'Pintura',                label: 'Pintura',             Icon: Paintbrush },
  { value: 'Mecánica automotriz',    label: 'Mecánica',            Icon: Car },
  { value: 'Techado',                label: 'Techado',             Icon: Home },
  { value: 'Soldadura y metalurgia', label: 'Soldadura',           Icon: Flame },
  { value: 'Jardinería',             label: 'Jardinería',          Icon: Leaf },
  { value: 'Limpieza y mantenimiento', label: 'Limpieza',          Icon: SprayCan },
  { value: 'Cocina y pastelería',    label: 'Cocina',              Icon: ChefHat },
  { value: 'Costura y confección',   label: 'Costura',             Icon: Scissors },
  { value: 'Otros oficios',          label: 'Otros',               Icon: Briefcase },
]

const DISTRICTS = ['Huancayo', 'El Tambo', 'Chilca']

const AVAIL_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  inmediata: { label: 'Disponible ahora', color: 'var(--olive-deep)', bg: 'var(--olive-100)' },
  semana:    { label: 'Esta semana',      color: 'var(--gold)',       bg: 'var(--gold-100)'  },
  mes:       { label: 'Este mes',         color: 'var(--ink-muted)',  bg: 'rgba(42,29,20,0.06)' },
}

const PRICE_UNIT_LABELS: Record<string, string> = {
  hora:     'por hora',
  proyecto: 'por proyecto',
  dia:      'por día',
}

const isAuthenticated = () => !!localStorage.getItem('access_token')

interface ListingCardProps {
  listing: ServiceListing
  onContact: () => void
}

const ListingCard: React.FC<ListingCardProps> = ({ listing, onContact }) => {
  const avail = listing.availability ? AVAIL_CONFIG[listing.availability] : null
  const CatIcon = TRADE_CATEGORIES.find(c => c.value === listing.trade_category)?.Icon ?? Briefcase

  return (
    <div
      className="card-warm p-5 flex flex-col gap-3 transition-all duration-200 hover:-translate-y-0.5"
      style={{ cursor: 'default' }}
    >
      {/* Top row */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2.5 flex-1 min-w-0">
          <div
            className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{ background: 'var(--terra-100)' }}
          >
            <CatIcon size={16} style={{ color: 'var(--terra-500)' }} />
          </div>
          <div className="min-w-0">
            <span className="kicker" style={{ color: 'var(--terra-500)' }}>{listing.trade_category}</span>
            <h3 className="font-semibold text-sm mt-0.5 line-clamp-2 leading-snug" style={{ color: 'var(--ink-strong)' }}>
              {listing.title}
            </h3>
          </div>
        </div>
        {avail && (
          <span
            className="text-[11px] px-2.5 py-1 rounded-full font-medium whitespace-nowrap flex-shrink-0"
            style={{ color: avail.color, background: avail.bg }}
          >
            {avail.label}
          </span>
        )}
      </div>

      <p className="text-xs leading-relaxed line-clamp-3" style={{ color: 'var(--ink-muted)' }}>
        {listing.description}
      </p>

      {listing.enriched_keywords.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {listing.enriched_keywords.slice(0, 4).map(k => (
            <span key={k} className="tag">{k}</span>
          ))}
          {listing.enriched_keywords.length > 4 && (
            <span className="text-[11px]" style={{ color: 'var(--ink-muted)' }}>+{listing.enriched_keywords.length - 4}</span>
          )}
        </div>
      )}

      {/* Meta */}
      <div className="pt-3 flex flex-col gap-1.5" style={{ borderTop: '1px solid var(--line)' }}>
        <div className="flex items-center justify-between text-xs">
          <span style={{ color: 'var(--ink-warm)' }}>
            {listing.price_reference
              ? `S/. ${Number(listing.price_reference).toFixed(2)} ${PRICE_UNIT_LABELS[listing.price_unit ?? ''] ?? ''}`
              : 'Precio a coordinar'}
          </span>
          <span className="flex items-center gap-1" style={{ color: 'var(--ink-muted)' }}>
            <MapPin size={11} />
            {listing.districts.join(', ')}
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--ink-muted)' }}>
          <span className="flex items-center gap-1">
            <Star size={11} style={{ color: 'var(--gold)' }} />
            {listing.worker_avg_rating.toFixed(1)}
          </span>
          <span>·</span>
          <span>{listing.worker_years_experience} años</span>
          {listing.worker_name && (
            <>
              <span>·</span>
              <span className="font-medium" style={{ color: 'var(--ink-warm)' }}>{listing.worker_name}</span>
            </>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        {listing.worker_username && (
          <a
            href={`/p/${listing.worker_username}`}
            className="flex-1 py-2 text-xs font-medium text-center rounded-full transition-colors"
            style={{ border: '1px solid var(--line-strong)', color: 'var(--ink-warm)' }}
            onMouseEnter={e => { (e.currentTarget as HTMLAnchorElement).style.background = 'rgba(42,29,20,0.04)' }}
            onMouseLeave={e => { (e.currentTarget as HTMLAnchorElement).style.background = 'transparent' }}
          >
            Ver portfolio
          </a>
        )}
        {isAuthenticated() ? (
          <button
            onClick={onContact}
            className="btn-primary flex-1 py-2 text-xs gap-1.5"
          >
            <MessageCircle size={13} />
            Contactar
          </button>
        ) : (
          <button
            onClick={() => {
              sessionStorage.setItem('login_return_url', window.location.pathname + window.location.search)
              window.location.href = '/login'
            }}
            className="btn-primary flex-1 py-2 text-xs cursor-pointer"
          >
            Inicia sesión para contactar
          </button>
        )}
      </div>
    </div>
  )
}

export const ServiceSearchPage: React.FC = () => {
  const { results, isLoading, search } = useMarketplaceSearch()
  const [query, setQuery] = useState('')
  const [district, setDistrict] = useState('')
  const [tradeCategory, setTradeCategory] = useState('')
  const [availability, setAvailability] = useState('')
  const [contactTarget, setContactTarget] = useState<ServiceListing | null>(null)

  useEffect(() => {
    search({ query: query || undefined, district: district || undefined, trade_category: tradeCategory || undefined, availability: availability || undefined, limit: 30 })
  }, [query, district, tradeCategory, availability])

  return (
    <div className="min-h-screen pb-16" style={{ background: 'var(--bg-base)' }}>
      <NavBar />

      {/* Hero */}
      <div
        className="py-12 px-4 text-center"
        style={{
          background: 'linear-gradient(160deg, var(--dark) 0%, var(--dark-2) 100%)',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <div className="absolute top-0 left-1/4 w-64 h-64 rounded-full blur-3xl pointer-events-none opacity-20" style={{ background: 'var(--terra-500)' }} />
        <div className="absolute bottom-0 right-1/4 w-48 h-48 rounded-full blur-3xl pointer-events-none opacity-15" style={{ background: 'var(--olive)' }} />
        <div className="relative z-10">
          <p className="kicker mb-3" style={{ color: 'var(--on-dark-muted)' }}>Servicios de oficio</p>
          <h1 className="text-3xl font-bold tracking-tight mb-2" style={{ color: 'var(--on-dark)', letterSpacing: '-0.03em' }}>
            Encuentra un{' '}
            <span className="serif-accent" style={{ color: 'var(--coral)' }}>trabajador de oficio</span>
          </h1>
          <p className="text-sm" style={{ color: 'var(--on-dark-muted)' }}>
            Identidad verificada · Linku · DRTPE-Junín
          </p>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 py-6 space-y-5">

        {/* Filtros por categoría */}
        <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
          {TRADE_CATEGORIES.map(({ value, label, Icon }) => {
            const active = tradeCategory === value
            return (
              <button
                key={value}
                onClick={() => setTradeCategory(prev => prev === value ? '' : value)}
                className="flex-shrink-0 flex items-center gap-1.5 px-3 py-2 rounded-full text-xs font-medium border transition-all duration-150"
                style={{
                  background: active ? 'var(--terra-500)' : 'var(--bg-elevated)',
                  color:      active ? '#fff' : 'var(--ink-warm)',
                  borderColor: active ? 'var(--terra-500)' : 'var(--line-strong)',
                }}
              >
                <Icon size={12} />
                {label}
              </button>
            )
          })}
        </div>

        {/* Búsqueda + filtros */}
        <div className="card-warm p-4 space-y-3">
          <div className="relative">
            <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: 'var(--ink-muted)' }} />
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder='Ej: "necesito electricista para instalar tomacorrientes en mi casa"'
              className="w-full pl-10 pr-4 py-3 rounded-xl text-sm transition-all focus:outline-none"
              style={{ border: '1px solid #d6c5a8', background: 'var(--bg-soft)', color: 'var(--ink-strong)' }}
              onFocus={e => { e.currentTarget.style.borderColor = 'var(--terra-500)'; e.currentTarget.style.boxShadow = '0 0 0 3px rgba(184,68,42,0.14)' }}
              onBlur={e => { e.currentTarget.style.borderColor = '#d6c5a8'; e.currentTarget.style.boxShadow = 'none' }}
            />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div className="relative">
              <MapPin size={13} className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: 'var(--ink-muted)' }} />
              <select
                value={district}
                onChange={e => setDistrict(e.target.value)}
                className="w-full pl-8 pr-4 py-2.5 rounded-xl text-sm focus:outline-none appearance-none"
                style={{ border: '1px solid #d6c5a8', background: 'var(--bg-soft)', color: 'var(--ink-warm)' }}
              >
                <option value="">Todos los distritos</option>
                {DISTRICTS.map(d => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
            <div className="relative">
              <Clock size={13} className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: 'var(--ink-muted)' }} />
              <select
                value={availability}
                onChange={e => setAvailability(e.target.value)}
                className="w-full pl-8 pr-4 py-2.5 rounded-xl text-sm focus:outline-none appearance-none"
                style={{ border: '1px solid #d6c5a8', background: 'var(--bg-soft)', color: 'var(--ink-warm)' }}
              >
                <option value="">Cualquier disponibilidad</option>
                <option value="inmediata">Disponible ahora</option>
                <option value="semana">Esta semana</option>
                <option value="mes">Este mes</option>
              </select>
            </div>
          </div>
        </div>

        {/* Badge DRTPE */}
        <div
          className="rounded-xl px-4 py-3 flex items-center gap-2.5"
          style={{ background: 'var(--blue-100)', border: '1px solid rgba(15,110,110,0.18)' }}
        >
          <Shield size={15} className="flex-shrink-0" style={{ color: 'var(--blue)' }} />
          <p className="text-xs leading-relaxed" style={{ color: 'var(--blue)' }}>
            Todos los trabajadores están registrados y su identidad verificada por la{' '}
            <strong>Dirección Regional de Trabajo y Promoción del Empleo — Junín</strong>.
          </p>
        </div>

        {/* Resultados */}
        {isLoading ? (
          <LoadingSpinner />
        ) : results.length > 0 ? (
          <>
            <p className="text-xs" style={{ color: 'var(--ink-muted)' }}>{results.length} servicios encontrados</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {results.map(l => (
                <ListingCard
                  key={l.id}
                  listing={l}
                  onContact={() => setContactTarget(l)}
                />
              ))}
            </div>
          </>
        ) : (
          <div className="text-center py-16 space-y-3">
            <div
              className="w-16 h-16 rounded-3xl mx-auto flex items-center justify-center"
              style={{ background: 'rgba(42,29,20,0.06)' }}
            >
              <Search size={28} style={{ color: 'var(--ink-muted)' }} />
            </div>
            <p className="font-semibold" style={{ color: 'var(--ink-strong)' }}>
              No se encontraron <span className="serif-accent">servicios</span>
            </p>
            <p className="text-sm" style={{ color: 'var(--ink-muted)' }}>
              Prueba con otros filtros o describe lo que necesitas
            </p>
          </div>
        )}
      </div>

      {contactTarget && (
        <ContactModal
          listingId={contactTarget.id}
          workerName={contactTarget.worker_name}
          listingTitle={contactTarget.title}
          onClose={() => setContactTarget(null)}
        />
      )}
    </div>
  )
}
