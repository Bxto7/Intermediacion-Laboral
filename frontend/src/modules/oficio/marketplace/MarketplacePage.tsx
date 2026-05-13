import { useState, useEffect } from 'react'
import {
  Search, MapPin, Clock, Star, Briefcase, MessageCircle,
  Plus, Pencil, Trash2, Store, X, Zap, Wrench, Hammer,
  Building2, Paintbrush, Car, Home, Flame, Leaf, SprayCan,
  ChefHat, Scissors,
} from 'lucide-react'
import { LoadingSpinner } from '../../../shared/LoadingSpinner'
import { ContactModal } from '../../../shared/ContactModal'
import { useMyListings, useMarketplaceSearch, ServiceListing, ListingCreate } from '../../../hooks/useMarketplace'
import { useAuthContext } from '../../../context/AuthContext'
import { useWorkerContext } from '../../../context/WorkerContext'

const TRADE_CATEGORIES = [
  'Electricidad', 'Gasfitería', 'Carpintería', 'Albañilería',
  'Pintura', 'Mecánica automotriz', 'Techado', 'Soldadura y metalurgia',
  'Jardinería', 'Limpieza y mantenimiento', 'Cocina y pastelería',
  'Costura y confección', 'Otros oficios',
]

const CATEGORY_ICONS: Record<string, React.ElementType> = {
  'Electricidad': Zap, 'Gasfitería': Wrench, 'Carpintería': Hammer,
  'Albañilería': Building2, 'Pintura': Paintbrush, 'Mecánica automotriz': Car,
  'Techado': Home, 'Soldadura y metalurgia': Flame, 'Jardinería': Leaf,
  'Limpieza y mantenimiento': SprayCan, 'Cocina y pastelería': ChefHat,
  'Costura y confección': Scissors, 'Otros oficios': Briefcase,
}

const DISTRICTS = ['Huancayo', 'El Tambo', 'Chilca']

const AVAIL_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  inmediata: { label: 'Disponible ahora', color: 'var(--olive-deep)', bg: 'var(--olive-100)' },
  semana:    { label: 'Esta semana',      color: 'var(--gold)',       bg: 'var(--gold-100)'  },
  mes:       { label: 'Este mes',         color: 'var(--ink-muted)',  bg: 'rgba(61,40,24,0.06)' },
}

const PRICE_UNIT_LABELS: Record<string, string> = {
  hora: 'por hora', proyecto: 'por proyecto', dia: 'por día',
}

/* ─── Create / Edit Modal ─── */
interface ListingModalProps {
  initial?: ServiceListing | null
  onClose: () => void
  onCreate: (data: ListingCreate) => Promise<void>
  onUpdate: (id: string, data: Partial<ListingCreate>) => Promise<void>
}

const ListingModal: React.FC<ListingModalProps> = ({ initial, onClose, onCreate, onUpdate }) => {
  const [form, setForm] = useState<ListingCreate>({
    trade_category: initial?.trade_category ?? '',
    title: initial?.title ?? '',
    description: initial?.description ?? '',
    districts: initial?.districts ?? [],
    price_reference: initial?.price_reference ?? null,
    price_unit: initial?.price_unit ?? null,
    availability: initial?.availability ?? null,
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const toggle = (list: string[], val: string) =>
    list.includes(val) ? list.filter(x => x !== val) : [...list, val]

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (!form.trade_category) { setError('Selecciona una categoría'); return }
    if (form.title.trim().length < 5) { setError('Título muy corto (mín. 5 caracteres)'); return }
    if (form.description.trim().length < 10) { setError('Descripción muy corta (mín. 10 caracteres)'); return }
    setSaving(true)
    try {
      initial ? await onUpdate(initial.id, form) : await onCreate(form)
      onClose()
    } catch {
      setError('Error al guardar. Intenta de nuevo.')
    } finally {
      setSaving(false)
    }
  }

  const fieldStyle = {
    border: '1px solid #d6c5a8',
    background: 'var(--bg-soft)',
    color: 'var(--ink-strong)',
    borderRadius: '12px',
    fontSize: '14px',
    padding: '10px 14px',
    width: '100%',
    outline: 'none',
    fontFamily: 'inherit',
  } as React.CSSProperties

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto modal-backdrop"
      style={{ background: 'rgba(26,15,10,0.55)', backdropFilter: 'blur(8px)' }}
    >
      <div
        className="modal-panel w-full max-w-lg my-4 overflow-hidden"
        style={{ background: 'var(--bg-elevated)', borderRadius: '24px', boxShadow: '0 50px 100px -30px rgba(0,0,0,0.4)', border: '1px solid var(--line)' }}
      >
        <div className="flex items-center justify-between px-6 pt-6 pb-4" style={{ borderBottom: '1px solid var(--line)' }}>
          <h2 className="font-bold text-base" style={{ color: 'var(--ink-strong)' }}>
            {initial ? 'Editar servicio' : 'Publicar nuevo servicio'}
          </h2>
          <button onClick={onClose} aria-label="Cerrar" className="w-11 h-11 rounded-full flex items-center justify-center transition-colors cursor-pointer" style={{ color: 'var(--ink-muted)' }} onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'rgba(61,40,24,0.07)' }} onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'transparent' }}>
            <X size={16} />
          </button>
        </div>

        <form onSubmit={submit} className="px-6 py-5 space-y-4">
          <div>
            <label className="block text-xs font-semibold mb-1.5" style={{ color: 'var(--ink-strong)' }}>Categoría de oficio *</label>
            <select value={form.trade_category} onChange={e => setForm(p => ({ ...p, trade_category: e.target.value }))} style={fieldStyle}>
              <option value="">Seleccionar...</option>
              {TRADE_CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold mb-1.5" style={{ color: 'var(--ink-strong)' }}>Título *</label>
            <input
              type="text"
              value={form.title}
              onChange={e => setForm(p => ({ ...p, title: e.target.value }))}
              placeholder="Ej: Instalación eléctrica residencial en Huancayo"
              maxLength={200}
              style={fieldStyle}
            />
          </div>

          <div>
            <label className="block text-xs font-semibold mb-1.5" style={{ color: 'var(--ink-strong)' }}>Descripción *</label>
            <textarea
              value={form.description}
              onChange={e => setForm(p => ({ ...p, description: e.target.value }))}
              placeholder="Describe los servicios que ofreces con detalle..."
              maxLength={2000}
              rows={4}
              style={{ ...fieldStyle, resize: 'none' }}
            />
            <p className="text-[11px] mt-0.5 text-right" style={{ color: 'var(--ink-muted)' }}>{form.description.length}/2000</p>
          </div>

          <div>
            <label className="block text-xs font-semibold mb-1.5" style={{ color: 'var(--ink-strong)' }}>Zonas de cobertura</label>
            <div className="flex gap-2 flex-wrap">
              {DISTRICTS.map(d => {
                const active = form.districts.includes(d)
                return (
                  <button
                    key={d}
                    type="button"
                    onClick={() => setForm(p => ({ ...p, districts: toggle(p.districts, d) }))}
                    className="px-3 py-1.5 rounded-full text-xs font-medium transition-all"
                    style={{
                      background: active ? 'var(--terra-500)' : 'transparent',
                      color: active ? '#fff' : 'var(--ink-warm)',
                      border: `1px solid ${active ? 'var(--terra-500)' : 'var(--line-strong)'}`,
                    }}
                  >
                    {d}
                  </button>
                )
              })}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold mb-1.5" style={{ color: 'var(--ink-strong)' }}>Precio referencial (S/.)</label>
              <input
                type="number" min="0" step="0.01"
                value={form.price_reference ?? ''}
                onChange={e => setForm(p => ({ ...p, price_reference: e.target.value ? parseFloat(e.target.value) : null }))}
                placeholder="Opcional"
                style={fieldStyle}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold mb-1.5" style={{ color: 'var(--ink-strong)' }}>Unidad</label>
              <select value={form.price_unit ?? ''} onChange={e => setForm(p => ({ ...p, price_unit: e.target.value || null }))} style={fieldStyle}>
                <option value="">—</option>
                <option value="hora">Por hora</option>
                <option value="proyecto">Por proyecto</option>
                <option value="dia">Por día</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold mb-1.5" style={{ color: 'var(--ink-strong)' }}>Disponibilidad</label>
            <div className="flex gap-2">
              {(['inmediata', 'semana', 'mes'] as const).map(a => {
                const active = form.availability === a
                const cfg = AVAIL_CONFIG[a]
                return (
                  <button
                    key={a}
                    type="button"
                    onClick={() => setForm(p => ({ ...p, availability: p.availability === a ? null : a }))}
                    className="flex-1 py-2 rounded-full text-xs font-medium transition-all"
                    style={{
                      background: active ? cfg.bg : 'transparent',
                      color: active ? cfg.color : 'var(--ink-muted)',
                      border: `1px solid ${active ? cfg.color : 'var(--line-strong)'}`,
                    }}
                  >
                    {cfg.label}
                  </button>
                )
              })}
            </div>
          </div>

          {error && (
            <p className="text-xs rounded-xl px-3 py-2" style={{ background: 'rgba(168,63,63,0.08)', color: 'var(--error)', border: '1px solid rgba(168,63,63,0.18)' }}>
              {error}
            </p>
          )}

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1 py-3">Cancelar</button>
            <button type="submit" disabled={saving} className="btn-primary flex-1 py-3">
              {saving ? 'Guardando...' : initial ? 'Guardar cambios' : 'Publicar servicio'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

/* ─── Listing Card ─── */
const ListingCard: React.FC<{
  listing: ServiceListing
  own?: boolean
  onEdit?: () => void
  onDelete?: () => void
  onContact?: () => void
}> = ({ listing, own, onEdit, onDelete, onContact }) => {
  const avail = listing.availability ? AVAIL_CONFIG[listing.availability] : null
  const CatIcon = CATEGORY_ICONS[listing.trade_category] ?? Briefcase

  return (
    <div className="card-warm p-5 flex flex-col gap-3 transition-all duration-200 hover:-translate-y-0.5">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2.5 flex-1 min-w-0">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: 'var(--terra-100)' }}>
            <CatIcon size={15} style={{ color: 'var(--terra-500)' }} />
          </div>
          <div className="min-w-0">
            <p className="kicker" style={{ color: 'var(--terra-500)' }}>{listing.trade_category}</p>
            <h3 className="font-bold text-sm leading-tight line-clamp-2 mt-0.5" style={{ color: 'var(--ink-strong)' }}>{listing.title}</h3>
          </div>
        </div>
        {avail && (
          <span className="shrink-0 text-[11px] font-medium px-2.5 py-1 rounded-full" style={{ color: avail.color, background: avail.bg }}>
            {avail.label}
          </span>
        )}
      </div>

      <p className="text-xs leading-relaxed line-clamp-3" style={{ color: 'var(--ink-muted)' }}>{listing.description}</p>

      {listing.enriched_keywords.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {listing.enriched_keywords.slice(0, 5).map(k => (
            <span key={k} className="tag">{k}</span>
          ))}
          {listing.enriched_keywords.length > 5 && (
            <span className="text-[11px]" style={{ color: 'var(--ink-muted)' }}>+{listing.enriched_keywords.length - 5}</span>
          )}
        </div>
      )}

      <div className="flex items-center justify-between text-xs pt-2" style={{ borderTop: '1px solid var(--line)', color: 'var(--ink-muted)' }}>
        <div className="flex items-center gap-3">
          {listing.price_reference && (
            <span className="font-semibold" style={{ color: 'var(--ink-warm)' }}>
              S/. {listing.price_reference.toFixed(0)}
              {listing.price_unit && <span className="font-normal"> {PRICE_UNIT_LABELS[listing.price_unit]}</span>}
            </span>
          )}
          {listing.districts.length > 0 && (
            <span className="flex items-center gap-1">
              <MapPin size={10} />
              {listing.districts.join(' · ')}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {listing.worker_avg_rating > 0 && (
            <span className="flex items-center gap-1">
              <Star size={11} fill="currentColor" style={{ color: 'var(--gold)' }} />
              {listing.worker_avg_rating.toFixed(1)}
            </span>
          )}
          {listing.relevance_score != null && (
            <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full" style={{ background: 'var(--olive-100)', color: 'var(--olive-deep)' }}>
              {Math.round(listing.relevance_score * 100)}%
            </span>
          )}
        </div>
      </div>

      {own ? (
        <div className="flex gap-2">
          <button onClick={onEdit} className="btn-secondary flex-1 py-2 text-xs gap-1.5">
            <Pencil size={12} /> Editar
          </button>
          <button
            onClick={onDelete}
            className="py-2 px-3 text-xs font-medium rounded-full transition-colors"
            style={{ border: '1px solid rgba(168,63,63,0.25)', color: 'var(--error)', background: 'transparent' }}
          >
            <Trash2 size={13} />
          </button>
        </div>
      ) : onContact && (
        <button onClick={onContact} className="btn-primary w-full py-2.5 text-xs gap-1.5">
          <MessageCircle size={13} /> Contactar
        </button>
      )}
    </div>
  )
}

/* ─── Main Page ─── */
export const MarketplacePage: React.FC = () => {
  const { user } = useAuthContext()
  const { worker } = useWorkerContext()
  const { listings, isLoading: loadingMine, create, update, remove } = useMyListings()
  const { results, isLoading: loadingSearch, search } = useMarketplaceSearch()

  const defaultTab = worker?.worker_type === 'oficio' ? 'mis-servicios' : 'buscar'
  const [tab, setTab] = useState<'mis-servicios' | 'buscar'>(defaultTab)
  const [showModal, setShowModal] = useState(false)
  const [editTarget, setEditTarget] = useState<ServiceListing | null>(null)
  const [contactTarget, setContactTarget] = useState<ServiceListing | null>(null)

  const [query, setQuery] = useState('')
  const [district, setDistrict] = useState('')
  const [tradeCategory, setTradeCategory] = useState('')
  const [availability, setAvailability] = useState('')

  useEffect(() => {
    if (tab === 'buscar') {
      search({ query: query || undefined, district: district || undefined, trade_category: tradeCategory || undefined, availability: availability || undefined })
    }
  }, [tab, query, district, tradeCategory, availability, search])

  const handleCreate = async (data: ListingCreate) => { await create(data) }
  const handleUpdate = async (id: string, data: Partial<ListingCreate>) => { await update(id, data) }
  const handleDelete = async (id: string) => {
    if (window.confirm('¿Eliminar este servicio del marketplace?')) await remove(id)
  }

  const isOwn = (l: ServiceListing) => worker?.id === l.worker_id || user?.id === l.worker_id

  return (
    <div>

      {/* Hero */}
      <div
        className="relative overflow-hidden py-8 px-4"
        style={{ background: 'linear-gradient(160deg, var(--dark-deep) 0%, var(--dark) 60%, var(--dark-2) 100%)' }}
      >
        <div className="absolute top-0 right-0 w-72 h-72 rounded-full blur-3xl opacity-15 pointer-events-none" style={{ background: 'var(--terra-500)' }} />
        <div className="max-w-5xl mx-auto relative z-10 flex items-center justify-between">
          <div>
            <p className="kicker mb-1" style={{ color: 'var(--on-dark-muted)' }}>Oficio · Linku</p>
            <h1 className="text-xl font-bold tracking-tight" style={{ color: 'var(--on-dark)', letterSpacing: '-0.025em' }}>
              Marketplace de <span className="serif-accent" style={{ color: 'var(--coral)' }}>servicios</span>
            </h1>
            <p className="text-sm mt-0.5" style={{ color: 'var(--on-dark-muted)' }}>
              DRTPE-Junín · Identidad verificada
            </p>
          </div>
          {worker?.worker_type === 'oficio' && (
            <button
              onClick={() => { setEditTarget(null); setShowModal(true) }}
              className="flex items-center gap-2 font-medium text-sm px-5 py-2.5 rounded-full transition-colors"
              style={{ background: 'var(--on-dark)', color: 'var(--dark-deep)' }}
            >
              <Plus size={15} />
              Publicar servicio
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div
        className="sticky z-30"
        style={{ top: '0', background: 'rgba(247,241,232,0.95)', backdropFilter: 'blur(10px)', borderBottom: '1px solid var(--line)' }}
      >
        <div className="max-w-5xl mx-auto px-4">
          <div className="flex gap-1 pt-2">
            {(worker?.worker_type === 'oficio'
              ? ['mis-servicios', 'buscar'] as const
              : ['buscar'] as const
            ).map(t => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className="px-4 py-2.5 text-sm font-semibold rounded-t-xl transition-all"
                style={{
                  color:           tab === t ? 'var(--terra-500)' : 'var(--ink-muted)',
                  borderBottom:    tab === t ? '2px solid var(--terra-500)' : '2px solid transparent',
                  background:      tab === t ? 'var(--bg-elevated)' : 'transparent',
                }}
              >
                {t === 'mis-servicios' ? `Mis servicios (${listings.length})` : 'Explorar marketplace'}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 py-5">

        {/* Mis servicios */}
        {worker?.worker_type === 'oficio' && tab === 'mis-servicios' && (
          loadingMine ? <LoadingSpinner /> : listings.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {listings.map(l => (
                <ListingCard
                  key={l.id} listing={l} own
                  onEdit={() => { setEditTarget(l); setShowModal(true) }}
                  onDelete={() => handleDelete(l.id)}
                />
              ))}
            </div>
          ) : (
            <div
              className="rounded-3xl p-12 text-center max-w-md mx-auto mt-4"
              style={{ background: 'var(--bg-elevated)', border: '2px dashed var(--line-strong)' }}
            >
              <div className="w-16 h-16 rounded-2xl mx-auto mb-4 flex items-center justify-center" style={{ background: 'rgba(61,40,24,0.05)' }}>
                <Store size={28} style={{ color: 'var(--ink-muted)' }} strokeWidth={1.5} />
              </div>
              <h3 className="font-bold text-base mb-1" style={{ color: 'var(--ink-strong)' }}>
                Sin servicios <span className="serif-accent" style={{ color: 'var(--terra-500)' }}>publicados</span>
              </h3>
              <p className="text-sm mb-5" style={{ color: 'var(--ink-muted)' }}>
                Publica tu disponibilidad y deja que empleadores te encuentren.
              </p>
              <button onClick={() => { setEditTarget(null); setShowModal(true) }} className="btn-primary px-6 py-2.5 text-sm gap-2">
                <Plus size={14} /> Publicar mi primer servicio
              </button>
            </div>
          )
        )}

        {/* Buscar */}
        {tab === 'buscar' && (
          <div className="space-y-4">
            <div className="card-warm p-4 space-y-3">
              <div className="relative">
                <Search size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: 'var(--ink-muted)' }} />
                <input
                  type="text"
                  value={query}
                  onChange={e => setQuery(e.target.value)}
                  placeholder='Ej: "necesito electricista para mi casa"'
                  className="w-full pl-10 pr-4 py-3 rounded-xl text-sm transition-all focus:outline-none"
                  style={{ border: '1px solid #d6c5a8', background: 'var(--bg-soft)', color: 'var(--ink-strong)' }}
                  onFocus={e => { e.currentTarget.style.borderColor = 'var(--terra-500)'; e.currentTarget.style.boxShadow = '0 0 0 3px rgba(194,86,46,0.14)' }}
                  onBlur={e => { e.currentTarget.style.borderColor = '#d6c5a8'; e.currentTarget.style.boxShadow = 'none' }}
                />
              </div>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { value: district, onChange: setDistrict, icon: MapPin, placeholder: 'Distrito', options: DISTRICTS },
                  { value: tradeCategory, onChange: setTradeCategory, icon: Briefcase, placeholder: 'Categoría', options: TRADE_CATEGORIES },
                ].map(({ value, onChange, icon: Icon, placeholder, options }, i) => (
                  <div key={i} className="relative">
                    <Icon size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: 'var(--ink-muted)' }} />
                    <select
                      value={value}
                      onChange={e => onChange(e.target.value)}
                      className="w-full pl-7 pr-2 py-2.5 rounded-xl text-xs focus:outline-none appearance-none"
                      style={{ border: '1px solid #d6c5a8', background: 'var(--bg-soft)', color: 'var(--ink-warm)' }}
                    >
                      <option value="">{placeholder}</option>
                      {options.map(o => <option key={o} value={o}>{o}</option>)}
                    </select>
                  </div>
                ))}
                <div className="relative">
                  <Clock size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: 'var(--ink-muted)' }} />
                  <select
                    value={availability}
                    onChange={e => setAvailability(e.target.value)}
                    className="w-full pl-7 pr-2 py-2.5 rounded-xl text-xs focus:outline-none appearance-none"
                    style={{ border: '1px solid #d6c5a8', background: 'var(--bg-soft)', color: 'var(--ink-warm)' }}
                  >
                    <option value="">Disponibilidad</option>
                    <option value="inmediata">Disponible ahora</option>
                    <option value="semana">Esta semana</option>
                    <option value="mes">Este mes</option>
                  </select>
                </div>
              </div>
            </div>

            {loadingSearch ? <LoadingSpinner /> : results.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {results.map(l => (
                  <ListingCard
                    key={l.id}
                    listing={l}
                    own={isOwn(l)}
                    onContact={!isOwn(l) ? () => setContactTarget(l) : undefined}
                  />
                ))}
              </div>
            ) : (
              <div className="text-center py-14 space-y-3">
                <div className="w-14 h-14 rounded-2xl mx-auto flex items-center justify-center" style={{ background: 'rgba(61,40,24,0.06)' }}>
                  <Search size={24} style={{ color: 'var(--ink-muted)' }} />
                </div>
                <p className="text-sm" style={{ color: 'var(--ink-muted)' }}>No se encontraron servicios con esos filtros</p>
              </div>
            )}
          </div>
        )}
      </div>

      {showModal && (
        <ListingModal
          initial={editTarget}
          onClose={() => { setShowModal(false); setEditTarget(null) }}
          onCreate={handleCreate}
          onUpdate={handleUpdate}
        />
      )}

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
