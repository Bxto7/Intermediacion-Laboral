# DESIGN SYSTEM — Linku / DRTPE Junín

Sistema visual unificado para TODA la aplicación: landing pública, dashboard, formularios, vistas de admin, emails y cualquier pantalla nueva. Cuando crees o modifiques cualquier UI en este proyecto, sigue este documento.

---

## 1. PRINCIPIOS

1. **Cálido institucional** — paleta crema + terracota inspirada en la tierra de Junín, no en startups SaaS azules/moradas.
2. **Tipografía masiva con acentos serif italic** — Geist como base, Instrument Serif italic para énfasis emocional.
3. **Fondo claro como base, zonas oscuras estratégicas** — el oscuro es marrón medio cálido, NUNCA negro puro.
4. **Distribución cromática** — cada sección/módulo dominado por un color de acento distinto (terracota, azul, oliva, mostaza) para crear ritmo.
5. **Bordes generosos y sombras sutiles** — radios ≥12px, sombras cálidas con tinte marrón.
6. **Sin AI slop** — sin emojis decorativos, sin íconos genéricos de Material Design, sin gradients de Tailwind por defecto.

---

## 2. FUENTES — REEMPLAZAR la tipografía actual del proyecto

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700;800&family=Instrument+Serif:ital@0;1&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet" />
```

Next.js:
```ts
import { Geist, Instrument_Serif, Geist_Mono } from "next/font/google";
export const geist = Geist({ subsets: ["latin"], variable: "--font-sans" });
export const serif = Instrument_Serif({ subsets: ["latin"], weight: "400", style: ["normal","italic"], variable: "--font-serif" });
export const mono  = Geist_Mono({ subsets: ["latin"], variable: "--font-mono" });
```

CSS global:
```css
html, body {
  font-family: 'Geist', var(--font-sans), -apple-system, sans-serif;
  font-feature-settings: 'ss01', 'cv11';
  -webkit-font-smoothing: antialiased;
  letter-spacing: -0.005em;
  background: var(--bg-base);
  color: var(--ink);
}
```

**NO USAR:** Inter, Roboto, Arial, system-ui, Open Sans, Montserrat, Poppins.

---

## 3. TOKENS DE COLOR — único origen de verdad

```css
:root {
  /* ===== FONDOS ===== */
  --bg-base: #f7f1e8;       /* fondo principal app */
  --bg-elevated: #ffffff;   /* cards, modales, dropdowns */
  --bg-soft: #fdf6ea;       /* cards alternativos / inputs */
  --bg-warm: #ebe0cd;       /* secciones secundarias */

  /* ===== TINTA / TEXTO ===== */
  --ink-strong: #3d2818;    /* títulos, datos importantes */
  --ink: #5a3d2b;           /* cuerpo */
  --ink-warm: #6b4a35;      /* labels, metadatos */
  --ink-muted: #8a6648;     /* placeholders, deshabilitado */

  /* ===== ZONAS OSCURAS (hero cards, CTAs, footer) ===== */
  --dark: #4a3120;
  --dark-2: #5a3d2b;
  --dark-deep: #3d2818;
  --on-dark: #fdf6ea;       /* texto sobre oscuro */
  --on-dark-muted: rgba(253,246,234,0.72);

  /* ===== ACENTO PRINCIPAL ===== */
  --terra-500: #c2562e;     /* primary brand */
  --terra-400: #d97757;     /* hover / claro */
  --terra-700: #8a3a1c;     /* pressed / oscuro */
  --terra-100: rgba(194,86,46,0.10); /* fondo soft */

  /* ===== ACENTOS SECUNDARIOS (rotar por módulos) ===== */
  --blue: #2d5a82;          /* info, links secundarios */
  --blue-100: rgba(45,90,130,0.10);
  --olive: #7a8c5c;         /* success, validaciones */
  --olive-deep: #5d6b46;
  --olive-100: rgba(122,140,92,0.14);
  --gold: #b8893a;          /* warnings, premium */
  --gold-light: #e8b45a;
  --gold-100: rgba(184,137,58,0.14);
  --coral: #e8a691;         /* italics sobre oscuro */

  /* ===== SEMÁNTICOS ===== */
  --success: #5d6b46;
  --warning: #b8893a;
  --error: #a83f3f;
  --info: #2d5a82;

  /* ===== BORDES / LÍNEAS ===== */
  --line: rgba(61, 40, 24, 0.10);
  --line-strong: rgba(61, 40, 24, 0.18);
  --line-on-dark: rgba(253, 246, 234, 0.10);
}
```

Tailwind config (`tailwind.config.ts`):
```ts
extend: {
  colors: {
    bg: { base: '#f7f1e8', elevated: '#ffffff', soft: '#fdf6ea', warm: '#ebe0cd' },
    ink: { strong: '#3d2818', DEFAULT: '#5a3d2b', warm: '#6b4a35', muted: '#8a6648' },
    dark: { DEFAULT: '#4a3120', 2: '#5a3d2b', deep: '#3d2818' },
    terra: { 400: '#d97757', 500: '#c2562e', 700: '#8a3a1c' },
    blue: { brand: '#2d5a82' },
    olive: { DEFAULT: '#7a8c5c', deep: '#5d6b46' },
    gold: { DEFAULT: '#b8893a', light: '#e8b45a' },
    coral: '#e8a691',
  },
  fontFamily: {
    sans: ['Geist', 'sans-serif'],
    serif: ['"Instrument Serif"', 'serif'],
    mono: ['"Geist Mono"', 'monospace'],
  },
}
```

**Reglas de uso de color:**
- **Acción primaria** → terracota (`--terra-500`)
- **Info / links secundarios** → azul
- **Éxito / verificado / activo** → oliva
- **Warning / premium / dorado** → mostaza
- **Por módulo:** Empleos→terracota · Empresas→azul · Capacitación→oliva · Premium→mostaza
- **NUNCA** usar #000, #fff puro para textos, ni morados/púrpuras/azules brillantes Material.

---

## 4. ESCALA TIPOGRÁFICA

| Token | Tamaño | Peso | Tracking | Uso |
|---|---|---|---|---|
| `display` | clamp(56px, 7vw, 108px) | 700 | -0.045em | Hero landing |
| `h1` | 48px | 600 | -0.035em | Page hero |
| `h2` | 36px | 600 | -0.03em | Section title |
| `h3` | 28px | 600 | -0.025em | Card title grande |
| `h4` | 20px | 600 | -0.02em | Card title estándar |
| `h5` | 16px | 600 | -0.01em | Subtítulo |
| `body-lg` | 18px | 400 | -0.005em | Lede / intro |
| `body` | 14.5px | 400 | -0.005em | Cuerpo |
| `body-sm` | 13px | 400 | 0 | Secundario |
| `caption` | 11.5px | 400 | 0 | Meta |
| `kicker` | 11.5px | 500 | 0.12em | UPPERCASE, mono |
| `display-num` | 56px | 400 | -0.03em | Stats (serif) |

**Patrón obligatorio: italic serif para énfasis.** En cualquier titular, identifica 1-3 palabras clave y envuélvelas:
```jsx
<h1>Tu próximo empleo <span className="font-serif italic font-normal text-terra-500">te espera</span></h1>
<h2>Empleos <span className="font-serif italic font-normal text-coral">verificados</span> en Junín</h2>
<h3>Tres pasos, un <span className="font-serif italic font-normal text-terra-500">empleo formal</span></h3>
```

**Stats / números grandes:** usar `font-serif font-normal` (Instrument Serif normal) para sentirse editorial.

---

## 5. ESPACIADO Y RADIOS

```css
--radius-sm: 8px;     /* tags, badges pequeños */
--radius-md: 12px;    /* inputs, botones rectangulares */
--radius-lg: 18px;    /* cards */
--radius-xl: 22px;    /* cards grandes, modales internos */
--radius-2xl: 28px;   /* hero cards, CTA bloques */
--radius-pill: 999px; /* botones, chips, pills */
```

**Reglas:**
- Botones siempre `border-radius: 999px` (excepto submit de formularios largos = 12px)
- Cards mínimo 16px, idealmente 18-22px
- Inputs 10-12px
- **NUNCA** 4px o 6px — se siente tieso y genérico

---

## 6. COMPONENTES CANÓNICOS

### Botones
```css
.btn-primary {
  background: linear-gradient(180deg, var(--terra-400), var(--terra-500));
  color: #fff;
  padding: 14px 24px;
  border-radius: 999px;
  font-weight: 500;
  letter-spacing: -0.005em;
  box-shadow: 0 1px 0 rgba(255,255,255,0.18) inset,
              0 8px 24px -10px rgba(194,86,46,0.5);
  transition: transform 0.15s, filter 0.15s;
}
.btn-primary:hover { transform: translateY(-1px); filter: brightness(1.05); }

.btn-outline {
  border: 1px solid var(--line-strong);
  color: var(--ink-strong);
  padding: 14px 24px;
  border-radius: 999px;
  background: transparent;
}
.btn-outline:hover { border-color: var(--ink-strong); background: rgba(61,40,24,0.04); }

.btn-ghost {
  color: var(--ink-warm);
  padding: 10px 16px;
  border-radius: 999px;
}
.btn-ghost:hover { background: rgba(61,40,24,0.05); }
```

### Cards
```css
.card {
  background: var(--bg-elevated);
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 28px;
  box-shadow: 0 1px 0 rgba(61,40,24,0.04),
              0 8px 24px -16px rgba(61,40,24,0.10);
}

.card-dark {
  background:
    radial-gradient(600px 300px at 20% 0%, rgba(217,119,87,0.28), transparent 60%),
    radial-gradient(500px 300px at 90% 100%, rgba(122,140,92,0.18), transparent 65%),
    linear-gradient(135deg, var(--dark), var(--dark-2));
  color: var(--on-dark);
  border-radius: 22px;
  padding: 36px 40px;
}
```

### Inputs
```css
.field input, .field select, .field textarea {
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid #d6c5a8;
  background: #fff;
  font-family: inherit;
  font-size: 14.5px;
  color: var(--ink-strong);
  outline: none;
  transition: border-color 0.18s, box-shadow 0.18s;
}
.field input:focus {
  border-color: var(--terra-500);
  box-shadow: 0 0 0 3px rgba(194,86,46,0.14);
}
.field label { font-size: 13px; font-weight: 500; color: var(--ink-strong); margin-bottom: 8px; display:block; }
```

### Tags / Chips
```css
.tag { padding: 4px 10px; border-radius: 999px; font-size: 11.5px; background: rgba(61,40,24,0.06); color: var(--ink-warm); }
.tag-terra { background: var(--terra-100); color: var(--terra-500); font-weight: 500; }
.tag-blue  { background: var(--blue-100);  color: var(--blue);       font-weight: 500; }
.tag-olive { background: var(--olive-100); color: var(--olive-deep); font-weight: 500; }
.tag-gold  { background: var(--gold-100);  color: #8a6620;           font-weight: 500; }
```

### Progress bars
```css
.progress-track { background: rgba(61,40,24,0.10); height: 8px; border-radius: 999px; overflow: hidden; }
.progress-fill  { background: linear-gradient(90deg, var(--terra-400), var(--gold-light)); height: 100%; border-radius: 999px; }

/* Sobre fondo oscuro */
.progress-track-on-dark { background: rgba(253,246,234,0.18); }
```

### Avatares
```css
.avatar { width: 38px; height: 38px; border-radius: 999px; background: linear-gradient(135deg, var(--terra-400), var(--terra-500)); color: #fff; display: grid; place-items: center; font-weight: 600; font-size: 13px; }
```

### Brand mark (logo)
- Cuadrado 32-40px, `border-radius: 9px`, gradient `linear-gradient(135deg, var(--terra-400), var(--terra-500))`, ícono blanco dentro
- Sombra: `0 6px 20px -6px rgba(194,86,46,0.6), inset 0 1px 0 rgba(255,255,255,0.15)`

---

## 7. PATRONES DE PANTALLA

### Hero card (welcome, banners, prompts grandes)
- `card-dark` con doble glow radial (terracota arriba-izq, oliva abajo-der)
- Heading h2/h3 con palabra clave en serif italic + color coral
- Texto sobre `--on-dark`
- Progress bar `progress-track-on-dark`
- **NO** usar gradient morado/azul Material — solo `--dark` warm

### Listados (empleos, postulaciones, empresas)
- Grid 2 columnas en desktop, 1 en mobile
- Cada item es un `.card` con logo coloreado, título, tags, meta abajo separada por `border-top: 1px solid var(--line)`
- Hover: `transform: translateY(-2px); border-color: var(--line-strong);`

### Formularios largos (registro, CV builder)
- Card central max-width 560px sobre `var(--bg-base)`
- Steps en mono uppercase con kicker style
- Botón submit ancho completo, radius 12px (excepción a la regla pill)
- Línea divisoria sutil entre secciones

### Empty states
- Centrado, ícono grande con color de acento del módulo
- Heading h4 con palabra clave en serif italic
- Texto secundario `--ink-warm`
- 1 CTA primario

### Modales
- Backdrop `rgba(26,15,10,0.55)` + `backdrop-filter: blur(8px)`
- Modal card `border-radius: 24px`, sombra `0 50px 100px -30px rgba(0,0,0,0.4)`
- Si tiene panel split, lado izq con gradient cálido claro (no oscuro) para que sea legible

---

## 8. ICONOGRAFÍA

- **Librería recomendada:** Lucide (`lucide-react`) — line-style, peso 1.5-1.8
- Color de íconos sigue el contexto: por defecto `--ink-warm`, en acento toma color del módulo
- Containers de íconos en cards: `32-56px`, `border-radius: 8-14px`, fondo translúcido del color (`--terra-100`, `--blue-100`, etc)
- **NO usar:** Material Icons, Heroicons sólidos, FontAwesome, emojis decorativos

---

## 9. ELEVACIÓN Y SOMBRAS

```css
--shadow-sm: 0 1px 0 rgba(61,40,24,0.04);
--shadow-md: 0 1px 0 rgba(61,40,24,0.04), 0 8px 24px -16px rgba(61,40,24,0.10);
--shadow-lg: 0 8px 32px -12px rgba(61,40,24,0.16);
--shadow-glow-terra: 0 8px 32px -8px rgba(194,86,46,0.30);
--shadow-modal: 0 50px 100px -30px rgba(0,0,0,0.40);
```

Sombras siempre con tinte marrón (no gris azulado). Mantener sutiles — preferir `border` + `shadow-sm` sobre `shadow-xl`.

---

## 10. MICROCOPIA / TONO

- **Conversacional pero profesional.** Tutea al usuario.
- **Frases cortas en CTAs.** "Crear cuenta" mejor que "Registrar mi nueva cuenta".
- **Énfasis con italic serif** en momentos emocionales: "Tu próximo empleo *te espera*", "El primer paso *importa*".
- **Datos como insignia institucional.** Usar formato "2,400+ trabajadores", "87% colocación".
- **Sin signos exclamativos excesivos.** Máximo 1 por pantalla.

---

## 11. CHECKLIST AL CREAR / MODIFICAR UNA PANTALLA

- [ ] Usa Geist en cuerpo, Instrument Serif italic en énfasis
- [ ] Fondo `--bg-base` (crema), no blanco puro ni gris
- [ ] Color primario terracota, NO morado/azul brillante
- [ ] Cards con radius ≥18px y sombra cálida sutil
- [ ] Botones primarios pill con gradient terracota
- [ ] Al menos 1 acento secundario (azul/oliva/mostaza) para no monocromar
- [ ] Textos con colores tinta cálida, no `text-gray-900`
- [ ] Iconos Lucide line-style en contenedor coloreado
- [ ] Sin emojis decorativos en UI
- [ ] Headings con palabra clave en serif italic

---

## 12. MIGRACIÓN — orden recomendado

1. **Reemplazar tokens** en `globals.css` / `tailwind.config` (ver §3)
2. **Cargar fuentes** y aplicar `font-family` global (ver §2)
3. **Encontrar y reemplazar** todos los `bg-purple-*`, `bg-indigo-*`, `bg-blue-600`, `from-purple`, `to-indigo` → tokens de la nueva paleta
4. **Encontrar y reemplazar** `rounded-md`, `rounded-lg` por `rounded-2xl` (18px) en cards y `rounded-full` en botones
5. **Buscar** `text-gray-*`, `text-slate-*`, `text-zinc-*` → reemplazar por `text-ink`, `text-ink-warm`, etc.
6. **Buscar** `shadow-lg`, `shadow-xl` → reemplazar por la escala de sombras cálidas
7. **Revisar** títulos h1/h2/h3 — añadir serif italic en palabra clave
8. **Auditar** cada pantalla con el checklist §11

Aplica este sistema de forma consistente. Cualquier nueva pantalla, componente, email o vista de admin debe seguirlo sin excepción.