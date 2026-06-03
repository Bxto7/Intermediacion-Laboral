import { Link } from 'react-router-dom'
import { MessageCircle, Users } from 'lucide-react'

export const EmployerMessagesPage: React.FC = () => {
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-bold" style={{ color: 'var(--ink-strong)', letterSpacing: '-0.02em' }}>
          Mensajes
        </h1>
        <p className="text-sm mt-0.5" style={{ color: 'var(--ink-muted)' }}>
          Conversaciones con tus candidatos
        </p>
      </div>

      <div className="card-warm p-12 text-center space-y-4">
        <div className="w-16 h-16 mx-auto rounded-2xl flex items-center justify-center" style={{ background: 'rgba(42,29,20,0.05)', border: '1px solid var(--line)' }}>
          <MessageCircle size={28} style={{ color: 'var(--ink-muted)' }} strokeWidth={1.5} />
        </div>
        <div>
          <p className="font-semibold text-sm" style={{ color: 'var(--ink-warm)' }}>Aún no tienes conversaciones</p>
          <p className="text-xs mt-1 max-w-md mx-auto" style={{ color: 'var(--ink-muted)' }}>
            Cuando contactes a un candidato desde la gestión de postulantes, la conversación aparecerá aquí.
          </p>
        </div>
        <Link to="/employer/candidates" className="btn-primary text-sm px-6 py-2.5 inline-flex items-center gap-2">
          <Users size={14} /> Ver candidatos
        </Link>
      </div>
    </div>
  )
}
