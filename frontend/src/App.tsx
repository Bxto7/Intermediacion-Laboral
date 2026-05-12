import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthGuard } from './guards/AuthGuard'
import { WorkerTypeGuard } from './guards/WorkerTypeGuard'
import { AdminGuard } from './guards/AdminGuard'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { OnboardingPage } from './onboarding/OnboardingPage'
import { WorkerDashboard } from './shared/WorkerDashboard'
import { EmployerDashboard } from './employer/EmployerDashboard'
import { WizardLayout } from './modules/primer-empleo/wizard/WizardLayout'
import { PortfolioPage } from './modules/oficio/portfolio/PortfolioPage'
import { MatchesPage } from './matching/MatchesPage'
import { AdminLayout } from './admin/AdminLayout'
import { PublicPortfolioPage } from './pages/PublicPortfolioPage'
import { NavBar } from './shared/NavBar'

const MarketplacePlaceholder: React.FC = () => (
  <div className="min-h-screen bg-warm-50">
    <NavBar />
    <div className="flex items-center justify-center h-[60vh]">
      <div className="text-center space-y-3">
        <div className="w-14 h-14 mx-auto rounded-2xl bg-warm-100 border border-warm-200 flex items-center justify-center">
          <svg className="w-7 h-7 text-bark-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        </div>
        <h2 className="text-lg font-bold text-bark-900">Marketplace de Servicios</h2>
        <p className="text-bark-400 text-sm">Disponible en Sprint 5</p>
      </div>
    </div>
  </div>
)

export default function App() {
  return (
    <Routes>
      {/* Públicas */}
      <Route path="/login"    element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/p/:slug"  element={<PublicPortfolioPage />} />

      {/* Onboarding */}
      <Route path="/onboarding" element={<AuthGuard><OnboardingPage /></AuthGuard>} />

      {/* Dashboard diferenciado por tipo + empleadores */}
      <Route path="/dashboard" element={<AuthGuard><WorkerDashboard /></AuthGuard>} />
      <Route path="/employer/dashboard" element={<AuthGuard><EmployerDashboard /></AuthGuard>} />

      {/* Wizard — solo PRIMER_EMPLEO */}
      <Route path="/wizard/*" element={
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
      <Route path="/marketplace/*" element={
        <AuthGuard>
          <WorkerTypeGuard allowedTypes={['oficio']}>
            <MarketplacePlaceholder />
          </WorkerTypeGuard>
        </AuthGuard>
      } />

      {/* Matching — todos los tipos */}
      <Route path="/matches" element={<AuthGuard><MatchesPage /></AuthGuard>} />

      {/* Admin */}
      <Route path="/admin/*" element={
        <AuthGuard>
          <AdminGuard>
            <AdminLayout />
          </AdminGuard>
        </AuthGuard>
      } />

      {/* Fallback */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
