import { match } from 'ts-pattern'
import { Navigate } from 'react-router-dom'
import { useWorkerContext } from '../context/WorkerContext'
import { useAuthContext } from '../context/AuthContext'
import { PrimerEmpleoDashboard } from '../modules/primer-empleo/PrimerEmpleoDashboard'
import { ExperienciaDashboard } from '../modules/experiencia/ExperienciaDashboard'
import { OficioDashboard } from '../modules/oficio/OficioDashboard'
import { LoadingSpinner } from './LoadingSpinner'

export const WorkerDashboard: React.FC = () => {
  const { user } = useAuthContext()
  const { workerType, isLoading } = useWorkerContext()

  if (user?.role === 'employer') return <Navigate to="/employer/dashboard" replace />
  if (user?.role === 'admin') return <Navigate to="/admin" replace />
  if (isLoading) return <LoadingSpinner />
  if (!workerType) return <Navigate to="/onboarding" replace />

  return match(workerType)
    .with('primer_empleo', () => <PrimerEmpleoDashboard />)
    .with('experiencia',   () => <ExperienciaDashboard />)
    .with('oficio',        () => <OficioDashboard />)
    .otherwise(() => null)
}
