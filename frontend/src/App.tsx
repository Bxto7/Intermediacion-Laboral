import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthGuard } from './guards/AuthGuard'
import { WorkerTypeGuard } from './guards/WorkerTypeGuard'
import { AdminGuard } from './guards/AdminGuard'
import { AppShell } from './shared/AppShell'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { OnboardingPage } from './onboarding/OnboardingPage'
import { WorkerDashboard } from './shared/WorkerDashboard'
import { EmployerDashboard } from './employer/EmployerDashboard'
import { WizardLayout } from './modules/primer-empleo/wizard/WizardLayout'
import { PortfolioPage } from './modules/oficio/portfolio/PortfolioPage'
import { MarketplacePage } from './modules/oficio/marketplace/MarketplacePage'
import { MatchesPage } from './matching/MatchesPage'
import { AdminLayout } from './admin/AdminLayout'
import { PublicPortfolioPage } from './pages/PublicPortfolioPage'
import { ApplicationsPage } from './pages/ApplicationsPage'
import { EconomicSurveyPage } from './pages/EconomicSurveyPage'
import { ServiceSearchPage } from './pages/ServiceSearchPage'

export default function App() {
  return (
    <Routes>
      {/* ── Rutas públicas (sin shell) ── */}
      <Route path="/login"    element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/p/:slug"  element={<PublicPortfolioPage />} />
      <Route path="/servicios" element={<ServiceSearchPage />} />

      {/* ── Onboarding (sin shell, flujo dedicado) ── */}
      <Route path="/onboarding" element={<AuthGuard><OnboardingPage /></AuthGuard>} />

      {/* ── AppShell — todas las rutas autenticadas ── */}
      <Route element={<AuthGuard><AppShell /></AuthGuard>}>

        {/* Dashboard diferenciado por tipo de worker */}
        <Route path="/dashboard" element={<WorkerDashboard />} />

        {/* Employer */}
        <Route path="/employer/dashboard" element={<EmployerDashboard />} />

        {/* Wizard — solo PRIMER_EMPLEO */}
        <Route path="/wizard/*" element={
          <WorkerTypeGuard allowedTypes={['primer_empleo']}>
            <WizardLayout />
          </WorkerTypeGuard>
        } />

        {/* Portfolio — solo OFICIO */}
        <Route path="/oficio/portfolio" element={
          <WorkerTypeGuard allowedTypes={['oficio']}>
            <PortfolioPage />
          </WorkerTypeGuard>
        } />

        {/* Marketplace — solo OFICIO */}
        <Route path="/marketplace/*" element={
          <WorkerTypeGuard allowedTypes={['oficio']}>
            <MarketplacePage />
          </WorkerTypeGuard>
        } />

        {/* Postulaciones — todos */}
        <Route path="/applications" element={<ApplicationsPage />} />

        {/* Encuesta económica — todos */}
        <Route path="/survey/economic" element={<EconomicSurveyPage />} />

        {/* Matching — todos */}
        <Route path="/matches" element={<MatchesPage />} />

        {/* Admin */}
        <Route path="/admin/*" element={
          <AdminGuard>
            <AdminLayout />
          </AdminGuard>
        } />
      </Route>

      {/* Fallback */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
