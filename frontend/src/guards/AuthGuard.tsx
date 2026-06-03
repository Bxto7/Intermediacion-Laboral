import { Navigate } from 'react-router-dom'
import { useAuthContext } from '../context/AuthContext'
import { LoadingSpinner } from '../shared/LoadingSpinner'

export const AuthGuard: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuthContext()
  if (isLoading) return <LoadingSpinner fullScreen />
  if (!isAuthenticated) return <Navigate to="/" replace />
  return <>{children}</>
}
