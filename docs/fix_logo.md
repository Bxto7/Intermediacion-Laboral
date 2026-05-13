Lee el CLAUDE.md antes de tocar cualquier archivo. Usa Bash para todo.

Tienes que reemplazar el archivo frontend/src/shared/LinkuLogo.tsx con una implementación que use el logo real de Linku. El logo actual en el código es un SVG de trazo simple que no corresponde al logo real de la marca.

---

## EL LOGO REAL — descripción exacta

El logo de Linku tiene tres elementos:
1. Una L mayúscula terracota (#c2562e) con bordes muy redondeados — trazo grueso, extremo superior redondeado, gira 90° en la base
2. Un círculo marrón oscuro (#3d2818) pequeño, posicionado a la derecha a media altura de la L
3. Una forma orgánica de gota/blob marrón oscuro (#3d2818) grande, en la esquina inferior derecha, que se apoya en la base de la L

Los tres colores exactos del logo son:
- Terracota principal: #c2562e
- Marrón oscuro: #3d2818
- Blanco (fondo, para la variante sobre oscuro): #ffffff

---

## VARIANTES NECESARIAS

El logo necesita 4 variantes para no perderse en distintos fondos:

**Variante `default`** — sobre fondos claros (bg-base #f7f1e8, bg-elevated #ffffff, bg-soft #fdf6ea)
- L en terracota #c2562e
- Círculo y gota en marrón oscuro #3d2818
- Sin contenedor, el logo va directo sobre el fondo claro

**Variante `white`** — sobre fondos oscuros (dark #3d2818, auth panel azul #2d5a82, footer oscuro)
- L en blanco #ffffff
- Círculo y gota en blanco con opacity 0.65 para dar dimensión
- El contraste es blanco sobre oscuro

**Variante `mono-terra`** — sobre fondos de color medio (cards terracota, badges)
- L en blanco #ffffff
- Círculo y gota en rgba(255,255,255,0.5)

**Variante `contained`** — el logo dentro de un contenedor cuadrado redondeado terracota (para favicons, avatares, app icon)
- Contenedor: gradiente terracota linear-gradient(135deg, #d97757, #c2562e)
- L en blanco
- Círculo y gota en rgba(255,255,255,0.7)

---

## EL SVG DEL LOGO

El SVG del logo en su forma original (default) es este. Úsalo como base para las variantes cambiando solo los colores de fill:

```svg
<svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
  <!-- L terracota — trazo grueso redondeado -->
  <rect x="18" y="10" width="22" height="65" rx="11" fill="#c2562e"/>
  <rect x="18" y="55" width="52" height="22" rx="11" fill="#c2562e"/>
  
  <!-- Círculo marrón — a la derecha a media altura -->
  <circle cx="68" cy="36" r="10" fill="#3d2818"/>
  
  <!-- Gota/blob marrón — esquina inferior derecha -->
  <ellipse cx="62" cy="72" rx="18" ry="16" fill="#3d2818"/>
</svg>
```

Nota: este SVG es una aproximación geométrica del logo. Ajusta las proporciones si no coinciden exactamente con la imagen, pero mantén la estructura de 4 elementos: dos rect (la L), un circle y un ellipse.

---

## IMPLEMENTACIÓN COMPLETA

Reemplaza el contenido COMPLETO de frontend/src/shared/LinkuLogo.tsx con este código:

```tsx
// LinkuLogo — logo real de Linku con variantes de color
// Variante default: sobre fondos claros
// Variante white: sobre fondos oscuros (auth, footer, hero oscuro)
// Variante mono-terra: sobre fondos de color medio
// Variante contained: con contenedor terracota (favicon, avatar)

export type LogoVariant = 'default' | 'white' | 'mono-terra' | 'contained'

interface Colors {
  l: string
  dot: string
  blob: string
}

function getColors(variant: LogoVariant): Colors {
  switch (variant) {
    case 'white':
      return { l: '#ffffff', dot: 'rgba(255,255,255,0.65)', blob: 'rgba(255,255,255,0.55)' }
    case 'mono-terra':
      return { l: '#ffffff', dot: 'rgba(255,255,255,0.55)', blob: 'rgba(255,255,255,0.45)' }
    case 'contained':
      return { l: '#ffffff', dot: 'rgba(255,255,255,0.75)', blob: 'rgba(255,255,255,0.65)' }
    default:
      return { l: '#c2562e', dot: '#3d2818', blob: '#3d2818' }
  }
}

interface MarkProps {
  size?: number
  variant?: LogoVariant
}

// Solo el símbolo del logo (sin texto ni contenedor)
export const LinkuMark: React.FC<MarkProps> = ({ size = 32, variant = 'default' }) => {
  const c = getColors(variant)
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* L — trazo vertical */}
      <rect x="18" y="10" width="22" height="65" rx="11" fill={c.l} />
      {/* L — trazo horizontal */}
      <rect x="18" y="55" width="52" height="22" rx="11" fill={c.l} />
      {/* Círculo marrón — parte superior derecha */}
      <circle cx="68" cy="36" r="10" fill={c.dot} />
      {/* Gota/blob marrón — esquina inferior derecha */}
      <ellipse cx="62" cy="72" rx="18" ry="16" fill={c.blob} />
    </svg>
  )
}

interface LogoProps {
  size?: number
  variant?: LogoVariant
}

// Logo con contenedor cuadrado redondeado (modo "app icon")
export const LinkuLogo: React.FC<LogoProps> = ({ size = 36, variant = 'contained' }) => {
  const isContained = variant === 'contained' || variant === 'default'
  return (
    <span
      style={{
        width: size,
        height: size,
        borderRadius: size * 0.28,
        background: isContained
          ? 'linear-gradient(135deg, #d97757 0%, #c2562e 100%)'
          : 'transparent',
        border: variant === 'white' ? '1px solid rgba(255,255,255,0.18)' : 'none',
        display: 'grid',
        placeItems: 'center',
        flexShrink: 0,
        boxShadow: isContained
          ? '0 4px 14px -4px rgba(194,86,46,0.45), inset 0 1px 0 rgba(255,255,255,0.18)'
          : 'none',
        overflow: 'hidden',
      }}
    >
      <LinkuMark
        size={Math.round(size * 0.70)}
        variant={isContained ? 'contained' : variant}
      />
    </span>
  )
}

interface FullProps {
  size?: number
  variant?: LogoVariant
  showSubtitle?: boolean
}

// Wordmark completo: ícono + "Linku" + subtítulo DRTPE
export const LinkuLogoFull: React.FC<FullProps> = ({
  size = 36,
  variant = 'default',
  showSubtitle = true,
}) => {
  const nameColor = variant === 'white' || variant === 'mono-terra'
    ? '#ffffff'
    : 'var(--ink-strong)'
  const subtitleColor = variant === 'white' || variant === 'mono-terra'
    ? 'rgba(255,255,255,0.50)'
    : 'var(--ink-muted)'

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <LinkuLogo size={size} variant={variant} />
      <div>
        <div
          style={{
            fontSize: size * 0.47,
            fontWeight: 700,
            letterSpacing: '-0.025em',
            color: nameColor,
            lineHeight: 1.15,
          }}
        >
          Linku
        </div>
        {showSubtitle && (
          <div
            style={{
              fontSize: 10,
              color: subtitleColor,
              fontFamily: 'Geist Mono, monospace',
              letterSpacing: '0.055em',
              textTransform: 'uppercase',
              lineHeight: 1.2,
              marginTop: 1,
            }}
          >
            DRTPE Junín · Empleo formal
          </div>
        )}
      </div>
    </div>
  )
}

// Solo el ícono sin texto — alias conveniente
export const LinkuLogoIcon: React.FC<LogoProps> = ({ size = 36, variant = 'contained' }) => (
  <LinkuLogo size={size} variant={variant} />
)

// Alias para compatibilidad con código existente que usa LinkuLogoOnDark
export const LinkuLogoOnDark: React.FC<{ size?: number }> = ({ size = 36 }) => (
  <LinkuLogoFull size={size} variant="white" />
)
```

---

## ACTUALIZAR TODOS LOS USOS EN EL PROYECTO

Después de reemplazar el archivo, actualiza cada uso según el fondo donde aparece:

**frontend/src/shared/NavBar.tsx**
Fondo: claro (--bg-base)
```tsx
<LinkuLogoIcon size={30} variant="contained" />
// o el wordmark:
<LinkuLogoFull size={30} variant="default" />
```

**frontend/src/pages/landing/LandingNav.tsx**
Fondo: transparente sobre claro / blur crema
```tsx
<LinkuLogoFull size={34} variant="default" />
```

**frontend/src/pages/landing/LoginModal.tsx**
Panel izquierdo: fondo claro (crema)
```tsx
<LinkuLogoFull size={32} variant="default" />
```

**frontend/src/pages/LoginPage.tsx**
Panel: fondo claro
```tsx
<LinkuLogoFull size={36} variant="default" />
```

**frontend/src/pages/RegisterPage.tsx**
Panel derecho: fondo oscuro azul (--grad-auth)
```tsx
<LinkuLogoFull size={36} variant="white" />
```

**frontend/src/pages/LandingPage.tsx footer**
Fondo: oscuro marrón (#3d2818)
```tsx
<LinkuLogoFull size={30} variant="white" showSubtitle={true} />
```

**frontend/src/onboarding/OnboardingPage.tsx**
Fondo: claro
```tsx
<LinkuLogoFull size={40} variant="default" />
```

**frontend/src/admin/AdminLayout.tsx** (si existe un sidebar oscuro)
Fondo: oscuro
```tsx
<LinkuLogoFull size={32} variant="white" />
```

---

## VERIFICACIÓN

Ejecuta al terminar:
```bash
cd frontend && npx tsc --noEmit 2>&1 | head -20
```

Verifica visualmente que:
1. En la LandingNav (fondo crema) → el logo tiene la L terracota y las formas marrón oscuro visibles.
2. En el panel derecho del Register (fondo azul oscuro) → el logo es completamente blanco con las formas en blanco semitransparente.
3. En el footer de la landing (fondo marrón oscuro) → el logo es blanco y legible.
4. El ícono contenido (contenedor terracota) se ve en el NavBar autenticado.
5. En ningún fondo el logo se pierde o tiene bajo contraste.

Además copia el archivo logo_linku.png a frontend/public/ 
y úsalo como favicon en index.html reemplazando el favicon actual.
En los lugares donde se usa el logo como imagen estática 
(og:image del meta, apple-touch-icon) usa /logo_linku.png.
En el código React sigue usando el componente SVG LinkuLogoFull.