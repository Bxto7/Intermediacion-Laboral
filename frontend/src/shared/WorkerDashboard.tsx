import { match } from 'ts-pattern'
import { Navigate } from 'react-router-dom'
import { useWorkerContext } from '../context/WorkerContext'
import { useAuthContext } from '../context/AuthContext'
import { PrimerEmpleoDashboard } from '../modules/primer-empleo/PrimerEmpleoDashboard'
import { ExperienciaDashboard } from '../modules/experiencia/ExperienciaDashboard'
import { OficioDashboard } from '../modules/oficio/OficioDashboard'
import { LoadingSpinner } from './LoadingSpinner'
import { NavBar } from './NavBar'

export const WorkerDashboard: React.FC = () => {
  const { user } = useAuthContext()
  const { workerType, isLoading } = useWorkerContext()

  // Los empleadores tienen su propio dashboard
  if (user?.role === 'employer') {
    return <Navigate to="/employer/dashboard" replace />
  }

  // Los administradores van al panel admin
  if (user?.role === 'admin') {
    return <Navigate to="/admin" replace />
  }

  if (isLoading) {
    return <LoadingSpinner fullScreen />
  }

  if (!workerType) {
    return <Navigate to="/onboarding" replace />
  }

  const dashboard = match(workerType)
    .with('primer_empleo', () => <PrimerEmpleoDashboard />)
    .with('experiencia', () => <ExperienciaDashboard />)
    .with('oficio', () => <OficioDashboard />)
    .otherwise(() => null)

  return (
    <>
      <NavBar />
      {dashboard}
    </>
  )
}

