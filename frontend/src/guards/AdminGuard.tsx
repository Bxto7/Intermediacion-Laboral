import { Navigate } from 'react-router-dom'
import { useAuthContext } from '../context/AuthContext'

export const AdminGuard: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuthContext()
  if (user?.role !== 'admin') return <Navigate to="/dashboard" replace />
  return <>{children}</>
}
