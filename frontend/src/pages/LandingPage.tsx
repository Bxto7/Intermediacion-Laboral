import { useState, useEffect } from 'react'
import { LoginModal } from './landing/LoginModal'
import { RegisterModal } from './landing/RegisterModal'
import { LandingNav } from './landing/LandingNav'
import { DrtpeSeal } from './landing/DrtpeSeal'
import { JOBS, CATEGORIES, TESTIMONIALS } from './landing/data'
import { Reveal } from '../shared/Reveal'

// Paleta institucional para acentos de tarjetas/empresas
const ACCENTS = ['#b8442a', '#0f6e6e', '#e0a32e', '#9e2b25', '#147a7a', '#b07d12']

// Logo real por empresa (en public/logos/). Si no hay match, se usa la inicial.
const JOB_LOGOS: Record<string, string> = {
  'Volcan Mining': '/logos/volcan.png',
  'Caja Huancayo': '/logos/caja-huancayo.png',
  'Constructora Wari': '/logos/constructora-wari.png',
  'Hidrandina': '/logos/hidrandina.png',
  'Agroindustria Junín': '/logos/agroindustria.png',
  'Doe Run Perú': '/logos/doe-run.png',
}

// Logo de empresa en tarjeta de empleo: imagen real con respaldo a inicial.
const JobLogo: React.FC<{ company: string; initials: string; accent: string }> = ({ company, initials, accent }) => {
  const src = JOB_LOGOS[company]
  const [err, setErr] = useState(false)
  if (src && !err) {
    return (
      <div className="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0 bg-white" style={{ border: '1px solid rgba(42,29,20,0.08)' }}>
        <img src={src} alt={company} className="w-full h-full object-contain p-1.5" loading="lazy" onError={() => setErr(true)} />
      </div>
    )
  }
  return (
    <div className="w-11 h-11 rounded-xl flex items-center justify-center text-white text-sm font-bold flex-shrink-0"
      style={{ background: `linear-gradient(140deg, ${accent}, ${accent}d0)` }}>
      {initials}
    </div>
  )
}

// Entidades y empresas registradas en la plataforma
interface Company { name: string; initials: string; logo?: string }
const COMPANIES: Company[] = [
  { name: 'Cementos Andinos',  initials: 'CA', logo: '/logos/cementos-andinos.png' },
  { name: 'Doe Run',           initials: 'DR', logo: '/logos/doe-run.png' },
  { name: 'Hidrandina',        initials: 'HD', logo: '/logos/hidrandina.png' },
  { name: 'Volcan Mining',     initials: 'VM', logo: '/logos/volcan.png' },
  { name: 'Agroindustria',     initials: 'AJ', logo: '/logos/agroindustria.png' },
  { name: 'Caja Huancayo',     initials: 'CH', logo: '/logos/caja-huancayo.png' },
  { name: 'Constructora Wari', initials: 'CW', logo: '/logos/constructora-wari.png' },
  { name: 'Peruarbo',          initials: 'PA', logo: '/logos/peruarbo.png' },
  { name: 'Electro Centro',    initials: 'EC', logo: '/logos/electro-centro.png' },
  { name: 'SEDAM Huancayo',    initials: 'SH', logo: '/logos/sedam-huancayo.png' },
  { name: 'Coop. Tocache',     initials: 'CT', logo: '/logos/coop-tocache.png' },
  { name: 'SEDAPAL Junín',     initials: 'SJ', logo: '/logos/sedapal.png' },
]

const CompanyLogo: React.FC<{ c: Company; i: number }> = ({ c, i }) => {
  const [imgError, setImgError] = useState(false)
  const accent = ACCENTS[i % ACCENTS.length]
  return (
    <div className="icard icard-hover py-4 px-3 flex flex-col items-center justify-center gap-2 text-center" style={{ minHeight: 86 }}>
      {c.logo && !imgError ? (
        <img src={c.logo} alt={c.name} onError={() => setImgError(true)} className="h-9 max-w-[85%] object-contain" loading="lazy" />
      ) : (
        <div className="w-9 h-9 rounded-lg flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
          style={{ background: `linear-gradient(140deg, ${accent}, ${accent}cc)` }}>
          {c.initials}
        </div>
      )}
      <span style={{ fontSize: 11, color: '#6e5d49', fontWeight: 500, lineHeight: 1.3 }}>{c.name}</span>
    </div>
  )
}

export const LandingPage: React.FC = () => {
  const [loginOpen, setLoginOpen] = useState(false)
  const [registerOpen, setRegisterOpen] = useState(false)
  const openRegister = () => { setLoginOpen(false); setRegisterOpen(true) }
  const openLogin = () => { setRegisterOpen(false); setLoginOpen(true) }
  const [scrolled, setScrolled] = useState(false)
  const [activeFilter, setActiveFilter] = useState('Todos')

  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 24)
    window.addEventListener('scroll', fn)
    return () => window.removeEventListener('scroll', fn)
  }, [])

  const handleLoginClick = () => {
    const PUBLIC = ['/', '/login', '/register', '/servicios']
    const path = window.location.pathname
    if (!PUBLIC.includes(path) && !path.startsWith('/p/')) {
      sessionStorage.setItem('login_return_url', path + window.location.search)
    }
    setLoginOpen(true)
  }

  const filtered = activeFilter === 'Todos' ? JOBS : JOBS.filter(j => j.category === activeFilter)

  // ── Tarjeta de vacante ──
  const JobCard = ({ job, i }: { job: typeof JOBS[0]; i: number }) => {
    const accent = ACCENTS[i % ACCENTS.length]
    return (
      <div className="icard icard-hover p-5 space-y-4 cursor-pointer">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <JobLogo company={job.company} initials={job.logo} accent={accent} />
            <div className="min-w-0">
              <p className="text-sm font-semibold truncate" style={{ color: '#2a1d14' }}>{job.company}</p>
              <p className="text-xs flex items-center gap-1" style={{ color: '#6e5d49' }}>
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <circle cx="12" cy="11" r="2.5" />
                </svg>
                {job.location}
              </p>
            </div>
          </div>
          {job.verified && (
            <span className="inst-verified flex-shrink-0">
              <svg className="w-3 h-3" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" /></svg>
              DRTPE
            </span>
          )}
        </div>
        <div>
          <h3 className="font-semibold text-base leading-snug" style={{ color: '#2a1d14' }}>{job.title}</h3>
          <p className="text-sm font-semibold mt-1" style={{ color: '#0f6e6e' }}>{job.salary}</p>
        </div>
        <div className="flex items-center justify-between pt-1" style={{ borderTop: '1px solid rgba(42,29,20,0.07)' }}>
          <div className="flex flex-wrap gap-1.5">
            {job.tags.map(t => (
              <span key={t} className="text-[11px] px-2.5 py-1 rounded-full font-medium" style={{ background: 'rgba(15,110,110,0.06)', color: '#5a4a39' }}>{t}</span>
            ))}
          </div>
          <span className="text-[13px] font-semibold" style={{ color: '#0f6e6e' }}>Postular →</span>
        </div>
      </div>
    )
  }

  return (
    <div className="linku-landing min-h-screen">
      <LandingNav onLoginClick={handleLoginClick} onRegisterClick={openRegister} scrolled={scrolled} />
      {loginOpen && <LoginModal onClose={() => setLoginOpen(false)} onSwitchToRegister={openRegister} />}
      {registerOpen && <RegisterModal onClose={() => setRegisterOpen(false)} onSwitchToLogin={openLogin} />}

      {/* ═══════════════ HERO ═══════════════ */}
      <section className="inst-glow inst-grid relative overflow-hidden">
        {/* sello marca de agua (giratorio) */}
        <div className="absolute -right-20 top-20 opacity-[0.08] pointer-events-none hidden lg:block">
          <DrtpeSeal size={480} tone="navy" />
        </div>

        <div className="max-w-6xl mx-auto px-5 pt-32 md:pt-36 pb-16 relative z-10">
          <div className="grid lg:grid-cols-[1.15fr_0.85fr] gap-12 lg:gap-10 items-center">
            {/* Columna izquierda */}
            <div>
              <div className="flex items-center gap-2.5 inst-rise" style={{ animationDelay: '0.05s' }}>
                <span className="inline-flex items-center justify-center bg-white rounded-xl px-2.5 py-1.5" style={{ border: '1px solid rgba(42,29,20,0.10)', boxShadow: '0 6px 16px -12px rgba(42,29,20,0.5)' }}>
                  <img src="/institucional/gobierno-regional-junin.png" alt="Gobierno Regional de Junín" className="h-8 w-auto object-contain" onError={(e) => { e.currentTarget.style.display = 'none' }} />
                </span>
                <span className="inline-flex items-center justify-center bg-white rounded-xl px-2.5 py-1.5" style={{ border: '1px solid rgba(42,29,20,0.10)', boxShadow: '0 6px 16px -12px rgba(42,29,20,0.5)' }}>
                  <img src="/institucional/drtpe.png" alt="DRTPE" className="h-8 w-auto object-contain" onError={(e) => { e.currentTarget.style.display = 'none' }} />
                </span>
                <span className="text-xs font-medium leading-tight pl-1" style={{ color: '#6e5d49' }}>Iniciativa oficial<br />del Estado</span>
              </div>

              <h1 className="inst-hero-h1 mt-6 inst-rise" style={{ animationDelay: '0.12s' }}>
                El empleo <span className="inst-it">formal</span><br />
                de Junín, en<br />
                un solo lugar.
              </h1>

              <p className="text-lg leading-relaxed mt-6 max-w-xl inst-rise" style={{ color: '#6e5d49', animationDelay: '0.2s' }}>
                Bolsa de trabajo de la Dirección Regional de Trabajo y Promoción del Empleo.
                CV asistido con IA, vacantes verificadas y emparejamiento inteligente por habilidades.
              </p>

              {/* Buscador */}
              <div className="icard p-2 flex flex-col sm:flex-row gap-2 mt-8 inst-rise" style={{ animationDelay: '0.28s' }}>
                <div className="flex-1 flex items-center gap-2 px-3.5 py-3 rounded-xl" style={{ background: '#f4ece0' }}>
                  <svg className="w-4 h-4 flex-shrink-0" style={{ color: '#6e5d49' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" /></svg>
                  <input className="flex-1 bg-transparent text-sm outline-none" placeholder="Cargo, oficio o empresa…" style={{ color: '#2a1d14' }} />
                </div>
                <div className="flex items-center gap-2 px-3.5 py-3 rounded-xl sm:w-44" style={{ background: '#f4ece0' }}>
                  <svg className="w-4 h-4 flex-shrink-0" style={{ color: '#6e5d49' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><circle cx="12" cy="11" r="2.5" /></svg>
                  <input className="flex-1 bg-transparent text-sm outline-none w-full" placeholder="Huancayo…" style={{ color: '#2a1d14' }} />
                </div>
                <button onClick={openRegister} className="ibtn ibtn-navy">Buscar empleo</button>
              </div>

              {/* chips de búsqueda rápida */}
              <div className="flex flex-wrap items-center gap-2 mt-4 inst-rise" style={{ animationDelay: '0.34s' }}>
                <span className="text-xs font-medium" style={{ color: '#8a7860' }}>Populares:</span>
                {['Minería', 'Construcción', 'Banca', 'TI', 'Gastronomía'].map(c => (
                  <button key={c} onClick={() => { setActiveFilter(c); document.getElementById('empleos')?.scrollIntoView({ behavior: 'smooth' }) }}
                    className="text-xs font-medium px-2.5 py-1 rounded-full transition-colors"
                    style={{ background: '#fff', border: '1px solid rgba(42,29,20,0.12)', color: '#5a4a39' }}>
                    {c}
                  </button>
                ))}
              </div>
            </div>

            {/* Columna derecha — credencial de vacante verificada */}
            <div className="inst-rise hidden lg:block" style={{ animationDelay: '0.4s' }}>
              <div className="icard p-6 relative" style={{ background: 'linear-gradient(160deg, #ffffff, #f4ece0)' }}>
                <div className="absolute -top-5 -right-5">
                  <DrtpeSeal size={84} tone="navy" />
                </div>
                <p className="inst-kicker">Vacante verificada · Nº 2026-0471</p>
                <div className="flex items-center gap-3 mt-4">
                  <JobLogo company="Volcan Mining" initials="VM" accent="#0f6e6e" />
                  <div>
                    <p className="font-semibold" style={{ color: '#2a1d14' }}>Volcan Mining</p>
                    <p className="text-xs" style={{ color: '#6e5d49' }}>Yauli · Minería</p>
                  </div>
                </div>
                <h3 className="text-lg font-semibold mt-4" style={{ color: '#2a1d14' }}>Operario planta concentradora</h3>
                <p className="text-sm font-semibold mt-1" style={{ color: '#0f6e6e' }}>S/. 2,200 – 2,800</p>

                <div className="mt-5 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span style={{ color: '#6e5d49' }}>Compatibilidad con tu perfil</span>
                    <span className="font-bold" style={{ color: '#b07d12' }}>92%</span>
                  </div>
                  <div className="h-2 rounded-full overflow-hidden" style={{ background: 'rgba(42,29,20,0.08)' }}>
                    <div className="h-full rounded-full" style={{ width: '92%', background: 'linear-gradient(90deg, #147a7a, #e0a32e)' }} />
                  </div>
                </div>

                <div className="flex items-center gap-2 mt-5 pt-4" style={{ borderTop: '1px solid rgba(42,29,20,0.08)' }}>
                  <span className="inst-verified">
                    <svg className="w-3 h-3" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812z" clipRule="evenodd" /></svg>
                    Validada por DRTPE
                  </span>
                  <span className="text-xs" style={{ color: '#8a7860' }}>Publicada hoy</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Ticker de vacantes recientes */}
        <div className="inst-ticker relative overflow-hidden border-y" style={{ borderColor: 'rgba(42,29,20,0.08)', background: 'rgba(244,236,224,0.6)' }}>
          <div className="inst-ticker-track py-3">
            {[...JOBS, ...JOBS].map((j, i) => (
              <span key={i} className="inline-flex items-center gap-2 text-sm px-5" style={{ color: '#5a4a39' }}>
                <span style={{ color: '#e0a32e' }}>●</span>
                <span className="font-medium">{j.title}</span>
                <span style={{ color: '#8a7860' }}>· {j.company} · {j.salary}</span>
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════ REGISTRO PÚBLICO (stats) ═══════════════ */}
      <section className="max-w-6xl mx-auto px-5 py-16">
        <div className="flex items-center justify-between mb-6">
          <p className="inst-kicker">Registro público de intermediación laboral</p>
          <p className="text-xs hidden sm:block" style={{ color: '#8a7860', fontFamily: 'Geist Mono, monospace' }}>Actualizado · Junín 2026</p>
        </div>
        <div className="rule-2 mb-10" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {[
            { value: '2,400+', unit: 'trabajadores', sec: '§ 01' },
            { value: '340+',   unit: 'empresas',     sec: '§ 02' },
            { value: '180+',   unit: 'vacantes',     sec: '§ 03' },
            { value: '87%',    unit: 'colocación',   sec: '§ 04' },
          ].map(s => (
            <Reveal key={s.unit}>
              <div className="space-y-1">
                <p className="text-[11px] font-medium" style={{ color: '#8a7860', fontFamily: 'Geist Mono, monospace', letterSpacing: '0.1em' }}>{s.sec}</p>
                <p className="inst-serif-num" style={{ fontSize: 'clamp(44px,5vw,62px)', color: '#0f6e6e' }}>{s.value}</p>
                <p className="text-sm font-medium uppercase tracking-wider" style={{ color: '#6e5d49' }}>{s.unit}</p>
              </div>
            </Reveal>
          ))}
        </div>
        <div className="rule-2 mt-10" />
      </section>

      {/* ═══════════════ EMPLEOS ═══════════════ */}
      <section className="max-w-6xl mx-auto px-5 pb-20 space-y-7" id="empleos">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
          <div>
            <p className="inst-kicker">Vacantes verificadas</p>
            <h2 className="inst-display text-3xl md:text-4xl mt-2">
              Encuentra tu próxima <span className="inst-it">oportunidad</span>
            </h2>
          </div>
          <p className="text-sm" style={{ color: '#6e5d49', fontFamily: 'Geist Mono, monospace' }}>{filtered.length} resultados</p>
        </div>

        <div className="flex flex-wrap gap-2">
          {CATEGORIES.map(c => (
            <button key={c} onClick={() => setActiveFilter(c)}
              className={`inst-chip ${activeFilter === c ? 'active' : ''}`}>
              {c}
            </button>
          ))}
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((job, i) => (
            <Reveal key={job.id} delay={Math.min(i * 0.05, 0.25)}>
              <JobCard job={job} i={i} />
            </Reveal>
          ))}
        </div>

        <div className="text-center pt-4">
          <button onClick={openRegister} className="ibtn ibtn-outline">Ver todas las vacantes →</button>
        </div>
      </section>

      {/* ═══════════════ CÓMO FUNCIONA (oscuro) ═══════════════ */}
      <section className="inst-dark relative overflow-hidden py-24 px-5" id="como-funciona">
        <div className="absolute -right-20 -bottom-20 opacity-[0.09] pointer-events-none">
          <DrtpeSeal size={420} tone="light" />
        </div>
        <div className="max-w-6xl mx-auto relative z-10 space-y-14">
          <div className="space-y-3">
            <p className="inst-kicker" style={{ color: '#eab84e' }}>Proceso simple y sin fricción</p>
            <h2 className="inst-display text-4xl md:text-5xl" style={{ color: '#fff' }}>
              Cómo <span className="inst-it" style={{ color: '#eab84e' }}>funciona</span>
            </h2>
            <div className="rule-2-dark max-w-xs" />
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              { n: '01', title: 'Crea tu perfil', desc: 'Regístrate y responde 2 preguntas. El sistema detecta tu tipo de perfil y personaliza tu experiencia.' },
              { n: '02', title: 'Genera tu CV con IA', desc: 'El asistente extrae tus habilidades y arma un CV profesional listo para descargar.' },
              { n: '03', title: 'Conecta con empleadores', desc: 'El motor de ML cruza tu perfil con vacantes reales y te muestra las más compatibles.' },
            ].map((s, i) => (
              <Reveal key={s.n} delay={i * 0.08}>
                <div className="rounded-2xl p-7 h-full" style={{ background: 'rgba(255,255,255,0.045)', border: '1px solid rgba(255,255,255,0.10)' }}>
                  <p className="inst-serif-num" style={{ fontSize: 56, color: '#eab84e' }}>{s.n}</p>
                  <h3 className="font-semibold text-xl mt-4" style={{ color: '#fff' }}>{s.title}</h3>
                  <p className="text-sm mt-2.5 leading-relaxed" style={{ color: 'rgba(244,236,224,0.66)' }}>{s.desc}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════ EMPRESAS ═══════════════ */}
      <section className="py-20 px-5" id="empresas">
        <div className="max-w-6xl mx-auto space-y-8">
          <div className="text-center space-y-2">
            <p className="inst-kicker">Entidades y empresas registradas</p>
            <h2 className="inst-display text-2xl md:text-3xl">Confían en la bolsa de empleo de la DRTPE</h2>
          </div>
          <div className="grid grid-cols-3 md:grid-cols-6 gap-4">
            {COMPANIES.map((c, i) => <CompanyLogo key={c.name} c={c} i={i} />)}
          </div>
        </div>
      </section>

      {/* ═══════════════ TESTIMONIOS ═══════════════ */}
      <section className="max-w-6xl mx-auto px-5 py-16 space-y-10" style={{ background: 'transparent' }}>
        <div className="text-center space-y-2">
          <p className="inst-kicker">Historias de colocación</p>
          <h2 className="inst-display text-3xl md:text-4xl">
            Resultados <span className="inst-it">reales</span> en Junín
          </h2>
        </div>
        <div className="grid md:grid-cols-3 gap-5">
          {TESTIMONIALS.map((t, i) => {
            const accent = ACCENTS[i % ACCENTS.length]
            return (
              <Reveal key={t.name} delay={i * 0.08} className="h-full">
                <div className="icard p-6 space-y-5 h-full" style={{ borderTop: `3px solid ${accent}` }}>
                  <p className="inst-serif-num text-5xl leading-none" style={{ color: accent, opacity: 0.35 }}>“</p>
                  <p className="text-sm leading-relaxed" style={{ color: '#5a4a39' }}>{t.quote}</p>
                  <div className="flex items-center gap-3 pt-2">
                    <div className="w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0" style={{ background: accent }}>
                      {t.initial}
                    </div>
                    <div>
                      <p className="font-semibold text-sm" style={{ color: '#2a1d14' }}>{t.name}</p>
                      <p className="text-xs" style={{ color: '#6e5d49' }}>{t.role}</p>
                    </div>
                  </div>
                </div>
              </Reveal>
            )
          })}
        </div>
      </section>

      {/* ═══════════════ CTA FINAL ═══════════════ */}
      <section className="inst-dark relative overflow-hidden py-24 px-5">
        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 opacity-[0.07] pointer-events-none">
          <DrtpeSeal size={460} tone="light" />
        </div>
        <div className="max-w-3xl mx-auto relative z-10 text-center space-y-7">
          <h2 className="inst-display text-4xl md:text-6xl" style={{ color: '#fff', lineHeight: 1.02 }}>
            Empieza hoy. <span className="inst-it" style={{ color: '#eab84e' }}>Es gratis.</span>
          </h2>
          <p className="text-lg" style={{ color: 'rgba(244,236,224,0.72)' }}>
            Crea tu cuenta y accede a la bolsa de empleo formal de Junín en menos de 3 minutos.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <button onClick={openRegister} className="ibtn ibtn-gold text-base !px-8 !py-4">Crear cuenta gratis</button>
            <button onClick={() => setLoginOpen(true)} className="ibtn ibtn-on-dark text-base !px-8 !py-4">Ya tengo cuenta</button>
          </div>
        </div>
      </section>

      {/* ═══════════════ RESPALDADO POR ═══════════════ */}
      <section className="py-14 px-5" style={{ background: '#ffffff', borderTop: '1px solid rgba(42,29,20,0.07)' }}>
        <div className="max-w-5xl mx-auto flex flex-col items-center gap-8">
          <p className="inst-kicker text-center">Una iniciativa del Estado · Respaldado por</p>
          <div className="flex flex-wrap items-center justify-center gap-x-14 gap-y-8">
            <img src="/institucional/gobierno-regional-junin.png" alt="Gobierno Regional de Junín"
              className="h-16 md:h-[72px] w-auto object-contain"
              onError={(e) => { e.currentTarget.style.display = 'none' }} />
            <span className="hidden sm:block h-12 w-px" style={{ background: 'rgba(42,29,20,0.12)' }} />
            <img src="/institucional/drtpe.png" alt="DRTPE · Dirección Regional de Trabajo y Promoción del Empleo de Junín"
              className="h-16 md:h-[72px] w-auto object-contain"
              onError={(e) => { e.currentTarget.style.display = 'none' }} />
          </div>
        </div>
      </section>

      {/* ═══════════════ FOOTER ═══════════════ */}
      <footer style={{ background: '#2a1d14', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
        <div className="max-w-6xl mx-auto px-5 py-14 grid grid-cols-2 md:grid-cols-4 gap-8">
          <div className="col-span-2 md:col-span-1 space-y-4">
            <img src="/institucional/linku.png" alt="Linku · Empleo formal" className="rounded-xl"
              style={{ width: 58, height: 58, background: '#fff' }}
              onError={(e) => { e.currentTarget.style.display = 'none' }} />
            <p className="text-xs leading-relaxed" style={{ color: 'rgba(244,236,224,0.55)' }}>
              Bolsa de empleo formal respaldada por la Dirección Regional de Trabajo y Promoción del Empleo de Junín.
            </p>
          </div>
          {[
            { title: 'Trabajadores', links: ['Buscar empleo', 'Subir CV', 'Orientación laboral', 'Portafolio de oficio'] },
            { title: 'Empresas', links: ['Publicar vacante', 'Buscar candidatos', 'Planes', 'Verificación DRTPE'] },
            { title: 'Institucional', links: ['Acerca de', 'DRTPE-Junín', 'Privacidad', 'Términos'] },
          ].map(col => (
            <div key={col.title} className="space-y-3">
              <p className="text-xs uppercase tracking-widest" style={{ color: 'rgba(244,236,224,0.55)', fontFamily: 'Geist Mono, monospace' }}>{col.title}</p>
              <ul className="space-y-2">
                {col.links.map(l => (
                  <li key={l}>
                    <a href="#" className="text-sm transition-colors" style={{ color: 'rgba(244,236,224,0.7)' }}
                      onMouseEnter={e => (e.currentTarget.style.color = '#eab84e')}
                      onMouseLeave={e => (e.currentTarget.style.color = 'rgba(244,236,224,0.7)')}>
                      {l}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="border-t px-5 py-5 flex flex-col md:flex-row items-center justify-between gap-2 max-w-6xl mx-auto" style={{ borderColor: 'rgba(255,255,255,0.07)' }}>
          <p className="text-xs" style={{ color: 'rgba(244,236,224,0.5)' }}>© 2026 Linku · Gobierno Regional de Junín · DRTPE. Todos los derechos reservados.</p>
          <p className="text-xs" style={{ color: 'rgba(244,236,224,0.42)', fontFamily: 'Geist Mono, monospace' }}>Huancayo, Perú · Investigación aplicada</p>
        </div>
      </footer>
    </div>
  )
}
