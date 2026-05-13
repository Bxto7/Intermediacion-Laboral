Eres el agente python-pro (o senior-frontend si está disponible). Lee el archivo CLAUDE.md en la raíz antes de tocar cualquier archivo. Usa la herramienta Bash para todo. Solo modifica los archivos que se indican explícitamente.

---

Tienes que corregir 7 bugs concretos en el frontend. Están distribuidos en 6 archivos existentes. No crear archivos nuevos.

---

BUG 1 — La ruta raíz "/" lleva al dashboard en lugar de la landing
Archivo: frontend/src/App.tsx

La LandingPage existe completa en pages/LandingPage.tsx pero nunca se muestra porque la ruta raíz redirige al dashboard. Cualquier visitante sin sesión aterriza en /login sin ver la plataforma.

Cambio 1: agrega el import lazy de LandingPage junto a los demás imports lazy al inicio del archivo:
  const LandingPage = lazy(() => import('./pages/LandingPage').then(m => ({ default: m.LandingPage })))

Cambio 2: localiza esta línea cerca del final del archivo:
  <Route path="/" element={<Navigate to="/dashboard" replace />} />

Reemplázala por:
  <Route path="/" element={<Suspense fallback={<PageFallback />}><LandingPage /></Suspense>} />

Cambio 3: el fallback de ruta no encontrada cámbialo a:
  <Route path="*" element={<Navigate to="/" replace />} />

---

BUG 2 — El marketplace interno /marketplace está bloqueado solo para OFICIO
Archivo: frontend/src/App.tsx

La ruta /marketplace tiene WorkerTypeGuard con allowedTypes=['oficio']. Cualquier usuario PRIMER_EMPLEO o EXPERIENCIA que intenta entrar es redirigido al dashboard. El marketplace de búsqueda debe ser visible para todos los autenticados.

Localiza este bloque exacto:
  <Route path="/marketplace/*" element={
    <WorkerTypeGuard allowedTypes={['oficio']}>
      <Suspense fallback={<PageFallback />}><MarketplacePage /></Suspense>
    </WorkerTypeGuard>
  } />

Reemplázalo por (solo requiere estar autenticado, que ya lo garantiza el AuthGuard del padre):
  <Route path="/marketplace/*" element={
    <Suspense fallback={<PageFallback />}><MarketplacePage /></Suspense>
  } />

---

BUG 3 — El botón "Publicar servicio" en MarketplacePage aparece para todos
Archivo: frontend/src/modules/oficio/marketplace/MarketplacePage.tsx

Al quitar el guard de la ruta, cualquier usuario autenticado puede llegar a /marketplace. Pero el botón "Publicar servicio" del hero y el tab "mis-servicios" deben seguir siendo exclusivos de OFICIO.

El componente ya importa useWorkerContext. La variable worker ya está disponible. Aplica estos cambios:

Cambio 1 — Condiciona el botón "Publicar servicio" del hero. Localiza:
  <button
    onClick={() => { setEditTarget(null); setShowModal(true) }}
    className="flex items-center gap-2 font-medium text-sm px-5 py-2.5 rounded-full transition-colors"
    style={{ background: 'var(--on-dark)', color: 'var(--dark-deep)' }}
  >
    <Plus size={15} />
    Publicar servicio
  </button>

Reemplázalo por:
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

Cambio 2 — Condiciona el tab "mis-servicios". Localiza el array que define los tabs. Será algo como:
  (['mis-servicios', 'buscar'] as const).map(t => ...)

Reemplaza el array por una expresión condicional:
  (worker?.worker_type === 'oficio'
    ? ['mis-servicios', 'buscar'] as const
    : ['buscar'] as const
  ).map(t => ...)

Y cambia el estado inicial del tab de 'mis-servicios' a 'buscar' cuando el tipo no es oficio. Localiza:
  const [tab, setTab] = useState<'mis-servicios' | 'buscar'>('mis-servicios')

Reemplázalo por:
  const { worker } = useWorkerContext()
  const defaultTab = worker?.worker_type === 'oficio' ? 'mis-servicios' : 'buscar'
  const [tab, setTab] = useState<'mis-servicios' | 'buscar'>(defaultTab)

Nota: useWorkerContext ya está importado en ese archivo, no lo importes dos veces.

Cambio 3 — El panel de "mis servicios" solo se renderiza para OFICIO. Busca el bloque que renderiza el listado de mis-servicios (el que tiene las cards con botones de editar/eliminar). Envuélvelo en:
  {worker?.worker_type === 'oficio' && tab === 'mis-servicios' && (
    // contenido existente
  )}

---

BUG 4 — ContactModal abre sin verificar autenticación y muestra error 401 crudo
Archivo: frontend/src/shared/ContactModal.tsx

El modal se abre y llama al API directamente. Sin token el backend devuelve 401 y el usuario ve "No se pudo enviar el mensaje" en lugar de un prompt de login.

Agrega al inicio de los imports:
  import { Link } from 'react-router-dom'

Dentro del componente, antes del return, agrega:
  const isAuthenticated = !!localStorage.getItem('access_token')

En el JSX, envuelve el contenido actual con una condición. El modal tiene tres estados posibles: no autenticado, enviado, y formulario. Reemplaza la estructura actual por:

  {!isAuthenticated ? (
    <div className="px-6 py-8 text-center space-y-5">
      <div
        className="w-14 h-14 rounded-full mx-auto flex items-center justify-center"
        style={{ background: 'var(--terra-100)' }}
      >
        <Shield size={24} style={{ color: 'var(--terra-500)' }} />
      </div>
      <div>
        <h3 className="font-bold text-base" style={{ color: 'var(--ink-strong)' }}>
          Inicia sesión para contactar
        </h3>
        <p className="text-sm mt-1.5 leading-relaxed" style={{ color: 'var(--ink-muted)' }}>
          Para enviar un mensaje a <strong>{workerName}</strong> necesitas tener
          una cuenta en Linku. Es gratis y toma menos de 2 minutos.
        </p>
      </div>
      <div className="flex flex-col gap-2.5 pt-1">
        <Link
          to="/login"
          className="btn-primary w-full py-3 text-center block"
          onClick={onClose}
        >
          Iniciar sesión
        </Link>
        <Link
          to="/register"
          className="btn-secondary w-full py-3 text-center block"
          onClick={onClose}
        >
          Registrarse gratis
        </Link>
      </div>
      <button onClick={onClose} className="text-xs" style={{ color: 'var(--ink-muted)' }}>
        Cancelar
      </button>
    </div>
  ) : sent ? (
    // bloque existente de "mensaje enviado" — no cambiar nada
  ) : (
    // formulario existente — no cambiar nada
  )}

---

BUG 5 — En PublicPortfolioPage y ServiceSearchPage el CTA sin auth manda a /register en lugar de /login
Archivos: frontend/src/pages/PublicPortfolioPage.tsx y frontend/src/pages/ServiceSearchPage.tsx

Actualmente ambas páginas tienen un botón/link "Regístrate para contactar" que va a /register. Es más probable que el visitante ya tenga cuenta. El texto y destino deben cambiar a login, guardando la URL actual para volver después.

En PublicPortfolioPage.tsx, localiza:
  <a href="/register" className="btn-primary inline-flex items-center gap-2 px-8 py-3.5 text-sm">
    <MessageCircle size={16} />
    Regístrate para contactar
  </a>

Reemplázalo por:
  <button
    onClick={() => {
      sessionStorage.setItem('login_return_url', window.location.pathname)
      window.location.href = '/login'
    }}
    className="btn-primary inline-flex items-center gap-2 px-8 py-3.5 text-sm"
  >
    <MessageCircle size={16} />
    Inicia sesión para contactar
  </button>

En ServiceSearchPage.tsx, dentro de ListingCard, localiza:
  <a
    href="/register"
    className="btn-primary flex-1 py-2 text-xs text-center"
  >
    Regístrate para contactar
  </a>

Reemplázalo por:
  <button
    onClick={() => {
      sessionStorage.setItem('login_return_url', window.location.pathname + window.location.search)
      window.location.href = '/login'
    }}
    className="btn-primary flex-1 py-2 text-xs"
  >
    Inicia sesión para contactar
  </button>

---

BUG 6 — LoginModal siempre redirige a /dashboard perdiendo el contexto de navegación
Archivo: frontend/src/pages/landing/LoginModal.tsx

Después de login siempre hace navigate('/dashboard') sin importar de dónde vino el usuario. Si vino desde /servicios o /p/{username}, debe volver ahí.

Localiza la función handleSubmit. Actualmente tiene:
  navigate('/dashboard')

Reemplaza esa línea por:
  const returnUrl = sessionStorage.getItem('login_return_url') || '/dashboard'
  sessionStorage.removeItem('login_return_url')
  navigate(returnUrl)

Además, cuando el usuario abre el LoginModal desde la LandingPage (botón "Iniciar sesión" del nav), guarda la URL actual. En LandingPage.tsx, localiza el botón que llama a setLoginOpen(true) en la LandingNav (el onLoginClick). Justo antes de abrirlo, guarda el return_url. Localiza en LandingPage.tsx la función o el punto donde se pasa onLoginClick al LandingNav y agrega:

  const handleLoginClick = () => {
    if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
      sessionStorage.setItem('login_return_url', window.location.pathname + window.location.search)
    }
    setLoginOpen(true)
  }

Luego pasa handleLoginClick en lugar del lambda directo:
  <LandingNav onLoginClick={handleLoginClick} scrolled={scrolled} />

---

BUG 7 — El NavBar autenticado muestra "Marketplace" solo a OFICIO
Archivo: frontend/src/shared/NavBar.tsx

El link a /marketplace está dentro del bloque {workerType === 'oficio' && ...} por lo que PRIMER_EMPLEO y EXPERIENCIA no lo ven. Todos los usuarios autenticados deben poder acceder al marketplace para buscar servicios.

Localiza este bloque:
  {workerType === 'oficio' && (
    <>
      <Link to="/oficio/portfolio" className="btn-ghost text-xs px-3 py-2" style={{ color: 'var(--ink-warm)' }}>
        Portfolio
      </Link>
      <Link to="/marketplace" className="btn-ghost text-xs px-3 py-2" style={{ color: 'var(--ink-warm)' }}>
        Marketplace
      </Link>
    </>
  )}

Reemplázalo por:
  {workerType === 'oficio' && (
    <Link to="/oficio/portfolio" className="btn-ghost text-xs px-3 py-2" style={{ color: 'var(--ink-warm)' }}>
      Portfolio
    </Link>
  )}
  {workerType && (
    <Link to="/marketplace" className="btn-ghost text-xs px-3 py-2" style={{ color: 'var(--ink-warm)' }}>
      Buscar servicios
    </Link>
  )}

---

VERIFICACIÓN FINAL

Ejecuta TypeScript para verificar que no hay errores de tipos:
  npx tsc --noEmit 2>&1 | head -40

Luego verifica manualmente estos 7 flujos y muéstrame el resultado de cada uno:

1. http://localhost:5173/ sin sesión → debe mostrar LandingPage, NO redirigir al login.
2. Clic en "Buscar servicios" del nav de la landing → va a /servicios sin pedir login.
3. En /servicios, clic en "Contactar" en cualquier card → abre ContactModal con panel "Inicia sesión para contactar" (no el formulario).
4. En ContactModal sin sesión, clic en "Iniciar sesión" → va a /login y cierra el modal.
5. Después de login, navigate va a la URL guardada en sessionStorage (no a /dashboard).
6. Usuario EXPERIENCIA autenticado → NavBar muestra "Buscar servicios" y entra a /marketplace sin ser redirigido.
7. En /marketplace como EXPERIENCIA → ve el feed de búsqueda, NO ve el botón "Publicar servicio" ni el tab "mis-servicios".
8. En /marketplace como OFICIO → ve el feed Y el botón "Publicar servicio" Y el tab "mis-servicios".
