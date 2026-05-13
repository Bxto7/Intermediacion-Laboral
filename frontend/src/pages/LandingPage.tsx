import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { LoginModal } from './landing/LoginModal'
import { LandingNav } from './landing/LandingNav'
import { JOBS, CATEGORIES, COMPANIES, TESTIMONIALS } from './landing/data'
import { LinkuLogoFull } from '../shared/LinkuLogo'

export const LandingPage: React.FC = () => {
  const [loginOpen, setLoginOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const [activeFilter, setActiveFilter] = useState('Todos')
  const [bookmarks, setBookmarks] = useState<Set<number>>(new Set())

  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', fn)
    return () => window.removeEventListener('scroll', fn)
  }, [])

  const toggleBookmark = (id: number) =>
    setBookmarks(prev => { const s = new Set(prev); s.has(id) ? s.delete(id) : s.add(id); return s })

  const filtered = activeFilter === 'Todos' ? JOBS : JOBS.filter(j => j.category === activeFilter)

  const handleLoginClick = () => {
    if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
      sessionStorage.setItem('login_return_url', window.location.pathname + window.location.search)
    }
    setLoginOpen(true)
  }

  const useMouseGlow = () => {
    const ref = useRef<HTMLDivElement>(null)
    const move = (e: React.MouseEvent) => {
      const r = ref.current?.getBoundingClientRect()
      if (r && ref.current) {
        ref.current.style.setProperty('--mouse-x', `${e.clientX - r.left}px`)
        ref.current.style.setProperty('--mouse-y', `${e.clientY - r.top}px`)
      }
    }
    return { ref, onMouseMove: move }
  }

  const JobCard = ({ job }: { job: typeof JOBS[0] }) => {
    const { ref, onMouseMove } = useMouseGlow()
    const saved = bookmarks.has(job.id)
    return (
      <div ref={ref} onMouseMove={onMouseMove} className="job-card card-warm p-5 space-y-4 hover:shadow-warm transition-all cursor-pointer">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-xl flex items-center justify-center text-white text-sm font-bold shadow-warm-sm flex-shrink-0"
              style={{ background: `linear-gradient(135deg, ${job.logoColor}cc, ${job.logoColor})` }}>
              {job.logo}
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <p className="text-sm font-semibold" style={{ color: '#3d2818' }}>{job.company}</p>
                {job.verified && (
                  <svg className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="#2d5a82"><path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/></svg>
                )}
              </div>
              <p className="text-xs" style={{ color: '#8a6648' }}>{job.location}</p>
            </div>
          </div>
          <button onClick={() => toggleBookmark(job.id)} className="p-1.5 rounded-xl transition-colors" style={{ color: saved ? '#c2562e' : '#bba99c' }}>
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill={saved ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/></svg>
          </button>
        </div>
        <div>
          <h3 className="font-semibold text-base leading-snug" style={{ color: '#3d2818' }}>{job.title}</h3>
          <p className="text-sm font-medium mt-1" style={{ color: '#c2562e' }}>{job.salary}</p>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {job.tags.map(t => <span key={t} className="tag-warm text-[11px]">{t}</span>)}
        </div>
      </div>
    )
  }

  return (
    <div className="glow-bg grain min-h-screen">
      <LandingNav onLoginClick={handleLoginClick} scrolled={scrolled} />
      {loginOpen && <LoginModal onClose={() => setLoginOpen(false)} />}

      {/* ═══ HERO ═══ */}
      <section className="pt-32 pb-20 px-5 max-w-6xl mx-auto">
        <div className="flex flex-col lg:flex-row gap-16 items-start">
          <div className="flex-1 space-y-8">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border" style={{ background: 'rgba(194,86,46,0.07)', borderColor: 'rgba(194,86,46,0.20)' }}>
              <div className="w-1.5 h-1.5 rounded-full animate-pulse-slow" style={{ background: '#c2562e' }} />
              <span className="font-mono text-xs uppercase tracking-widest" style={{ color: '#c2562e' }}>Plataforma oficial · Junín, Perú · OFICIAL</span>
            </div>

            <h1 className="hero-heading">
              Tu próximo<br />
              empleo{' '}
              <span style={{ fontFamily: 'Instrument Serif, Georgia, serif', fontStyle: 'italic', color: '#e8a691' }}>
                te espera.
              </span>
            </h1>

            <p className="text-lg leading-relaxed max-w-xl" style={{ color: '#6b4a35' }}>
              La bolsa de empleo formal de la Dirección Regional de Trabajo y Promoción del Empleo de Junín. CV con IA, empleos verificados y matching inteligente.
            </p>

            <div className="flex flex-wrap gap-3">
              <Link to="/register" className="btn-primary text-base px-7 py-3.5">Encontrar empleo</Link>
              <button onClick={() => setLoginOpen(true)} className="btn-secondary text-base px-7 py-3.5">Soy empresa</button>
            </div>
          </div>

          {/* Features aside */}
          <div className="lg:w-80 space-y-3 pt-4">
            {[
              { color: '#c2562e', bg: 'rgba(194,86,46,0.08)', icon: '✦', title: 'CV generado con IA', desc: 'Crea tu CV profesional en minutos con ayuda de inteligencia artificial.' },
              { color: '#2d5a82', bg: 'rgba(45,90,130,0.08)', icon: '◆', title: 'Empleos verificados', desc: 'Todas las ofertas son validadas por la DRTPE-Junín.' },
              { color: '#7a8c5c', bg: 'rgba(122,140,92,0.10)', icon: '●', title: 'Matching por ML', desc: 'El sistema aprende de tu perfil y recomienda empleos compatibles.' },
            ].map(f => (
              <div key={f.title} className="card-warm p-4 flex gap-3.5">
                <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 text-sm font-bold"
                  style={{ background: f.bg, color: f.color }}>
                  {f.icon}
                </div>
                <div>
                  <p className="font-semibold text-sm" style={{ color: '#3d2818' }}>{f.title}</p>
                  <p className="text-xs mt-0.5 leading-relaxed" style={{ color: '#8a6648' }}>{f.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ STATS ═══ */}
      <section style={{ background: 'rgba(61,40,24,0.04)', borderTop: '1px solid rgba(61,40,24,0.08)', borderBottom: '1px solid rgba(61,40,24,0.08)' }}>
        <div className="max-w-6xl mx-auto px-5 py-12 grid grid-cols-2 md:grid-cols-4 gap-8">
          {[
            { value: '2,400+', unit: 'trabajadores', color: '#c2562e' },
            { value: '340+',   unit: 'empresas',     color: '#2d5a82' },
            { value: '180+',   unit: 'empleos',      color: '#b8893a' },
            { value: '87%',    unit: 'colocación',   color: '#7a8c5c' },
          ].map(s => (
            <div key={s.unit} className="text-center space-y-1">
              <p className="stat-number" style={{ color: s.color }}>{s.value}</p>
              <p className="font-mono text-xs uppercase tracking-widest" style={{ color: '#8a6648' }}>{s.unit}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ═══ SEARCH ═══ */}
      <section className="max-w-6xl mx-auto px-5 py-12" id="descubrir">
        <div className="card-warm p-2 flex flex-col md:flex-row gap-2">
          {[
            { ph: '¿Qué buscas?', icon: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg> },
            { ph: 'Dónde (Huancayo…)', icon: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg> },
          ].map(f => (
            <div key={f.ph} className="flex-1 flex items-center gap-2 px-4 py-3 rounded-xl" style={{ background: 'rgba(255,255,255,0.7)' }}>
              <span style={{ color: '#8a6648' }}>{f.icon}</span>
              <input className="flex-1 bg-transparent text-sm outline-none" placeholder={f.ph} style={{ color: '#3d2818' }} />
            </div>
          ))}
          <select className="flex-1 px-4 py-3 rounded-xl text-sm outline-none" style={{ background: 'rgba(255,255,255,0.7)', color: '#3d2818', border: 'none' }}>
            <option>Modalidad</option>
            <option>Full-time</option>
            <option>Part-time</option>
            <option>Por proyecto</option>
          </select>
          <button className="btn-primary px-8 py-3 rounded-xl text-sm">Buscar empleos</button>
        </div>
      </section>

      {/* ═══ EMPLEOS ═══ */}
      <section className="max-w-6xl mx-auto px-5 pb-20 space-y-6">
        <div className="flex items-end justify-between">
          <div>
            <p className="kicker" style={{ color: '#c2562e' }}>Empleos disponibles</p>
            <h2 className="text-3xl font-bold mt-1" style={{ color: '#3d2818', letterSpacing: '-0.03em' }}>Encuentra tu próxima oportunidad</h2>
          </div>
          <p className="text-sm" style={{ color: '#8a6648' }}>{filtered.length} resultados</p>
        </div>

        <div className="flex flex-wrap gap-2">
          {CATEGORIES.map(c => (
            <button key={c} onClick={() => setActiveFilter(c)}
              className="px-4 py-1.5 rounded-full text-sm font-medium transition-all"
              style={activeFilter === c
                ? { background: '#c2562e', color: 'white', border: '1.5px solid #c2562e' }
                : { background: 'rgba(255,255,255,0.55)', color: '#6b4a35', border: '1.5px solid rgba(61,40,24,0.12)' }}>
              {c}
            </button>
          ))}
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          {filtered.map(job => <JobCard key={job.id} job={job} />)}
        </div>

        <div className="text-center pt-4">
          <Link to="/register" className="btn-secondary px-8 py-3">Ver todos los empleos →</Link>
        </div>
      </section>

      {/* ═══ CÓMO FUNCIONA (oscuro) ═══ */}
      <section className="relative overflow-hidden py-20 px-5" style={{ background: 'linear-gradient(135deg, #4a3120 0%, #5a3d2b 100%)' }}>
        <div className="absolute -left-32 top-0 w-64 h-64 rounded-full opacity-20 blur-3xl" style={{ background: '#c2562e' }} />
        <div className="absolute right-0 bottom-0 w-56 h-56 rounded-full opacity-15 blur-3xl" style={{ background: '#7a8c5c' }} />
        <div className="max-w-6xl mx-auto relative z-10 space-y-12">
          <div className="text-center space-y-2">
            <p className="kicker" style={{ color: '#e8a691' }}>Simple y sin fricción</p>
            <h2 className="text-4xl font-bold text-white" style={{ letterSpacing: '-0.03em' }}>
              Cómo{' '}
              <span style={{ fontFamily: 'Instrument Serif, Georgia, serif', fontStyle: 'italic', color: '#e8a691' }}>funciona</span>
            </h2>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              { n: '01', color: '#c2562e', bg: 'rgba(194,86,46,0.15)', title: 'Crea tu perfil', desc: 'Regístrate y responde 2 preguntas. El sistema detecta tu tipo de perfil y personaliza tu experiencia.' },
              { n: '02', color: '#2d5a82', bg: 'rgba(45,90,130,0.15)', title: 'Genera tu CV con IA', desc: 'Nuestro asistente extrae tus habilidades y genera un CV profesional listo para descargar.' },
              { n: '03', color: '#b8893a', bg: 'rgba(184,137,58,0.15)', title: 'Conecta con empleadores', desc: 'El motor de ML cruza tu perfil con ofertas reales y te muestra las más compatibles.' },
            ].map(s => (
              <div key={s.n} className="rounded-2xl p-6 space-y-4" style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}>
                <div className="w-12 h-12 rounded-xl flex items-center justify-center font-bold text-lg"
                  style={{ background: s.bg, color: s.color, border: `1px solid ${s.color}30` }}>
                  {s.n}
                </div>
                <div>
                  <h3 className="font-bold text-white text-lg">{s.title}</h3>
                  <p className="text-sm mt-2 leading-relaxed" style={{ color: 'rgba(255,255,255,0.55)' }}>{s.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ LOGOS EMPRESAS ═══ */}
      <section className="py-16 px-5 border-b" style={{ borderColor: 'rgba(61,40,24,0.08)' }} id="empleadores">
        <div className="max-w-6xl mx-auto space-y-8">
          <p className="text-center font-mono text-xs uppercase tracking-widest" style={{ color: '#8a6648' }}>Empresas que confían en Linku · DRTPE-Junín</p>
          <div className="grid grid-cols-3 md:grid-cols-6 gap-4">
            {COMPANIES.map(c => (
              <div key={c} className="card-warm py-4 px-3 flex items-center justify-center text-center hover:shadow-warm transition-all" style={{ minHeight: 64 }}>
                <span style={{ fontFamily: 'Instrument Serif, Georgia, serif', fontSize: '13px', color: '#6b4a35', fontWeight: 400 }}>{c}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ TESTIMONIOS ═══ */}
      <section className="max-w-6xl mx-auto px-5 py-20 space-y-10" id="recursos">
        <div className="text-center space-y-2">
          <p className="kicker" style={{ color: '#c2562e' }}>Lo que dicen nuestros usuarios</p>
          <h2 className="text-4xl font-bold" style={{ color: '#3d2818', letterSpacing: '-0.03em' }}>
            Historias{' '}
            <span style={{ fontFamily: 'Instrument Serif, Georgia, serif', fontStyle: 'italic', color: '#c2562e' }}>reales</span>
          </h2>
        </div>
        <div className="grid md:grid-cols-3 gap-5">
          {TESTIMONIALS.map(t => (
            <div key={t.name} className="card-warm p-6 space-y-5" style={{ borderTop: `3px solid ${t.color}` }}>
              <p className="text-4xl font-serif leading-none" style={{ color: t.color, opacity: 0.4 }}>"</p>
              <p className="text-sm leading-relaxed" style={{ color: '#5a3d2b' }}>{t.quote}</p>
              <div className="flex items-center gap-3 pt-2">
                <div className="w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
                  style={{ background: t.color }}>
                  {t.initial}
                </div>
                <div>
                  <p className="font-semibold text-sm" style={{ color: '#3d2818' }}>{t.name}</p>
                  <p className="text-xs" style={{ color: '#8a6648' }}>{t.role}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ═══ CTA FINAL ═══ */}
      <section className="relative overflow-hidden py-24 px-5" style={{ background: '#3d2818' }}>
        <div className="absolute left-1/4 top-0 w-80 h-80 rounded-full opacity-25 blur-3xl" style={{ background: '#c2562e' }} />
        <div className="absolute right-1/4 bottom-0 w-64 h-64 rounded-full opacity-20 blur-3xl" style={{ background: '#7a8c5c' }} />
        <div className="max-w-3xl mx-auto relative z-10 text-center space-y-8">
          <h2 className="text-5xl md:text-6xl font-bold text-white leading-tight" style={{ letterSpacing: '-0.04em' }}>
            Empieza hoy.{' '}
            <span style={{ fontFamily: 'Instrument Serif, Georgia, serif', fontStyle: 'italic', color: '#e8a691' }}>
              Es gratis.
            </span>
          </h2>
          <p className="text-lg" style={{ color: 'rgba(255,255,255,0.55)' }}>
            Crea tu cuenta y accede a la bolsa de empleo formal de Junín en menos de 3 minutos.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link to="/register" className="btn-primary text-base px-8 py-4">Crear cuenta gratis</Link>
            <button onClick={() => setLoginOpen(true)}
              className="text-base px-8 py-4 rounded-xl font-semibold transition-all"
              style={{ background: 'rgba(255,255,255,0.08)', color: 'white', border: '1px solid rgba(255,255,255,0.15)' }}>
              Ya tengo cuenta
            </button>
          </div>
        </div>
      </section>

      {/* ═══ FOOTER ═══ */}
      <footer style={{ background: '#3d2818', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
        <div className="max-w-6xl mx-auto px-5 py-14 grid grid-cols-2 md:grid-cols-4 gap-8">
          <div className="col-span-2 md:col-span-1 space-y-3">
            <LinkuLogoFull size={30} variant="white" />
            <p className="text-xs leading-relaxed" style={{ color: 'rgba(255,255,255,0.35)' }}>
              Bolsa de empleo formal respaldada por la Dirección Regional de Trabajo de Junín.
            </p>
          </div>
          {[
            { title: 'Trabajadores', links: ['Buscar empleo', 'Subir CV', 'Orientación laboral', 'Portfolio de oficio'] },
            { title: 'Empresas', links: ['Publicar oferta', 'Buscar candidatos', 'Planes', 'Verificación DRTPE'] },
            { title: 'Institucional', links: ['Acerca de', 'DRTPE-Junín', 'Privacidad', 'Términos'] },
          ].map(col => (
            <div key={col.title} className="space-y-3">
              <p className="font-mono text-xs uppercase tracking-widest" style={{ color: 'rgba(255,255,255,0.40)' }}>{col.title}</p>
              <ul className="space-y-2">
                {col.links.map(l => (
                  <li key={l}>
                    <a href="#" className="text-sm transition-colors" style={{ color: 'rgba(255,255,255,0.45)' }}
                      onMouseEnter={e => (e.currentTarget.style.color = 'rgba(255,255,255,0.85)')}
                      onMouseLeave={e => (e.currentTarget.style.color = 'rgba(255,255,255,0.45)')}>
                      {l}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="border-t px-5 py-5 flex flex-col md:flex-row items-center justify-between gap-2 max-w-6xl mx-auto" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
          <p className="text-xs" style={{ color: 'rgba(255,255,255,0.25)' }}>© 2026 Linku · DRTPE-Junín. Todos los derechos reservados.</p>
          <p className="text-xs font-mono" style={{ color: 'rgba(255,255,255,0.20)' }}>Huancayo, Perú · Investigación aplicada</p>
        </div>
      </footer>
    </div>
  )
}
