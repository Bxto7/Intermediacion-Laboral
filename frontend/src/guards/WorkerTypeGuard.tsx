import { Navigate } from 'react-router-dom'
import { useWorkerContext } from '../context/WorkerContext'
import { LoadingSpinner } from '../shared/LoadingSpinner'

type WType = 'primer_empleo' | 'experiencia' | 'oficio'

interface Props {
  allowedTypes: WType[]
  children: React.ReactNode
  redirectTo?: string
}

export const WorkerTypeGuard: React.FC<Props> = ({ allowedTypes, children, redirectTo = '/dashboard' }) => {
  const { workerType, isLoading } = useWorkerContext()
  if (isLoading) return <LoadingSpinner fullScreen />
  if (!workerType) return <Navigate to="/onboarding" replace />
  if (!allowedTypes.includes(workerType as WType)) return <Navigate to={redirectTo} replace />
  return <>{children}</>
}
