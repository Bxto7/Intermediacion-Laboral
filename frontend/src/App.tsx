import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthGuard } from './guards/AuthGuard'
import { WorkerTypeGuard } from './guards/WorkerTypeGuard'
import { AdminGuard } from './guards/AdminGuard'
import { AppShell } from './shared/AppShell'
import { LoadingSpinner } from './shared/LoadingSpinner'

// ── Eagerly loaded (always needed for auth flow) ────────────────────────────
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'

// ── Lazy loaded (split at route level) ──────────────────────────────────────
const LandingPage         = lazy(() => import('./pages/LandingPage').then(m => ({ default: m.LandingPage })))
const OnboardingPage      = lazy(() => import('./onboarding/OnboardingPage').then(m => ({ default: m.OnboardingPage })))
const WorkerDashboard     = lazy(() => import('./shared/WorkerDashboard').then(m => ({ default: m.WorkerDashboard })))
const EmployerDashboard   = lazy(() => import('./employer/EmployerDashboard').then(m => ({ default: m.EmployerDashboard })))
const WizardLayout        = lazy(() => import('./modules/primer-empleo/wizard/WizardLayout').then(m => ({ default: m.WizardLayout })))
const PortfolioPage       = lazy(() => import('./modules/oficio/portfolio/PortfolioPage').then(m => ({ default: m.PortfolioPage })))
const MarketplacePage     = lazy(() => import('./modules/oficio/marketplace/MarketplacePage').then(m => ({ default: m.MarketplacePage })))
const MatchesPage         = lazy(() => import('./matching/MatchesPage').then(m => ({ default: m.MatchesPage })))
const AdminLayout         = lazy(() => import('./admin/AdminLayout').then(m => ({ default: m.AdminLayout })))
const PublicPortfolioPage = lazy(() => import('./pages/PublicPortfolioPage').then(m => ({ default: m.PublicPortfolioPage })))
const ApplicationsPage    = lazy(() => import('./pages/ApplicationsPage').then(m => ({ default: m.ApplicationsPage })))
const EconomicSurveyPage  = lazy(() => import('./pages/EconomicSurveyPage').then(m => ({ default: m.EconomicSurveyPage })))
const ServiceSearchPage   = lazy(() => import('./pages/ServiceSearchPage').then(m => ({ default: m.ServiceSearchPage })))
const SettingsPage        = lazy(() => import('./pages/SettingsPage').then(m => ({ default: m.SettingsPage })))
const EmployerPublishPage    = lazy(() => import('./pages/employer/EmployerPublishPage').then(m => ({ default: m.EmployerPublishPage })))
const EmployerCandidatesPage = lazy(() => import('./pages/employer/EmployerCandidatesPage').then(m => ({ default: m.EmployerCandidatesPage })))
const EmployerMessagesPage   = lazy(() => import('./pages/employer/EmployerMessagesPage').then(m => ({ default: m.EmployerMessagesPage })))

const PageFallback = () => <LoadingSpinner fullScreen />

export default function App() {
  return (
    <Routes>
      {/* ── Rutas públicas (sin shell) ── */}
      <Route path="/login"    element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/p/:slug"  element={<Suspense fallback={<PageFallback />}><PublicPortfolioPage /></Suspense>} />
      <Route path="/servicios" element={<Suspense fallback={<PageFallback />}><ServiceSearchPage /></Suspense>} />

      {/* ── Onboarding (sin shell, flujo dedicado) ── */}
      <Route path="/onboarding" element={
        <AuthGuard>
          <Suspense fallback={<PageFallback />}>
            <OnboardingPage />
          </Suspense>
        </AuthGuard>
      } />

      {/* ── AppShell — todas las rutas autenticadas ── */}
      <Route element={<AuthGuard><AppShell /></AuthGuard>}>

        <Route path="/dashboard" element={
          <Suspense fallback={<PageFallback />}><WorkerDashboard /></Suspense>
        } />

        <Route path="/settings" element={
          <Suspense fallback={<PageFallback />}><SettingsPage /></Suspense>
        } />

        {/* Employer */}
        <Route path="/employer/dashboard" element={
          <Suspense fallback={<PageFallback />}><EmployerDashboard /></Suspense>
        } />
        <Route path="/employer/publish" element={
          <Suspense fallback={<PageFallback />}><EmployerPublishPage /></Suspense>
        } />
        <Route path="/employer/candidates" element={
          <Suspense fallback={<PageFallback />}><EmployerCandidatesPage /></Suspense>
        } />
        <Route path="/employer/messages" element={
          <Suspense fallback={<PageFallback />}><EmployerMessagesPage /></Suspense>
        } />

        {/* Wizard — solo PRIMER_EMPLEO */}
        <Route path="/wizard/*" element={
          <WorkerTypeGuard allowedTypes={['primer_empleo']}>
            <Suspense fallback={<PageFallback />}><WizardLayout /></Suspense>
          </WorkerTypeGuard>
        } />

        {/* Portfolio — solo OFICIO */}
        <Route path="/oficio/portfolio" element={
          <WorkerTypeGuard allowedTypes={['oficio']}>
            <Suspense fallback={<PageFallback />}><PortfolioPage /></Suspense>
          </WorkerTypeGuard>
        } />

        {/* Marketplace — accesible a todos los usuarios autenticados */}
        <Route path="/marketplace/*" element={
          <Suspense fallback={<PageFallback />}><MarketplacePage /></Suspense>
        } />

        <Route path="/applications" element={
          <Suspense fallback={<PageFallback />}><ApplicationsPage /></Suspense>
        } />
        <Route path="/survey/economic" element={
          <Suspense fallback={<PageFallback />}><EconomicSurveyPage /></Suspense>
        } />
        <Route path="/matches" element={
          <Suspense fallback={<PageFallback />}><MatchesPage /></Suspense>
        } />

        {/* Admin */}
        <Route path="/admin/*" element={
          <AdminGuard>
            <Suspense fallback={<PageFallback />}><AdminLayout /></Suspense>
          </AdminGuard>
        } />
      </Route>

      {/* Ruta raíz → landing pública */}
      <Route path="/" element={<Suspense fallback={<PageFallback />}><LandingPage /></Suspense>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
