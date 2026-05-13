# LINKU — Rediseño completo de la aplicación

Sistema de intermediación laboral DRTPE Junín. Migra TODA la app al app-shell unificado descrito abajo. Stack libre (Next.js + Tailwind recomendado).

---

## 1. LOGO — Linku brand mark

El logo es una **"L" estilizada con un punto de "link"** al final del trazo horizontal — representa "linku" = link + you (conectar gente con empleo). Va dentro de un cuadrado terracota con esquinas redondeadas.

### SVG del mark (úsalo tal cual)
```jsx
function LinkuMark({ size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
      <path d="M8 5 L8 16 Q8 19 11 19 L17 19"
            stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" fill="none"/>
      <circle cx="17" cy="19" r="1.7" fill="currentColor"/>
    </svg>
  );
}
```

### Container del logo (terracota gradient)
```jsx
function LinkuLogo({ size = 34 }) {
  return (
    <span style={{
      width: size, height: size, borderRadius: size * 0.27,
      background: 'linear-gradient(135deg, #d97757, #c2562e)',
      display: 'grid', placeItems: 'center', color: '#fff',
      boxShadow: '0 4px 12px -4px rgba(194,86,46,0.5), inset 0 1px 0 rgba(255,255,255,0.2)',
    }}>
      <LinkuMark size={size * 0.53} />
    </span>
  );
}
```

### Wordmark completo (sidenav y nav)
```jsx
<div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
  <LinkuLogo size={34} />
  <div>
    <div style={{ fontSize: 16, fontWeight: 600, letterSpacing: '-0.02em' }}>Linku</div>
    <div style={{ fontSize: 10.5, color: 'var(--ink-muted)' }}>DRTPE Junín · Empleo formal</div>
  </div>
</div>
```

### Variantes
- **Sidenav / nav:** 34px cuadrado con wordmark + subtítulo "DRTPE Junín · Empleo formal"
- **Favicon:** solo el mark 32×32
- **Sobre fondo oscuro:** el mark se mantiene blanco (`color: white`), el container puede ser transparente con borde sutil
- **Loading state:** rota el path del mark 360° en 1.4s

### ❌ NO hacer
- No usar negro o gris en el mark
- No estirar/deformar el cuadrado
- No quitar el dot del final (define la marca)
- No usar el wordmark "Linku" en Inter o Roboto — solo Geist

---

## 2. SISTEMA VISUAL — tokens

```css
:root {
  /* Fondos */
  --bg-base: #f7f1e8;       /* app background */
  --bg-elevated: #ffffff;   /* cards */
  --bg-soft: #fdf6ea;       /* sidenav, inputs alternativos */
  --bg-warm: #ebe0cd;       /* secciones secundarias */

  /* Tinta */
  --ink-strong: #3d2818;
  --ink: #5a3d2b;
  --ink-warm: #6b4a35;
  --ink-muted: #8a6648;

  /* Oscuros (marrón medio, NO negro) */
  --dark: #4a3120;
  --dark-2: #5a3d2b;
  --dark-deep: #3d2818;
  --on-dark: #fdf6ea;

  /* Acento principal */
  --terra-500: #c2562e;
  --terra-400: #d97757;
  --terra-700: #8a3a1c;
  --terra-100: rgba(194,86,46,0.10);

  /* Acentos secundarios — rotar por módulo */
  --blue: #2d5a82;          --blue-100: rgba(45,90,130,0.10);
  --olive: #7a8c5c;         --olive-deep: #5d6b46;  --olive-100: rgba(122,140,92,0.14);
  --gold: #b8893a;          --gold-light: #e8b45a;  --gold-100: rgba(184,137,58,0.14);
  --coral: #e8a691;         /* italics sobre oscuro */

  /* Líneas */
  --line: rgba(61,40,24,0.10);
  --line-strong: rgba(61,40,24,0.18);

  /* Radios */
  --r-sm: 8px; --r-md: 12px; --r-lg: 18px; --r-xl: 22px; --r-2xl: 28px;

  /* Sombras cálidas */
  --shadow-sm: 0 1px 0 rgba(61,40,24,0.04);
  --shadow-md: 0 1px 0 rgba(61,40,24,0.04), 0 8px 24px -16px rgba(61,40,24,0.12);
  --shadow-lg: 0 8px 32px -12px rgba(61,40,24,0.18);
}
```

### Asignación cromática por módulo
- **Empleos / acción principal** → terracota
- **Postulaciones / DRTPE / info** → azul
- **Progreso / éxito / verificado** → oliva
- **Rating / actividad / premium** → mostaza

---

## 3. TIPOGRAFÍA

```html
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700;800&family=Instrument+Serif:ital@0;1&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet" />
```

| Fuente | Uso |
|---|---|
| **Geist** | Body, UI, todo |
| **Instrument Serif italic** | Acentos en titulares ("te espera", "encajas", "primer paso") + números grandes |
| **Geist Mono** | Kickers/labels uppercase con `letter-spacing: 0.12em` |

**Patrón obligatorio en cada heading:**
```jsx
<h1>Hola María, <span className="serif-it" style={{ color: 'var(--coral)' }}>4 nuevos matches</span></h1>
<h2>Trabajos donde <span className="it">encajas</span></h2>
```
Donde `.serif-it` = `font-family: 'Instrument Serif'; font-style: italic; font-weight: 400;`

**Escala:**
- h1 page hero: 32px / 600 / -0.03em
- h2 section: 22px / 600 / -0.025em
- h3 card: 17px / 600 / -0.02em
- Body: 14.5px / 400 / -0.005em
- Stats serif: 30-56px Instrument Serif normal

---

## 4. APP-SHELL — arquitectura

```
┌──────────────────────────────────────────────────────┐
│  TOPBAR (60px)                                       │
│  [logo] [search global ⌘K]      [DRTPE] [🔔] [user] │
├────────────┬─────────────────────────────────────────┤
│            │                                         │
│  SIDENAV   │   MAIN CONTENT AREA                     │
│  240px     │   (max-width 1280px, padding 24px 32px) │
│            │                                         │
│  [brand]   │                                         │
│  PRINCIPAL │                                         │
│  · Inicio  │                                         │
│  · etc     │                                         │
│  CUENTA    │                                         │
│  · etc     │                                         │
│  [perfil   │                                         │
│   completi-│                                         │
│   tud card]│                                         │
└────────────┴─────────────────────────────────────────┘
```

### Topbar
- Sticky, `backdrop-filter: blur(12px)`, fondo `rgba(247,241,232,0.85)`
- Search global pill con `kbd ⌘K` visible
- Badge DRTPE azul (no terracota) con ícono ShieldCheck
- Bell con contador rojo (terracota)
- User chip: avatar + nombre + role + chevron

### Sidenav
- Fondo `var(--bg-soft)`, border-right `var(--line)`
- Brand row arriba con `LinkuLogo` + nombre + subtítulo
- Items: `padding 8px 10px`, `border-radius: 10px`, ícono Lucide 16px
- Item **activo**: card blanca con border + sombra suave + ícono en terracota + contador en pill terracota
- Item con contador: pill `nav-count` a la derecha (12, 3, 8…)
- **Bottom card** sticky: fondo `var(--dark)` con glow terracota, muestra "Estás casi *listo* · 72%" + progress bar + CTA "Completar perfil →" — siempre presente como nudge a completar
- Mobile: colapsa a **bottom-nav** de 5 items con badges

### Items por rol de usuario
**Worker Oficio:**
- PRINCIPAL: Inicio · Mi portfolio · Marketplace · Empleos para mí · Postulaciones
- CUENTA: Mi progreso · Configuración

**Worker Primer Empleo:**
- PRINCIPAL: Inicio · Completar perfil · Empleos para mí · Postulaciones · Orientación

**Worker Experiencia:**
- PRINCIPAL: Inicio · Bolsa de empleos · Postulaciones · Alertas · Mi progreso

**Employer:**
- PRINCIPAL: Dashboard · Publicar empleo · Candidatos · Mensajes

**Admin:**
- ADMIN: KPIs · Trabajadores · Empleadores · Ofertas

---

## 5. COMPONENTES BASE

### Botones (siempre pill)
```css
.btn-primary {
  background: linear-gradient(180deg, var(--terra-400), var(--terra-500));
  color: #fff;
  padding: 9px 16px;
  border-radius: 999px;
  box-shadow: 0 1px 0 rgba(255,255,255,0.18) inset, 0 6px 16px -8px rgba(194,86,46,0.5);
}
.btn-outline { border: 1px solid var(--line-strong); background: transparent; }
.btn-ghost { color: var(--ink-warm); background: transparent; }
.btn-sm { padding: 6px 12px; font-size: 12px; }
```

### Cards
```css
.card { background: #fff; border: 1px solid var(--line); border-radius: 18px; padding: 22px; }
.card-soft { background: var(--bg-soft); /* idem */ }
.card-dark {
  background:
    radial-gradient(500px 300px at 15% 0%, rgba(217,119,87,0.28), transparent 60%),
    radial-gradient(400px 300px at 95% 100%, rgba(122,140,92,0.18), transparent 65%),
    linear-gradient(140deg, var(--dark), var(--dark-2));
  color: var(--on-dark);
  border-radius: 22px;
}
```

### Tags / chips (4 variantes de color)
```css
.tag { padding: 3px 9px; border-radius: 999px; font-size: 11.5px; }
.tag-terra { background: var(--terra-100); color: var(--terra-500); }
.tag-blue  { background: var(--blue-100);  color: var(--blue); }
.tag-olive { background: var(--olive-100); color: var(--olive-deep); }
.tag-gold  { background: var(--gold-100);  color: #8a6620; }
```

### Match bar (compatibilidad)
- Track `rgba(61,40,24,0.08)` height 6px pill
- Fill color según %:
  - ≥85% → `var(--olive)`
  - 70-84% → `var(--gold)`
  - <70% → `var(--terra-500)`
- Texto del % al lado en peso 600 con el mismo color

### Avatares sin foto
```jsx
<span className="avatar" /* placeholder con iniciales */>
  {/* fondo: rgba(61,40,24,0.08), border: 1px var(--line), texto var(--ink-warm) */}
</span>
```
Para placeholders SIN nombre todavía: ícono `<I.User>` en mismo container, NUNCA colores aleatorios estilo Gravatar.

### Avatares de empresa (en match cards)
4 variantes:
```jsx
.avatar-photo { background: linear-gradient(135deg, var(--terra-400), var(--terra-500)); color: #fff; }
.avatar-blue  { background: linear-gradient(135deg, var(--blue), #1a3a52);  color: #fff; }
.avatar-olive { background: linear-gradient(135deg, var(--olive), var(--olive-deep)); color: #fff; }
.avatar-gold  { background: linear-gradient(135deg, var(--gold-light), var(--gold)); color: #fff; }
```

### DRTPE verified pill
```jsx
<span className="verified">
  <ShieldCheckIcon /> verificado
</span>
```
Siempre azul (`var(--blue)`), siempre presente en empleos, empresas y trabajadores.

### Iconografía
**Librería:** `lucide-react` (line-style, stroke-width 1.7). NO usar Material, FontAwesome, Heroicons solid, emojis decorativos en UI.

Iconos clave: Home, Briefcase, Folder, Store, FileText, BarChart, Settings, Bell, Search, MapPin, Star, Plus, Check, ArrowRight, Sparkles, Bookmark, ShieldCheck, Image, Edit, Trash, Send, Clock, TrendingUp, Eye, Filter, Wrench.

---

## 6. LAS VISTAS DEL APP-SHELL

### A. Inicio (Worker Oficio)
**Welcome dark card:**
- Avatar 56px + saludo grande con día actual ("Bienvenida, lunes 12 de mayo")
- H1: "Hola [Nombre], *tienes 4 nuevos matches*" (italic serif en parte motivadora)
- 4 stats serif inline: Rating ★ · Trabajos · Visibilidad · Postulaciones (separados por divider vertical)

**Grid 1.7fr / 1fr:**
- **Izq (2/3):**
  - "Empleos compatibles · 12 nuevos" → grid 2×2 de MatchCards compactos
  - "Postulaciones recientes" → card con 3 items en timeline (dot de color por status + título + empresa + salario + tag de estado)
- **Der (1/3):**
  - Portfolio status card (gradient crema con glow terracota): "8 trabajos · linku.pe/p/maria-rojas", 4 thumbnails mini, botón "+ Agregar trabajo"
  - Progreso (checklist visual): 5 items, los completados con check oliva + texto tachado, pendientes con círculo dashed
  - Notificaciones: 3 items recientes con ícono coloreado por tipo

### B. Mi Portfolio
- Header compacto sin hero repetido: kicker + h1 "Mi *portfolio*" + meta inline (rating, años, distrito, DRTPE verificado)
- Botones top-right: Vista pública · Generar CV · **+ Agregar trabajo**
- Stats row: 4 MiniStats (Trabajos / Calificación / Habilidades / Vistas) cada uno con ícono en color distinto
- Grid 1fr / 380px:
  - **Izq:** grid 2-col de WorkCards (thumbnail gradient + título + descripción truncada + skill tags + rating + edit/delete inline)
  - **Der:** **slide-over panel sticky** "Agregar trabajo" — siempre visible, no modal:
    - Campo título, textarea descripción
    - Dropzone 3 fotos
    - Tag input con "La IA extraerá habilidades automáticamente" en banner azul
    - Cancelar / Publicar trabajo

### C. Marketplace
- Header con CTA "+ Publicar servicio"
- **Tabs inline:** Mis servicios (2) / Explorar servicios (184)
- Search pill amplio + dropdowns Distrito / Disponibilidad / Más filtros
- Scroll horizontal de categorías chips (Todos · Electricidad · Gasfitería · …) con activo en `var(--ink-strong)` color claro
- Banner DRTPE azul de verificación
- Grid 3-col de ListingCards: ícono categoría + título + tags + autor con rating + precio + Contactar

### D. Empleos para mí
- Header h1 "Empleos donde *encajas*"
- Layout 260px / 1fr:
  - **Sidebar filtros sticky:** Distrito, Modalidad, Salario (checkboxes con count), Compatibilidad mínima (segmented 60/70/80/90%) + tip de IA oliva
  - **Lista:** 6 MatchCards completos apilados verticalmente
- Tag oliva en skills coincidentes ("✓ Tableros eléctricos"), tag gris en faltantes ("+2 faltan")

### E. Mobile
- Topbar compacto: logo + nombre + bell + avatar
- Bottom-nav 5 items: Inicio · Portfolio · Marketplace · Empleos · Postul.
- Welcome dark card, match cards compactos, portfolio mini con thumbnails

---

## 7. FLUJOS PÚBLICOS

### Landing pública (`/`)
Hero split:
- **Izq:** kicker "Plataforma oficial · DRTPE Junín" + H1 masivo "Tu próximo empleo *te espera*" + lede + búsqueda
- **Der:** grid vivo de 4-6 ofertas/servicios recientes
- 3 caminos como cards: "Busco mi primer empleo" · "Tengo experiencia" · "Ofrezco un servicio"
- Stats institucional · empresas verificadas · testimonios · CTA final dark · footer dark

### Login (`/login`) y Registro (`/register`)
Split 50/50:
- **Panel izq CLARO:** gradient `#fdf6ea → #f0e0c4` con 4 glows radiales sutiles (mostaza/azul/terracota/oliva) — texto en `var(--ink-strong)` totalmente legible. NUNCA usar fondo oscuro aquí.
- **Panel der:** form blanco con inputs `border-radius: 12px`, border `#d6c5a8`, focus terracota
- Login con email + password + Google + Facebook
- Registro con DNI 8 dígitos + nombre + rol toggle (Trabajador/Empleador)

### Onboarding (`/onboarding`)
Conversacional, 2 pasos en misma página:
- "¿Es tu primer trabajo?" → bifurca
- "¿Trabajas en un oficio?" → grid 13 categorías con ícono Lucide (no emojis)
- Al terminar: redirige a `/app` con sidenav adecuado al tipo

### Wizard primer empleo (inline en `/app`, NO ruta separada)
- Aparece como primer panel activo del sidenav cuando el perfil está incompleto
- Layout 3/5 form izq + 2/5 CV live preview der (sticky)
- 6 pasos navegables: Datos · Educación · Habilidades (IA) · Actividades · Intereses · Vista previa
- Barra progreso superior

---

## 8. MICROCOPIA — tono Linku

- Tuteo: "Tu próximo empleo *te espera*", "Hola María"
- Léxico peruano: "Oficio" (no "habilidades técnicas"), "Trabajos realizados" (no "experiencia laboral"), "Postularme" (no "aplicar")
- Italic serif para énfasis emocional, no para datos
- Sin signos `¡!` excesivos — máximo 1 por pantalla
- Empty states motivadores: "Aún no tienes postulaciones. *Empieza acá* →"

---

## 9. ❌ REGLAS DE NO

- ❌ NO Inter, Roboto, Arial, system-ui — solo Geist
- ❌ NO morado, índigo, azul brillante, gradient `from-purple-* to-indigo-*`
- ❌ NO negro `#000` ni gris azulado — solo marrón cálido `#3d2818`
- ❌ NO `rounded-md` (4-6px) — mínimo 12px, ideal 18-22px
- ❌ NO `shadow-xl` / `shadow-2xl` agresivos — sombras cálidas sutiles
- ❌ NO emojis decorativos en UI (chips, badges, headings)
- ❌ NO avatares de color aleatorio para usuarios sin foto — usar placeholder neutro con ícono User
- ❌ NO hero repetido en cada sub-vista del shell — solo en Inicio
- ❌ NO modales para formularios que pueden ser slide-over (Agregar trabajo, Publicar servicio)
- ❌ NO "Ver todos →" si caben más items en pantalla — preferir infinite scroll o paginación inline

---

## 10. PLAN DE MIGRACIÓN

1. **Setup fuentes + tokens** en `globals.css` y `tailwind.config.ts`
2. **Componente `LinkuLogo` + `LinkuMark`** (sección 1) — reemplazar logo actual en TODA la app
3. **Componentes base** `Button`, `Card`, `Tag`, `Avatar`, `KickerLabel`, `SerifAccent` siguiendo §5
4. **AppShell** layout con TopBar + SideNav + main area (§4) — convertir el layout actual del dashboard a este shell
5. **Router**: las rutas `/dashboard`, `/matches`, `/applications`, `/portfolio`, `/marketplace` se convierten en **vistas internas** del shell, cambiando solo el contenido del `<main>` — la URL puede mantenerse para deep-link pero la página no se recarga
6. **Vistas** en orden: Inicio Oficio → Portfolio → Marketplace → Empleos → Postulaciones → Inicio Experiencia → Inicio Primer Empleo → Employer Dashboard → Admin
7. **Mobile**: AppShell responde con sidenav → bottom-nav en breakpoint `<768px`
8. **Auditar** cada vista con checklist:
   - [ ] Geist + Instrument Serif italic en heading
   - [ ] Sin morado/índigo
   - [ ] Cards radius ≥18px
   - [ ] Botones pill
   - [ ] DRTPE badge donde aplique
   - [ ] Tag verified en empresas/trabajadores
   - [ ] Empty states con CTA + italic serif

---

Aplica este sistema completo. Cualquier nueva pantalla, email, vista de admin o feature futura debe seguirlo sin excepción. La identidad de Linku es la paleta cálida terracota + el wordmark con el dot de "link" + el italic serif para humanizar — son los 3 elementos que NO pueden variar.