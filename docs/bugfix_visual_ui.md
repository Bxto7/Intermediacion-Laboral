Eres el agente python-pro (o senior-frontend). Lee el CLAUDE.md antes de tocar cualquier archivo. Usa Bash para todo. Solo modifica los archivos indicados.

Tienes que corregir 4 problemas visuales concretos detectados en capturas de pantalla del sistema. Son correcciones de UI, no de lógica de negocio.

---

BUG 1 — El label "auth.register.fullName" aparece en crudo en el formulario de registro

Archivo: frontend/src/pages/RegisterPage.tsx

Causa: el código usa la clave `auth.register.fullName` pero en el archivo de traducciones `src/i18n/es-PE.json` la clave correcta es `auth.register.full_name`. Como la clave no existe, react-intl devuelve la clave literal en lugar del texto traducido.

Localiza esta línea en RegisterPage.tsx:
  {intl.formatMessage({ id: 'auth.register.fullName' })}

Reemplázala por:
  {intl.formatMessage({ id: 'auth.register.full_name' })}

Verifica también que no haya otras claves mal escritas en el mismo archivo comparándolas con las existentes en src/i18n/es-PE.json. Las claves correctas son:
  auth.register.title → "Crear cuenta"
  auth.register.full_name → "Nombre completo"
  auth.register.email → "Correo electrónico"
  auth.register.password → "Contraseña"
  auth.register.submit → "Crear cuenta"
  auth.register.error → debe existir o agregar "Error al crear la cuenta. Intenta de nuevo."
  common.loading → debe existir o agregar "Cargando..."

Si alguna clave falta en src/i18n/es-PE.json, agrégala al final del objeto JSON.

---

BUG 2 — El logo no se muestra: prop `variant` no existe en LinkuLogoFull ni LinkuLogoIcon

Archivos afectados (todos los que pasan variant= al logo):
  frontend/src/shared/NavBar.tsx
  frontend/src/onboarding/OnboardingPage.tsx
  frontend/src/pages/LoginPage.tsx
  frontend/src/pages/landing/LandingNav.tsx
  frontend/src/pages/landing/LoginModal.tsx
  frontend/src/pages/LandingPage.tsx
  frontend/src/pages/RegisterPage.tsx

Causa: LinkuLogoFull y LinkuLogoIcon no tienen la prop variant en su interfaz TypeScript, así que se ignora silenciosamente y el logo siempre renderiza con los colores por defecto (terracota sobre fondo crema), que no contrasta en fondos oscuros.

Solución: agrega la prop variant a los componentes del logo en frontend/src/shared/LinkuLogo.tsx.

Modifica LinkuLogoFull así:
```tsx
interface FullProps { size?: number; showSubtitle?: boolean; variant?: 'default' | 'white' | 'terracota' }

export const LinkuLogoFull: React.FC<FullProps> = ({ size = 34, showSubtitle = true, variant = 'default' }) => {
  const nameColor = variant === 'white' ? '#ffffff' : 'var(--ink-strong)'
  const subtitleColor = variant === 'white' ? 'rgba(255,255,255,0.55)' : 'var(--ink-muted)'
  const iconBg = variant === 'white'
    ? 'rgba(255,255,255,0.15)'
    : 'linear-gradient(135deg, #d97757, #c2562e)'
  const iconBorder = variant === 'white' ? '1px solid rgba(255,255,255,0.20)' : 'none'

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <span style={{
        width: size,
        height: size,
        borderRadius: size * 0.27,
        background: iconBg,
        border: iconBorder,
        display: 'grid',
        placeItems: 'center',
        flexShrink: 0,
        boxShadow: variant !== 'white' ? '0 4px 12px -4px rgba(194,86,46,0.5), inset 0 1px 0 rgba(255,255,255,0.2)' : 'none',
      }}>
        <LinkuMark size={Math.round(size * 0.53)} color="#fff" />
      </span>
      <div>
        <div style={{
          fontSize: size * 0.47,
          fontWeight: 600,
          letterSpacing: '-0.02em',
          color: nameColor,
          lineHeight: 1.2,
        }}>
          Linku
        </div>
        {showSubtitle && (
          <div style={{
            fontSize: 10.5,
            color: subtitleColor,
            fontFamily: 'Geist Mono, monospace',
            letterSpacing: '0.06em',
            textTransform: 'uppercase',
            lineHeight: 1.2,
          }}>
            DRTPE Junín · Empleo formal
          </div>
        )}
      </div>
    </div>
  )
}
```

Modifica también LinkuLogoIcon para aceptar variant:
```tsx
export const LinkuLogoIcon: React.FC<{ size?: number; variant?: 'default' | 'white' | 'terracota' }> = ({ size = 34, variant = 'default' }) => (
  <LinkuLogo size={size} />
)
```

Con este cambio:
- variant="white" → logo blanco para fondos oscuros (RegisterPage panel azul, LandingPage footer oscuro)
- variant="terracota" o "default" → logo terracota para fondos claros (NavBar, LoginPage, LandingNav)

---

BUG 3 — Las empresas en la landing son solo texto plano sin contraste visual

Archivo: frontend/src/pages/LandingPage.tsx

Situación actual: la sección "Empresas que confían en Linku" renderiza tarjetas con solo el nombre de la empresa en texto pequeño sobre fondo blanco. No hay imágenes de logos (ni deben haberlas — son empresas reales de Junín y no tenemos sus assets). El problema es que visualmente se ve vacío y sin contraste.

No uses imágenes externas. La solución correcta es darle más carácter visual a cada tarjeta con las iniciales de la empresa estilizadas y un color de acento.

Reemplaza la sección de COMPANIES en LandingPage.tsx. Localiza el bloque que mapea COMPANIES (el que tiene el grid de tarjetas con nombres de empresa) y reemplázalo por este enfoque con iniciales y colores:

```tsx
{/* ═══ LOGOS EMPRESAS ═══ */}
<section className="py-16 px-5 border-b" style={{ borderColor: 'rgba(61,40,24,0.08)' }} id="empleadores">
  <div className="max-w-6xl mx-auto space-y-8">
    <p className="text-center font-mono text-xs uppercase tracking-widest" style={{ color: '#8a6648' }}>
      Empresas que confían en Linku · DRTPE-Junín
    </p>
    <div className="grid grid-cols-3 md:grid-cols-6 gap-4">
      {[
        { name: 'Cementos Andinos', initials: 'CA', color: '#c2562e' },
        { name: 'Doe Run',          initials: 'DR', color: '#2d5a82' },
        { name: 'Hidrandina',       initials: 'HD', color: '#b8893a' },
        { name: 'Volcan Mining',    initials: 'VM', color: '#4d6a8a' },
        { name: 'Agroindustria',    initials: 'AJ', color: '#7a8c5c' },
        { name: 'Caja Huancayo',    initials: 'CH', color: '#b8893a' },
        { name: 'Constructora Wari',initials: 'CW', color: '#7a8c5c' },
        { name: 'Peruarbo',         initials: 'PA', color: '#c2562e' },
        { name: 'Electro Centro',   initials: 'EC', color: '#2d5a82' },
        { name: 'SEDAM Huancayo',   initials: 'SH', color: '#4d6a8a' },
        { name: 'Coop. Tocache',    initials: 'CT', color: '#7a8c5c' },
        { name: 'SEDAPAL Junín',    initials: 'SJ', color: '#b8893a' },
      ].map(c => (
        <div key={c.name}
          className="card-warm py-4 px-3 flex flex-col items-center justify-center gap-2 text-center hover:shadow-warm transition-all"
          style={{ minHeight: 80 }}>
          <div
            className="w-9 h-9 rounded-xl flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
            style={{ background: `linear-gradient(135deg, ${c.color}cc, ${c.color})` }}>
            {c.initials}
          </div>
          <span style={{ fontFamily: 'Instrument Serif, Georgia, serif', fontSize: '11px', color: '#6b4a35', fontWeight: 400, lineHeight: 1.3 }}>
            {c.name}
          </span>
        </div>
      ))}
    </div>
  </div>
</section>
```

---

BUG 4 — Bajo contraste en la sección CTA de la landing ("Empieza hoy. Es gratis.")

Archivo: frontend/src/pages/LandingPage.tsx

Situación: la sección final tiene fondo oscuro (#3d2818) y el botón "Ya tengo cuenta" es casi invisible porque usa `rgba(255,255,255,0.08)` como fondo y `rgba(255,255,255,0.15)` como borde, lo que no cumple el ratio mínimo de contraste WCAG AA.

Localiza el botón "Ya tengo cuenta" en la sección CTA final (el que llama a setLoginOpen). Reemplaza sus estilos:

De:
  style={{ background: 'rgba(255,255,255,0.08)', color: 'white', border: '1px solid rgba(255,255,255,0.15)' }}

A:
  style={{ background: 'rgba(255,255,255,0.12)', color: 'white', border: '1.5px solid rgba(255,255,255,0.35)' }}

También ajusta el hover del botón para que sea visible. Si el botón no tiene onMouseEnter/Leave, agrégalos:
  onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.20)'; e.currentTarget.style.borderColor = 'rgba(255,255,255,0.55)' }}
  onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.12)'; e.currentTarget.style.borderColor = 'rgba(255,255,255,0.35)' }}

---

VERIFICACIÓN FINAL

Ejecuta TypeScript para confirmar que no hay errores de tipos:
  npx tsc --noEmit 2>&1 | head -30

Luego verifica visualmente:
1. En /register → el label del campo nombre completo dice "Nombre completo", no "auth.register.fullName".
2. En /register panel azul oscuro → el logo Linku es blanco y visible.
3. En la landing, nav → el logo Linku terracota es visible sobre fondo crema.
4. En la landing, footer oscuro → el logo Linku es blanco.
5. La sección de empresas muestra tarjetas con iniciales coloreadas, no solo texto plano.
6. El botón "Ya tengo cuenta" en la sección CTA tiene borde visible sobre el fondo oscuro.
