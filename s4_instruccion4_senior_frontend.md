# SPRINT 4 — INSTRUCCIÓN 4 de 5
# Agente: `senior-frontend`
# Skills a cargar: `skills/senior-frontend`, `skills/ui-ux-pro-max`
# Tarea: Frontend completo — Onboarding, Wizard 6 pasos, Dashboard por tipo, Portfolio OFICIO, Panel Admin

---

## CONTEXTO OBLIGATORIO

Lee el archivo `CLAUDE.md` en la raíz del repositorio antes de escribir cualquier línea de código.
El frontend debe seguir exactamente los Flujos A, B y C del CLAUDE.md.

**Stack frontend del proyecto:**
- React 18 + Vite
- Tailwind CSS (sin CSS personalizado salvo variables)
- react-hook-form + zod (validación)
- react-intl (i18n es-PE)
- Axios (cliente HTTP con interceptores JWT)
- Recharts (gráficos del dashboard)
- react-dropzone (upload de fotos)
- WebSocket para notificaciones en tiempo real

**Regla crítica del CLAUDE.md:**
- NUNCA hardcodear strings en español → siempre usar `react-intl`
- El marketplace es EXCLUSIVO de OFICIO — nunca mostrar a PRIMER_EMPLEO ni EXPERIENCIA
- El wizard es EXCLUSIVO de PRIMER_EMPLEO — nunca mostrar a otros tipos
- El portfolio visual es EXCLUSIVO de OFICIO

---

## PARTE A — Estructura de rutas y Guards

Crea `frontend/src/guards/`:

```tsx
// frontend/src/guards/WorkerTypeGuard.tsx
import { Navigate } from 'react-router-dom';
import { useWorkerContext } from '../context/WorkerContext';

interface WorkerTypeGuardProps {
  allowedTypes: ('primer_empleo' | 'experiencia' | 'oficio')[];
  children: React.ReactNode;
  redirectTo?: string;
}

export const WorkerTypeGuard: React.FC<WorkerTypeGuardProps> = ({
  allowedTypes,
  children,
  redirectTo = '/dashboard',
}) => {
  const { workerType, isLoading } = useWorkerContext();

  if (isLoading) return <LoadingSpinner />;
  if (!workerType) return <Navigate to="/onboarding" replace />;
  if (!allowedTypes.includes(workerType)) return <Navigate to={redirectTo} replace />;

  return <>{children}</>;
};

// frontend/src/guards/AuthGuard.tsx
export const AuthGuard: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuthContext();
  if (isLoading) return <LoadingSpinner />;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
};

// frontend/src/guards/AdminGuard.tsx
export const AdminGuard: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuthContext();
  if (user?.role !== 'admin') return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
};
```

Configura `frontend/src/App.tsx` con rutas protegidas:

```tsx
// frontend/src/App.tsx
import { Routes, Route } from 'react-router-dom';

export const App = () => (
  <Routes>
    {/* Públicas */}
    <Route path="/login"           element={<LoginPage />} />
    <Route path="/register"        element={<RegisterPage />} />
    <Route path="/p/:slug"         element={<PublicPortfolioPage />} />

    {/* Onboarding — detecta tipo */}
    <Route path="/onboarding"      element={<AuthGuard><OnboardingPage /></AuthGuard>} />

    {/* Dashboard diferenciado */}
    <Route path="/dashboard"       element={
      <AuthGuard>
        <WorkerDashboard />
      </AuthGuard>
    } />

    {/* Wizard — solo PRIMER_EMPLEO */}
    <Route path="/wizard/*"        element={
      <AuthGuard>
        <WorkerTypeGuard allowedTypes={['primer_empleo']}>
          <WizardLayout />
        </WorkerTypeGuard>
      </AuthGuard>
    } />

    {/* Portfolio — solo OFICIO */}
    <Route path="/oficio/portfolio" element={
      <AuthGuard>
        <WorkerTypeGuard allowedTypes={['oficio']}>
          <PortfolioPage />
        </WorkerTypeGuard>
      </AuthGuard>
    } />

    {/* Marketplace — EXCLUSIVO OFICIO */}
    <Route path="/marketplace/*"   element={
      <AuthGuard>
        <WorkerTypeGuard allowedTypes={['oficio']}>
          <MarketplacePage />
        </WorkerTypeGuard>
      </AuthGuard>
    } />

    {/* Matching — todos los tipos */}
    <Route path="/matches"         element={<AuthGuard><MatchesPage /></AuthGuard>} />

    {/* Admin — solo ADMIN */}
    <Route path="/admin/*"         element={
      <AuthGuard>
        <AdminGuard>
          <AdminLayout />
        </AdminGuard>
      </AuthGuard>
    } />
  </Routes>
);
```

---

## PARTE B — Onboarding: detección de tipo (Flujo 0)

Crea `frontend/src/onboarding/OnboardingPage.tsx`:

```tsx
// frontend/src/onboarding/OnboardingPage.tsx
import { useState } from 'react';
import { useIntl } from 'react-intl';
import { useNavigate } from 'react-router-dom';
import { useWorkerContext } from '../context/WorkerContext';
import { api } from '../services/api';

type OnboardingStep = 'step1' | 'step2' | 'result';

export const OnboardingPage: React.FC = () => {
  const intl = useIntl();
  const navigate = useNavigate();
  const { setWorkerType } = useWorkerContext();
  const [step, setStep] = useState<OnboardingStep>('step1');
  const [isLoading, setIsLoading] = useState(false);

  const handleStep1 = async (isFirstJob: boolean) => {
    if (isFirstJob) {
      await submitOnboarding({ is_first_job: true, is_trade_worker: false });
    } else {
      setStep('step2');
    }
  };

  const handleStep2 = async (isTradeWorker: boolean) => {
    await submitOnboarding({ is_first_job: false, is_trade_worker: isTradeWorker });
  };

  const submitOnboarding = async (answers: {
    is_first_job: boolean;
    is_trade_worker: boolean;
    trade_category?: string;
  }) => {
    setIsLoading(true);
    try {
      const { data } = await api.post('/api/v1/onboarding/detect-type', answers);
      setWorkerType(data.worker_type);
      // Redirigir según tipo
      if (data.worker_type === 'primer_empleo') navigate('/wizard/step/1');
      else if (data.worker_type === 'oficio') navigate('/oficio/portfolio');
      else navigate('/dashboard');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-blue-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-lg max-w-lg w-full p-8">
        {/* Logo DRTPE */}
        <div className="text-center mb-8">
          <img src="/logo-drtpe.svg" alt="DRTPE Junín" className="h-12 mx-auto mb-2" />
          <h1 className="text-2xl font-bold text-gray-800">
            {intl.formatMessage({ id: 'onboarding.title' })}
          </h1>
          <p className="text-gray-500 mt-1">
            {intl.formatMessage({ id: 'onboarding.subtitle' })}
          </p>
        </div>

        {step === 'step1' && (
          <Step1 onAnswer={handleStep1} isLoading={isLoading} />
        )}
        {step === 'step2' && (
          <Step2 onAnswer={handleStep2} isLoading={isLoading} onBack={() => setStep('step1')} />
        )}
      </div>
    </div>
  );
};

const Step1: React.FC<{ onAnswer: (v: boolean) => void; isLoading: boolean }> = ({ onAnswer, isLoading }) => {
  const intl = useIntl();
  return (
    <div className="space-y-4">
      <p className="text-lg font-medium text-gray-700 text-center">
        {intl.formatMessage({ id: 'onboarding.step1.question' })}
      </p>
      <div className="grid grid-cols-2 gap-4">
        <button
          onClick={() => onAnswer(true)}
          disabled={isLoading}
          className="py-4 px-6 bg-blue-500 hover:bg-blue-600 text-white rounded-xl font-semibold transition-colors disabled:opacity-50"
        >
          {intl.formatMessage({ id: 'onboarding.step1.yes' })}
        </button>
        <button
          onClick={() => onAnswer(false)}
          disabled={isLoading}
          className="py-4 px-6 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl font-semibold transition-colors disabled:opacity-50"
        >
          {intl.formatMessage({ id: 'onboarding.step1.no' })}
        </button>
      </div>
    </div>
  );
};

const Step2: React.FC<{
  onAnswer: (v: boolean) => void;
  isLoading: boolean;
  onBack: () => void;
}> = ({ onAnswer, isLoading, onBack }) => {
  const intl = useIntl();
  return (
    <div className="space-y-4">
      <button onClick={onBack} className="text-blue-500 text-sm">← Volver</button>
      <p className="text-lg font-medium text-gray-700 text-center">
        {intl.formatMessage({ id: 'onboarding.step2.question' })}
      </p>
      <p className="text-sm text-gray-500 text-center">
        {intl.formatMessage({ id: 'onboarding.step2.examples' })}
      </p>
      <div className="grid grid-cols-2 gap-4">
        <button
          onClick={() => onAnswer(true)}
          disabled={isLoading}
          className="py-4 px-6 bg-amber-500 hover:bg-amber-600 text-white rounded-xl font-semibold transition-colors"
        >
          {intl.formatMessage({ id: 'onboarding.step2.yes' })}
        </button>
        <button
          onClick={() => onAnswer(false)}
          disabled={isLoading}
          className="py-4 px-6 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl font-semibold transition-colors"
        >
          {intl.formatMessage({ id: 'onboarding.step2.no' })}
        </button>
      </div>
    </div>
  );
};
```

---

## PARTE C — Wizard 6 pasos (PRIMER_EMPLEO)

Crea `frontend/src/modules/primer-empleo/wizard/`:

```tsx
// frontend/src/modules/primer-empleo/wizard/WizardLayout.tsx
import { Routes, Route } from 'react-router-dom';
import { WizardProgressBar } from './WizardProgressBar';
import { Step1PersonalData } from './steps/Step1PersonalData';
import { Step2Education } from './steps/Step2Education';
import { Step3Skills } from './steps/Step3Skills';
import { Step4Activities } from './steps/Step4Activities';
import { Step5Interests } from './steps/Step5Interests';
import { Step6Preview } from './steps/Step6Preview';

export const WizardLayout: React.FC = () => {
  const steps = [
    { path: 'step/1', label: 'Datos personales' },
    { path: 'step/2', label: 'Educación' },
    { path: 'step/3', label: 'Habilidades' },
    { path: 'step/4', label: 'Actividades' },
    { path: 'step/5', label: 'Intereses' },
    { path: 'step/6', label: 'Mi CV' },
  ];

  return (
    <div className="min-h-screen bg-blue-50">
      <WizardProgressBar steps={steps} />
      <div className="max-w-4xl mx-auto p-4 grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl shadow p-6">
          <Routes>
            <Route path="step/1" element={<Step1PersonalData />} />
            <Route path="step/2" element={<Step2Education />} />
            <Route path="step/3" element={<Step3Skills />} />
            <Route path="step/4" element={<Step4Activities />} />
            <Route path="step/5" element={<Step5Interests />} />
            <Route path="step/6" element={<Step6Preview />} />
          </Routes>
        </div>
        {/* Preview CV en tiempo real (panel derecho) */}
        <div className="hidden lg:block bg-white rounded-2xl shadow p-6">
          <CVLivePreview />
        </div>
      </div>
    </div>
  );
};
```

```tsx
// frontend/src/modules/primer-empleo/wizard/steps/Step3Skills.tsx
// Paso con NLP en tiempo real — envía texto al backend y recibe skills extraídas
import { useState } from 'react';
import { useIntl } from 'react-intl';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { api } from '../../../../services/api';
import { useWizardStore } from '../../../../store/wizardStore';
import { SkillTag } from '../../../../shared/SkillTag';

const schema = z.object({
  free_text: z.string().min(10, 'Cuéntanos un poco más (mínimo 10 caracteres)'),
});

export const Step3Skills: React.FC = () => {
  const intl = useIntl();
  const { answers, setAnswer, extractedSkills, setExtractedSkills } = useWizardStore();
  const [isExtracting, setIsExtracting] = useState(false);
  const { register, handleSubmit, watch } = useForm({ resolver: zodResolver(schema) });

  const freeText = watch('free_text', '');

  // Extracción NLP en tiempo real (debounced 1s)
  const extractSkills = async (text: string) => {
    if (text.length < 15) return;
    setIsExtracting(true);
    try {
      const { data } = await api.post('/api/v1/wizard/extract-skills', {
        user_text: text,
        step: 3,
      });
      setExtractedSkills(data.skills || []);
    } catch { /* silencioso */ }
    finally { setIsExtracting(false); }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-800">
          {intl.formatMessage({ id: 'wizard.step3.title' })}
        </h2>
        <p className="text-gray-500 text-sm mt-1">
          {intl.formatMessage({ id: 'wizard.step3.subtitle' })}
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {intl.formatMessage({ id: 'wizard.step3.question' })}
        </label>
        <textarea
          {...register('free_text')}
          onChange={(e) => {
            register('free_text').onChange(e);
            // Debounce NLP
            clearTimeout((window as any)._skillTimer);
            (window as any)._skillTimer = setTimeout(() => extractSkills(e.target.value), 1000);
          }}
          rows={4}
          placeholder={intl.formatMessage({ id: 'wizard.step3.placeholder' })}
          className="w-full border border-gray-300 rounded-lg p-3 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Skills extraídas en tiempo real */}
      {extractedSkills.length > 0 && (
        <div>
          <p className="text-sm font-medium text-green-700 mb-2">
            ✨ {intl.formatMessage({ id: 'wizard.step3.skills_found' })}
          </p>
          <div className="flex flex-wrap gap-2">
            {extractedSkills.map((skill) => (
              <SkillTag key={skill} label={skill} removable />
            ))}
          </div>
        </div>
      )}

      {isExtracting && (
        <p className="text-sm text-blue-500 animate-pulse">
          {intl.formatMessage({ id: 'wizard.step3.extracting' })}
        </p>
      )}

      <WizardNavigation step={3} onNext={() => { /* guardar y avanzar */ }} />
    </div>
  );
};
```

---

## PARTE D — Dashboard diferenciado (WorkerDashboard)

```tsx
// frontend/src/shared/WorkerDashboard.tsx
import { match } from 'ts-pattern';
import { useWorkerContext } from '../context/WorkerContext';
import { PrimerEmpleoDashboard } from '../modules/primer-empleo/PrimerEmpleoDashboard';
import { ExperienciaDashboard } from '../modules/experiencia/ExperienciaDashboard';
import { OficioDashboard } from '../modules/oficio/OficioDashboard';

export const WorkerDashboard: React.FC = () => {
  const { workerType } = useWorkerContext();

  return match(workerType)
    .with('primer_empleo', () => <PrimerEmpleoDashboard />)
    .with('experiencia',   () => <ExperienciaDashboard />)
    .with('oficio',        () => <OficioDashboard />)
    .otherwise(() => <LoadingSpinner />);
};
```

```tsx
// frontend/src/modules/primer-empleo/PrimerEmpleoDashboard.tsx
import { useIntl } from 'react-intl';
import { Link } from 'react-router-dom';
import { useMatches } from '../../hooks/useMatches';
import { JobMatchCard } from '../../matching/JobMatchCard';
import { CVProgressBar } from './CVProgressBar';
import { OrientacionLaboral } from './OrientacionLaboral';

export const PrimerEmpleoDashboard: React.FC = () => {
  const intl = useIntl();
  const { matches, isLoading } = useMatches();

  return (
    <div className="min-h-screen bg-blue-50">
      <div className="max-w-5xl mx-auto p-4 space-y-6">
        {/* Bienvenida motivadora */}
        <div className="bg-blue-500 text-white rounded-2xl p-6">
          <h1 className="text-2xl font-bold">
            {intl.formatMessage({ id: 'primer_empleo.dashboard.welcome' })}
          </h1>
          <p className="mt-1 opacity-90">
            {intl.formatMessage({ id: 'primer_empleo.dashboard.subtitle' })}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Mi CV */}
          <div className="bg-white rounded-2xl shadow p-6">
            <h2 className="font-bold text-gray-800 mb-4">
              {intl.formatMessage({ id: 'primer_empleo.dashboard.my_cv' })}
            </h2>
            <CVProgressBar />
            <Link
              to="/wizard/step/1"
              className="mt-4 block text-center py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
            >
              {intl.formatMessage({ id: 'primer_empleo.dashboard.continue_wizard' })}
            </Link>
          </div>

          {/* Orientación laboral */}
          <OrientacionLaboral />
        </div>

        {/* Recomendaciones de empleo */}
        <div className="bg-white rounded-2xl shadow p-6">
          <h2 className="font-bold text-gray-800 mb-4">
            {intl.formatMessage({ id: 'primer_empleo.dashboard.recommendations' })}
          </h2>
          {isLoading ? (
            <LoadingSpinner />
          ) : matches.length > 0 ? (
            <div className="space-y-3">
              {matches.slice(0, 5).map((m) => (
                <JobMatchCard key={m.job_id} match={m} workerType="primer_empleo" />
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-4">
              {intl.formatMessage({ id: 'primer_empleo.dashboard.no_matches_yet' })}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
```

---

## PARTE E — Portfolio Visual OFICIO

```tsx
// frontend/src/modules/oficio/portfolio/PortfolioPage.tsx
import { useState } from 'react';
import { useIntl } from 'react-intl';
import { useDropzone } from 'react-dropzone';
import { usePortfolio } from '../../../hooks/usePortfolio';
import { PortfolioCard } from './PortfolioCard';
import { AddEntryModal } from './AddEntryModal';
import { AvailabilityToggle } from './AvailabilityToggle';

export const PortfolioPage: React.FC = () => {
  const intl = useIntl();
  const { entries, isLoading, worker } = usePortfolio();
  const [showAddModal, setShowAddModal] = useState(false);

  return (
    <div className="min-h-screen bg-amber-50">
      {/* Header con disponibilidad */}
      <div className="bg-amber-700 text-white p-6">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">{worker?.display_name}</h1>
            <p className="opacity-80">{worker?.trade_category} · {worker?.district}</p>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-amber-300">{'★'.repeat(Math.round(worker?.avg_rating || 0))}</span>
              <span className="text-sm opacity-80">{worker?.avg_rating?.toFixed(1)}/5.0</span>
            </div>
          </div>
          <div className="flex flex-col items-end gap-2">
            <AvailabilityToggle />
            <a
              href={`/p/${worker?.slug}`}
              target="_blank"
              className="text-xs bg-amber-600 px-3 py-1 rounded-full hover:bg-amber-500"
            >
              {intl.formatMessage({ id: 'oficio.portfolio.view_public' })}
            </a>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto p-4 space-y-4">
        {/* Botones de acción */}
        <div className="flex gap-3">
          <button
            onClick={() => setShowAddModal(true)}
            className="flex-1 py-3 bg-amber-500 text-white rounded-xl font-semibold hover:bg-amber-600"
          >
            {intl.formatMessage({ id: 'oficio.portfolio.add_work' })}
          </button>
          <a
            href="/api/v1/cv/generate"
            className="flex-1 py-3 bg-white border border-amber-500 text-amber-700 rounded-xl font-semibold text-center hover:bg-amber-50"
          >
            {intl.formatMessage({ id: 'oficio.portfolio.generate_cv' })}
          </a>
        </div>

        {/* Grid de trabajos */}
        {isLoading ? (
          <LoadingGrid />
        ) : entries.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {entries.map((entry) => (
              <PortfolioCard key={entry.id} entry={entry} />
            ))}
          </div>
        ) : (
          <EmptyPortfolio onAdd={() => setShowAddModal(true)} />
        )}
      </div>

      {showAddModal && (
        <AddEntryModal onClose={() => setShowAddModal(false)} />
      )}
    </div>
  );
};
```

---

## PARTE F — Panel Admin con Recharts (KPIs de la tesis)

```tsx
// frontend/src/admin/AdminDashboard.tsx
import { useIntl } from 'react-intl';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, Legend,
} from 'recharts';
import { useAdminKPIs } from '../../hooks/useAdminKPIs';

const COLORS = {
  primer_empleo: '#4299e1',
  experiencia:   '#48bb78',
  oficio:        '#ed8936',
};

export const AdminDashboard: React.FC = () => {
  const intl = useIntl();
  const { kpis, isLoading } = useAdminKPIs();

  if (isLoading) return <LoadingSpinner />;

  // Preparar datos para los gráficos
  const vilData = Object.entries(kpis?.vil || {}).map(([type, data]: any) => ({
    type,
    dias: data.avg_days,
    label: type.replace('_', ' '),
  }));

  const tfData = Object.entries(kpis?.tf || {}).map(([type, data]: any) => ({
    type,
    porcentaje: data.tasa_percent,
  }));

  const tccData = Object.entries(kpis?.tcc || {}).map(([type, data]: any) => ({
    type,
    porcentaje: data.tcc_percent,
  }));

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">
        {intl.formatMessage({ id: 'admin.dashboard.title' })}
      </h1>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <KPICard
          label={intl.formatMessage({ id: 'admin.kpi.ivm' })}
          value={`${kpis?.ivm?.ivm_percent?.toFixed(1)}%`}
          subtitle={`${kpis?.ivm?.active_listings} listados activos`}
          color="amber"
        />
        <KPICard
          label={intl.formatMessage({ id: 'admin.kpi.workers_total' })}
          value={Object.values(kpis?.tf || {}).reduce((a: any, b: any) => a + b.total, 0)}
          subtitle="Trabajadores registrados"
          color="blue"
        />
        <KPICard
          label={intl.formatMessage({ id: 'admin.kpi.formalization' })}
          value={`${Object.values(kpis?.tf || {}).reduce((a: any, b: any) => a + b.tasa_percent, 0) / 3}%`}
          subtitle="Tasa promedio de formalización"
          color="green"
        />
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* VIL — Velocidad de Inserción Laboral */}
        <div className="bg-white rounded-2xl shadow p-6">
          <h3 className="font-bold text-gray-700 mb-4">
            {intl.formatMessage({ id: 'admin.kpi.vil.title' })}
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={vilData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" tick={{ fontSize: 11 }} />
              <YAxis unit=" días" tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v: any) => [`${v} días`, 'Promedio']} />
              <Bar dataKey="dias" fill="#4299e1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* TF — Tasa de Formalización */}
        <div className="bg-white rounded-2xl shadow p-6">
          <h3 className="font-bold text-gray-700 mb-4">
            {intl.formatMessage({ id: 'admin.kpi.tf.title' })}
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={tfData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="type" tick={{ fontSize: 11 }} />
              <YAxis unit="%" tick={{ fontSize: 11 }} domain={[0, 100]} />
              <Tooltip formatter={(v: any) => [`${v}%`, 'Formalización']} />
              <Bar dataKey="porcentaje" fill="#48bb78" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* TCC — Tasa Completitud CV */}
        <div className="bg-white rounded-2xl shadow p-6">
          <h3 className="font-bold text-gray-700 mb-4">
            {intl.formatMessage({ id: 'admin.kpi.tcc.title' })}
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={tccData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="type" tick={{ fontSize: 11 }} />
              <YAxis unit="%" tick={{ fontSize: 11 }} domain={[0, 100]} />
              <Tooltip formatter={(v: any) => [`${v}%`, 'Completitud']} />
              <Bar dataKey="porcentaje" fill="#ed8936" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Modelo ML — F1 score */}
        <ModelMetricsChart />
      </div>
    </div>
  );
};
```

---

## PARTE G — i18n: claves obligatorias

Crea `frontend/src/i18n/es-PE.json` con TODAS las claves usadas:

```json
{
  "onboarding.title": "Bienvenido al Sistema de Empleo de Junín",
  "onboarding.subtitle": "Te ayudaremos a encontrar el trabajo que buscas",
  "onboarding.step1.question": "¿Estás buscando tu primer empleo?",
  "onboarding.step1.yes": "Sí, es mi primer empleo",
  "onboarding.step1.no": "No, ya tengo experiencia",
  "onboarding.step2.question": "¿Trabajas en un oficio?",
  "onboarding.step2.examples": "(electricista, gasfitero, carpintero, albañil, etc.)",
  "onboarding.step2.yes": "Sí, soy trabajador de oficio",
  "onboarding.step2.no": "No, trabajo en otro rubro",
  "wizard.step3.title": "¿Qué sabes hacer bien?",
  "wizard.step3.subtitle": "Cuéntanos con tus propias palabras",
  "wizard.step3.question": "Describe lo que haces bien o lo que te gusta hacer",
  "wizard.step3.placeholder": "Ejemplo: Soy puntual, ayudo en la carpintería de mi papá, me gusta organizar cosas...",
  "wizard.step3.skills_found": "Habilidades que encontramos en lo que escribiste:",
  "wizard.step3.extracting": "Analizando tus habilidades...",
  "primer_empleo.dashboard.welcome": "¡Hola! Estás dando tu primer paso 👋",
  "primer_empleo.dashboard.subtitle": "Te ayudamos a construir tu primer CV y encontrar trabajo",
  "primer_empleo.dashboard.my_cv": "Mi CV",
  "primer_empleo.dashboard.continue_wizard": "Continuar mi CV",
  "primer_empleo.dashboard.recommendations": "Empleos que te pueden interesar",
  "primer_empleo.dashboard.no_matches_yet": "Completa tu perfil para ver recomendaciones",
  "oficio.portfolio.add_work": "+ Agregar trabajo realizado",
  "oficio.portfolio.generate_cv": "Generar mi CV",
  "oficio.portfolio.view_public": "Ver mi perfil público",
  "admin.dashboard.title": "Panel DRTPE-Junín — Indicadores del Sistema",
  "admin.kpi.ivm": "Visibilidad Marketplace",
  "admin.kpi.workers_total": "Trabajadores Registrados",
  "admin.kpi.formalization": "Tasa de Formalización",
  "admin.kpi.vil.title": "VIL — Días hasta primer contrato",
  "admin.kpi.tf.title": "Tasa de Formalización por tipo",
  "admin.kpi.tcc.title": "Tasa de Completitud de CV",
  "worker.primer_empleo.profile.title": "Mi perfil — Primer empleo",
  "worker.experiencia.profile.title": "Mi perfil profesional",
  "worker.oficio.profile.title": "Mi portfolio de oficio"
}
```

---

## ENTREGABLES DE ESTA INSTRUCCIÓN

- `frontend/src/guards/` (WorkerTypeGuard, AuthGuard, AdminGuard)
- `frontend/src/App.tsx` — rutas protegidas
- `frontend/src/onboarding/OnboardingPage.tsx`
- `frontend/src/modules/primer-empleo/wizard/` (WizardLayout + 6 steps)
- `frontend/src/shared/WorkerDashboard.tsx`
- `frontend/src/modules/primer-empleo/PrimerEmpleoDashboard.tsx`
- `frontend/src/modules/experiencia/ExperienciaDashboard.tsx`
- `frontend/src/modules/oficio/OficioDashboard.tsx`
- `frontend/src/modules/oficio/portfolio/PortfolioPage.tsx`
- `frontend/src/admin/AdminDashboard.tsx`
- `frontend/src/i18n/es-PE.json` — todas las claves i18n

**Verificar:**
```bash
cd frontend
npm run build          # ✅ sin errores TypeScript
npm run lint           # ✅ sin errores ESLint
# No hay strings en español hardcodeados en los componentes
grep -rn '"[A-ZÁÉÍÓÚ]' src/modules/ src/onboarding/ | grep -v i18n | grep -v ".json"
```

---

**Cuando termines, el agente `devops-engineer` recibirá la instrucción 5
para implementar el CI/CD completo con GitHub Actions y configurar GCS real.**
