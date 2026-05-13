# SPRINT 5 — INSTRUCCIÓN 3 de 6
# Agente: `senior-frontend`
# Skills a cargar: `skills/senior-frontend`, `skills/ui-ux-pro-max`
# Tarea: FlagContentButton + ModerationQueue + Orientación laboral PRIMER_EMPLEO + WCAG 2.1 AA + Playwright E2E

---

## CONTEXTO OBLIGATORIO

Lee el archivo `CLAUDE.md` en la raíz del repositorio antes de escribir cualquier línea de código.
La instrucción 2 del Sprint 5 implementó el backend de moderación, RF faltantes y seed realista.

**Reglas del CLAUDE.md vigentes:**
- No hardcodear strings en español — siempre react-intl
- Marketplace EXCLUSIVO de OFICIO
- ts-pattern para routing por worker_type
- i18n es-PE en todo el frontend

---

## PARTE A — FlagContentButton (reporte de contenido)

Crea `frontend/src/shared/FlagContentButton.tsx`:

```tsx
// frontend/src/shared/FlagContentButton.tsx
import { useState } from 'react';
import { useIntl } from 'react-intl';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { api } from '../services/api';

const flagSchema = z.object({
  reason: z.enum(['spam', 'falso', 'ofensivo', 'otro']),
  details: z.string().max(500).optional(),
});

type FlagFormData = z.infer<typeof flagSchema>;

interface FlagContentButtonProps {
  listingId: string;
  onFlagged?: () => void;
}

export const FlagContentButton: React.FC<FlagContentButtonProps> = ({ listingId, onFlagged }) => {
  const intl = useIntl();
  const [isOpen, setIsOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const { register, handleSubmit, formState: { errors } } = useForm<FlagFormData>({
    resolver: zodResolver(flagSchema),
  });

  const onSubmit = async (data: FlagFormData) => {
    setIsSubmitting(true);
    try {
      await api.post(`/api/v1/moderation/listings/${listingId}/flag`, data);
      setSubmitted(true);
      onFlagged?.();
      setTimeout(() => setIsOpen(false), 2000);
    } catch {
      /* error handled by interceptor */
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="text-gray-400 hover:text-red-500 text-xs flex items-center gap-1 transition-colors"
        aria-label={intl.formatMessage({ id: 'flag.button.aria_label' })}
      >
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"
          aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9" />
        </svg>
        {intl.formatMessage({ id: 'flag.button.label' })}
      </button>

      {/* Modal de reporte */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="flag-dialog-title"
        >
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6">
            <h2 id="flag-dialog-title" className="text-lg font-bold text-gray-800 mb-4">
              {intl.formatMessage({ id: 'flag.modal.title' })}
            </h2>

            {submitted ? (
              <div className="text-center py-6">
                <div className="text-green-500 text-4xl mb-2">✓</div>
                <p className="text-gray-600">{intl.formatMessage({ id: 'flag.modal.success' })}</p>
              </div>
            ) : (
              <form onSubmit={handleSubmit(onSubmit)} noValidate>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {intl.formatMessage({ id: 'flag.modal.reason_label' })}
                  </label>
                  <select
                    {...register('reason')}
                    className="w-full border border-gray-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-red-500"
                    aria-describedby={errors.reason ? 'reason-error' : undefined}
                  >
                    <option value="">{intl.formatMessage({ id: 'flag.modal.reason_placeholder' })}</option>
                    <option value="spam">{intl.formatMessage({ id: 'flag.reason.spam' })}</option>
                    <option value="falso">{intl.formatMessage({ id: 'flag.reason.falso' })}</option>
                    <option value="ofensivo">{intl.formatMessage({ id: 'flag.reason.ofensivo' })}</option>
                    <option value="otro">{intl.formatMessage({ id: 'flag.reason.otro' })}</option>
                  </select>
                  {errors.reason && (
                    <p id="reason-error" className="text-red-500 text-xs mt-1" role="alert">
                      {intl.formatMessage({ id: 'flag.modal.reason_required' })}
                    </p>
                  )}
                </div>

                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {intl.formatMessage({ id: 'flag.modal.details_label' })}
                  </label>
                  <textarea
                    {...register('details')}
                    rows={3}
                    className="w-full border border-gray-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-red-500"
                    placeholder={intl.formatMessage({ id: 'flag.modal.details_placeholder' })}
                  />
                </div>

                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => setIsOpen(false)}
                    className="flex-1 py-2.5 border border-gray-300 rounded-lg text-gray-600 text-sm hover:bg-gray-50"
                  >
                    {intl.formatMessage({ id: 'common.cancel' })}
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="flex-1 py-2.5 bg-red-500 text-white rounded-lg text-sm hover:bg-red-600 disabled:opacity-50"
                  >
                    {isSubmitting
                      ? intl.formatMessage({ id: 'common.sending' })
                      : intl.formatMessage({ id: 'flag.modal.submit' })}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </>
  );
};
```

---

## PARTE B — Cola de Moderación (solo MODERATOR/ADMIN)

Crea `frontend/src/admin/moderation/ModerationQueue.tsx`:

```tsx
// frontend/src/admin/moderation/ModerationQueue.tsx
import { useState } from 'react';
import { useIntl } from 'react-intl';
import { useModerationQueue } from '../../hooks/useModerationQueue';
import { api } from '../../services/api';

export const ModerationQueue: React.FC = () => {
  const intl = useIntl();
  const { flags, isLoading, refetch } = useModerationQueue();
  const [processing, setProcessing] = useState<string | null>(null);

  const handleBan = async (listingId: string, flagId: string) => {
    setProcessing(flagId);
    try {
      await api.post(`/api/v1/moderation/listings/${listingId}/ban`, {
        params: { reason: 'Contenido reportado y revisado por moderador' }
      });
      refetch();
    } finally {
      setProcessing(null);
    }
  };

  const handleDismiss = async (flagId: string) => {
    setProcessing(flagId);
    try {
      await api.patch(`/api/v1/moderation/flags/${flagId}/dismiss`);
      refetch();
    } finally {
      setProcessing(null);
    }
  };

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-800">
          {intl.formatMessage({ id: 'admin.moderation.title' })}
        </h2>
        <span className="bg-red-100 text-red-700 text-sm font-medium px-3 py-1 rounded-full">
          {flags.length} {intl.formatMessage({ id: 'admin.moderation.pending' })}
        </span>
      </div>

      {flags.length === 0 ? (
        <div className="bg-green-50 text-green-700 rounded-xl p-6 text-center">
          <div className="text-3xl mb-2">✓</div>
          <p>{intl.formatMessage({ id: 'admin.moderation.empty_queue' })}</p>
        </div>
      ) : (
        flags.map((flag) => (
          <div key={flag.id} className="bg-white rounded-xl shadow border border-gray-100 p-5">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                    flag.reason === 'ofensivo' ? 'bg-red-100 text-red-700' :
                    flag.reason === 'falso'    ? 'bg-orange-100 text-orange-700' :
                    'bg-gray-100 text-gray-600'
                  }`}>
                    {intl.formatMessage({ id: `flag.reason.${flag.reason}` })}
                  </span>
                  <span className="text-xs text-gray-400">
                    {new Date(flag.created_at).toLocaleDateString('es-PE')}
                  </span>
                </div>
                <p className="text-sm text-gray-700 font-medium truncate">
                  Listing: {flag.listing_id}
                </p>
                {flag.details && (
                  <p className="text-sm text-gray-500 mt-1">{flag.details}</p>
                )}
              </div>
              <div className="flex gap-2 flex-shrink-0">
                <button
                  onClick={() => handleDismiss(flag.id)}
                  disabled={processing === flag.id}
                  className="px-3 py-1.5 border border-gray-300 text-gray-600 text-xs rounded-lg hover:bg-gray-50 disabled:opacity-50"
                >
                  {intl.formatMessage({ id: 'admin.moderation.dismiss' })}
                </button>
                <button
                  onClick={() => handleBan(flag.listing_id, flag.id)}
                  disabled={processing === flag.id}
                  className="px-3 py-1.5 bg-red-500 text-white text-xs rounded-lg hover:bg-red-600 disabled:opacity-50"
                >
                  {intl.formatMessage({ id: 'admin.moderation.ban' })}
                </button>
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );
};
```

---

## PARTE C — Orientación laboral (PRIMER_EMPLEO)

Crea `frontend/src/modules/primer-empleo/OrientacionLaboral.tsx`:

```tsx
// frontend/src/modules/primer-empleo/OrientacionLaboral.tsx
import { useState } from 'react';
import { useIntl } from 'react-intl';

interface OrientacionItem {
  id: string;
  emoji: string;
  titleKey: string;
  contentKey: string;
}

const ORIENTACION_ITEMS: OrientacionItem[] = [
  { id: 'interview', emoji: '👔', titleKey: 'orientacion.interview.title', contentKey: 'orientacion.interview.content' },
  { id: 'clothes',   emoji: '👗', titleKey: 'orientacion.clothes.title',   contentKey: 'orientacion.clothes.content' },
  { id: 'salary',    emoji: '💰', titleKey: 'orientacion.salary.title',    contentKey: 'orientacion.salary.content' },
  { id: 'cv',        emoji: '📄', titleKey: 'orientacion.cv.title',        contentKey: 'orientacion.cv.content' },
  { id: 'rights',    emoji: '⚖️', titleKey: 'orientacion.rights.title',   contentKey: 'orientacion.rights.content' },
];

export const OrientacionLaboral: React.FC = () => {
  const intl = useIntl();
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <div className="bg-white rounded-2xl shadow p-6">
      <h2 className="font-bold text-gray-800 mb-4">
        {intl.formatMessage({ id: 'orientacion.section.title' })}
      </h2>
      <div className="space-y-2">
        {ORIENTACION_ITEMS.map((item) => (
          <div key={item.id} className="border border-gray-100 rounded-xl overflow-hidden">
            <button
              onClick={() => setExpanded(expanded === item.id ? null : item.id)}
              className="w-full flex items-center justify-between p-3 text-left hover:bg-blue-50 transition-colors"
              aria-expanded={expanded === item.id}
              aria-controls={`orientacion-${item.id}`}
            >
              <span className="flex items-center gap-2 font-medium text-gray-700 text-sm">
                <span aria-hidden="true">{item.emoji}</span>
                {intl.formatMessage({ id: item.titleKey })}
              </span>
              <svg
                className={`w-4 h-4 text-gray-400 transition-transform ${expanded === item.id ? 'rotate-180' : ''}`}
                fill="none" stroke="currentColor" viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            {expanded === item.id && (
              <div
                id={`orientacion-${item.id}`}
                className="px-4 pb-3 text-sm text-gray-600 bg-blue-50 leading-relaxed"
              >
                {intl.formatMessage({ id: item.contentKey })}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
```

---

## PARTE D — Accesibilidad WCAG 2.1 AA

Auditar y corregir los componentes existentes para cumplir WCAG 2.1 AA:

### D1 — Checklist de accesibilidad

```bash
# Instalar axe para audit automático
npm install --save-dev @axe-core/react jest-axe
```

**Reglas críticas a verificar en TODOS los componentes:**

1. **Contraste de colores** — ratio mínimo 4.5:1 para texto normal, 3:1 para texto grande
   - El azul `#4299e1` sobre blanco pasa el ratio 3.1:1 (texto grande ✅, texto normal requiere más oscuro)
   - Usar `#2b6cb0` para texto sobre fondo blanco
   - El ámbar `#744210` sobre fondo ámbar claro ✅

2. **Textos alternativos** — todo `<img>` debe tener `alt`
   ```tsx
   // ✅ Correcto:
   <img src="/logo-drtpe.svg" alt="DRTPE Junín — Sistema de Intermediación Laboral" />
   // ✅ Decorativa:
   <img src="/decoracion.png" alt="" aria-hidden="true" />
   ```

3. **Etiquetas de formulario** — todo input debe tener `<label>` asociado
   ```tsx
   // ✅ Correcto:
   <label htmlFor="email">Correo electrónico</label>
   <input id="email" type="email" ... />
   // ✅ O con aria-label:
   <input aria-label="Buscar servicios" type="search" ... />
   ```

4. **Focus visible** — el foco del teclado debe ser visible
   ```css
   /* En tailwind — agregar a los botones interactivos: */
   focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2
   ```

5. **Roles ARIA** — modales y diálogos deben tener `role="dialog"` y `aria-modal="true"`

6. **Skip link** — agregar en el layout principal:
   ```tsx
   // En MainLayout.tsx — primer elemento del body:
   <a
     href="#main-content"
     className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:bg-white focus:px-4 focus:py-2 focus:rounded focus:shadow"
   >
     {intl.formatMessage({ id: 'a11y.skip_to_content' })}
   </a>
   <main id="main-content" tabIndex={-1}>
     ...
   </main>
   ```

7. **Idioma del documento** — `<html lang="es-PE">`

### D2 — Componente accesible: SkillTag con opciones de eliminación

```tsx
// frontend/src/shared/SkillTag.tsx
interface SkillTagProps {
  label: string;
  removable?: boolean;
  onRemove?: (label: string) => void;
}

export const SkillTag: React.FC<SkillTagProps> = ({ label, removable, onRemove }) => {
  const intl = useIntl();
  return (
    <span className="inline-flex items-center gap-1 bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm">
      {label}
      {removable && onRemove && (
        <button
          onClick={() => onRemove(label)}
          className="ml-1 text-blue-500 hover:text-blue-700 focus-visible:ring-2 focus-visible:ring-blue-500 rounded"
          aria-label={intl.formatMessage({ id: 'skill_tag.remove_aria' }, { skill: label })}
        >
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </span>
  );
};
```

---

## PARTE E — Responsive Mobile

Auditar los componentes del Sprint 4 para mobile:

```tsx
// Breakpoints de Tailwind a usar:
// sm: 640px, md: 768px, lg: 1024px

// ✅ Onboarding — ya tiene diseño centrado
// ✅ Wizard — grid 1 col en mobile, 2 col en desktop (ya implementado)

// Verificar que el AdminDashboard es usable en mobile:
// Los BarChart de Recharts deben usar ResponsiveContainer (ya implementado)
// En mobile los gráficos deben ser scrollables horizontalmente:
<div className="overflow-x-auto">
  <div className="min-w-[300px]">
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data}>...</BarChart>
    </ResponsiveContainer>
  </div>
</div>

// Portfolio cards — grid responsive:
// 1 col en mobile, 2 col en sm, 3 col en lg
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">

// Botones de acción — full width en mobile:
<div className="flex flex-col sm:flex-row gap-3">
  <button className="w-full sm:w-auto ...">Acción 1</button>
  <button className="w-full sm:w-auto ...">Acción 2</button>
</div>
```

---

## PARTE F — Tests Playwright E2E

Configura Playwright e implementa los tests E2E más críticos:

```bash
cd frontend
npm install --save-dev @playwright/test
npx playwright install chromium
```

Crea `frontend/tests/e2e/`:

```typescript
// frontend/tests/e2e/onboarding.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Onboarding — Detección de tipo de usuario', () => {
  test.beforeEach(async ({ page }) => {
    // Registrar usuario de prueba
    await page.goto('/register');
    // ... setup
  });

  test('Flujo PRIMER_EMPLEO: responder Sí a primera pregunta', async ({ page }) => {
    await page.goto('/onboarding');
    await expect(page.getByText('¿Estás buscando tu primer empleo?')).toBeVisible();
    await page.getByRole('button', { name: /primer empleo/i }).click();
    // Debe redirigir al wizard
    await expect(page).toHaveURL(/\/wizard\/step\/1/);
  });

  test('Flujo OFICIO: No → Sí', async ({ page }) => {
    await page.goto('/onboarding');
    await page.getByRole('button', { name: /ya tengo experiencia/i }).click();
    await expect(page.getByText('¿Trabajas en un oficio?')).toBeVisible();
    await page.getByRole('button', { name: /soy trabajador de oficio/i }).click();
    await expect(page).toHaveURL(/\/oficio\/portfolio/);
  });

  test('Flujo EXPERIENCIA: No → No', async ({ page }) => {
    await page.goto('/onboarding');
    await page.getByRole('button', { name: /ya tengo experiencia/i }).click();
    await page.getByRole('button', { name: /trabajo en otro rubro/i }).click();
    await expect(page).toHaveURL(/\/dashboard/);
  });
});
```

```typescript
// frontend/tests/e2e/marketplace_access.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Marketplace — Control de acceso por tipo', () => {
  test('PRIMER_EMPLEO no puede publicar en marketplace', async ({ page }) => {
    // Login como PRIMER_EMPLEO
    await loginAs(page, 'primer_empleo');
    // Intentar acceder directamente
    await page.goto('/marketplace');
    // Debe redirigir (WorkerTypeGuard)
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('OFICIO puede acceder y publicar en marketplace', async ({ page }) => {
    await loginAs(page, 'oficio');
    await page.goto('/oficio/portfolio');
    await expect(page.getByText(/agregar trabajo/i)).toBeVisible();
  });
});
```

```typescript
// frontend/tests/e2e/wizard.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Wizard PRIMER_EMPLEO — 6 pasos', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'primer_empleo');
    await page.goto('/wizard/step/1');
  });

  test('Paso 1 — Datos personales: campos requeridos', async ({ page }) => {
    await expect(page.getByText(/datos personales/i)).toBeVisible();
    // Intentar avanzar sin datos
    await page.getByRole('button', { name: /siguiente/i }).click();
    await expect(page.getByRole('alert')).toBeVisible();
  });

  test('Paso 3 — Habilidades: extracción NLP en tiempo real', async ({ page }) => {
    await page.goto('/wizard/step/3');
    const textarea = page.getByPlaceholder(/cuéntanos/i);
    await textarea.fill('Ayudo a mi papá en su carpintería los fines de semana y soy muy puntual');
    // Esperar debounce + respuesta del API
    await page.waitForTimeout(1500);
    // Verificar que aparecen skills extraídas
    await expect(page.getByText(/habilidades que encontramos/i)).toBeVisible({ timeout: 5000 });
  });
});
```

```typescript
// frontend/tests/e2e/accessibility.spec.ts
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Accesibilidad WCAG 2.1 AA', () => {
  const pagesToTest = [
    { path: '/login',      name: 'Login' },
    { path: '/onboarding', name: 'Onboarding' },
    { path: '/dashboard',  name: 'Dashboard' },
  ];

  for (const { path, name } of pagesToTest) {
    test(`${name} — sin violaciones WCAG 2.1 AA`, async ({ page }) => {
      if (path !== '/login') await loginAs(page, 'experiencia');
      await page.goto(path);
      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze();
      expect(results.violations).toEqual([]);
    });
  }
});
```

**Configurar `playwright.config.ts`:**

```typescript
// frontend/playwright.config.ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  use: {
    baseURL: 'http://localhost:3000',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile-chrome', use: { ...devices['Pixel 5'] } },
  ],
});
```

---

## PARTE G — i18n: claves nuevas del Sprint 5

Agrega en `frontend/src/i18n/es-PE.json`:

```json
{
  "flag.button.label": "Reportar",
  "flag.button.aria_label": "Reportar este contenido como inapropiado",
  "flag.modal.title": "Reportar contenido",
  "flag.modal.reason_label": "¿Por qué reportas esto?",
  "flag.modal.reason_placeholder": "Selecciona un motivo",
  "flag.modal.details_label": "Detalles adicionales (opcional)",
  "flag.modal.details_placeholder": "Cuéntanos más sobre el problema...",
  "flag.modal.submit": "Enviar reporte",
  "flag.modal.success": "Gracias por tu reporte. Nuestro equipo lo revisará.",
  "flag.modal.reason_required": "Selecciona un motivo para continuar",
  "flag.reason.spam": "Es publicidad no deseada (spam)",
  "flag.reason.falso": "La información es falsa o engañosa",
  "flag.reason.ofensivo": "El contenido es ofensivo o inapropiado",
  "flag.reason.otro": "Otro motivo",
  "admin.moderation.title": "Cola de Moderación",
  "admin.moderation.pending": "pendientes",
  "admin.moderation.empty_queue": "¡Sin reportes pendientes! Todo está en orden.",
  "admin.moderation.dismiss": "Desestimar",
  "admin.moderation.ban": "Banear",
  "orientacion.section.title": "Orientación Laboral",
  "orientacion.interview.title": "¿Cómo ir a una entrevista?",
  "orientacion.interview.content": "Llega 10 minutos antes, vístete apropiadamente para el puesto, lleva tu CV impreso, saluda con seguridad y sonríe. Si no sabes algo, es mejor decirlo honestamente.",
  "orientacion.clothes.title": "¿Qué ropa usar?",
  "orientacion.clothes.content": "Para oficina o comercio: ropa limpia y planchada, colores sobrios. Para trabajo técnico u oficio: ropa cómoda y limpia. Lo importante es ir presentable y limpio.",
  "orientacion.salary.title": "¿Cómo negociar mi primer sueldo?",
  "orientacion.salary.content": "El sueldo mínimo en Perú es S/. 1,025. Para tu primer empleo, acepta aprender más que ganar. Pregunta sobre bonos, capacitaciones y posibilidades de crecimiento.",
  "orientacion.cv.title": "¿Cómo mejorar mi CV?",
  "orientacion.cv.content": "Completa todos los pasos del wizard. Agrega tus actividades escolares, voluntariados y cualquier trabajo que hayas hecho aunque sea informal. Cada experiencia cuenta.",
  "orientacion.rights.title": "Mis derechos como trabajador",
  "orientacion.rights.content": "Tienes derecho a: contrato de trabajo, sueldo mínimo S/. 1,025, gratificaciones en julio y diciembre, vacaciones de 15 días, seguro de salud (ESSALUD) y AFP. Ante dudas, contacta a la DRTPE-Junín.",
  "a11y.skip_to_content": "Ir al contenido principal",
  "skill_tag.remove_aria": "Eliminar habilidad: {skill}",
  "common.cancel": "Cancelar",
  "common.sending": "Enviando..."
}
```

---

## VERIFICACIONES FINALES

```bash
# Build sin errores
cd frontend && npm run build

# TypeScript
npx tsc --noEmit

# Tests unitarios frontend
npm run test -- --coverage --passWithNoTests

# Tests E2E (requiere servidor corriendo)
npx playwright test --reporter=list

# Lint accesibilidad básica
npx axe http://localhost:3000/onboarding --tags wcag2aa
```

---

## ENTREGABLES DE ESTA INSTRUCCIÓN

- `frontend/src/shared/FlagContentButton.tsx`
- `frontend/src/shared/SkillTag.tsx` — actualizado con a11y
- `frontend/src/admin/moderation/ModerationQueue.tsx`
- `frontend/src/modules/primer-empleo/OrientacionLaboral.tsx`
- `frontend/src/i18n/es-PE.json` — claves Sprint 5
- `frontend/tests/e2e/onboarding.spec.ts`
- `frontend/tests/e2e/marketplace_access.spec.ts`
- `frontend/tests/e2e/wizard.spec.ts`
- `frontend/tests/e2e/accessibility.spec.ts`
- `frontend/playwright.config.ts`
- Correcciones WCAG 2.1 AA en componentes existentes

---

**Cuando termines, el agente `devops-engineer` recibirá la instrucción 4
para el deploy real en GCP Cloud Run + Terraform + backups automáticos.**
