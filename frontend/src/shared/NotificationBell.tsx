import { useState } from 'react'
import { Bell, Sparkles, FileText, MessageCircle, FileCheck, X } from 'lucide-react'
import { useAuthContext } from '../context/AuthContext'
import { useNotifications } from '../hooks/useNotifications'

const TYPE_ICON: Record<string, React.ReactNode> = {
  new_match:          <Sparkles  size={14} style={{ color: 'var(--terra-500)' }} />,
  application_update: <FileText  size={14} style={{ color: 'var(--gold)' }} />,
  alert_job:          <Bell      size={14} style={{ color: 'var(--olive-deep)' }} />,
  message:            <MessageCircle size={14} style={{ color: 'var(--blue)' }} />,
  cv_ready:           <FileCheck size={14} style={{ color: 'var(--olive-deep)' }} />,
}

export const NotificationBell: React.FC = () => {
  const { user } = useAuthContext()
  const { notifications, unreadCount, connected, markAllRead, dismiss } = useNotifications(user?.id ?? null)
  const [open, setOpen] = useState(false)

  const toggle = () => {
    setOpen(p => !p)
    if (!open && unreadCount > 0) markAllRead()
  }

  return (
    <div className="relative">
      <button
        onClick={toggle}
        className="relative w-9 h-9 rounded-xl flex items-center justify-center transition-colors"
        style={{ color: 'var(--ink-warm)' }}
        onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.background = 'rgba(42,29,20,0.07)' }}
        onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.background = 'transparent' }}
        aria-label="Notificaciones"
      >
        <Bell size={18} strokeWidth={1.8} />
        {unreadCount > 0 && (
          <span
            className="absolute -top-0.5 -right-0.5 w-4 h-4 text-white text-[10px] font-bold rounded-full flex items-center justify-center leading-none"
            style={{ background: 'var(--terra-500)' }}
          >
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
        {connected && (
          <span className="absolute bottom-1 right-1 w-1.5 h-1.5 rounded-full" style={{ background: 'var(--olive)' }} title="Conectado" />
        )}
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div
            className="absolute right-0 top-11 z-50 w-80 overflow-hidden"
            style={{
              background: 'var(--bg-elevated)',
              borderRadius: '16px',
              boxShadow: '0 20px 60px -10px rgba(0,0,0,0.25)',
              border: '1px solid var(--line)',
            }}
          >
            <div className="flex items-center justify-between px-4 py-3" style={{ borderBottom: '1px solid var(--line)' }}>
              <h3 className="font-bold text-sm" style={{ color: 'var(--ink-strong)' }}>Notificaciones</h3>
              {notifications.length > 0 && (
                <button
                  onClick={markAllRead}
                  className="text-xs font-medium transition-colors"
                  style={{ color: 'var(--terra-500)' }}
                >
                  Marcar todo leído
                </button>
              )}
            </div>

            <div className="max-h-80 overflow-y-auto" style={{ borderBottom: '1px solid var(--line)' }}>
              {notifications.length === 0 ? (
                <div className="py-10 text-center">
                  <div className="w-10 h-10 rounded-2xl mx-auto mb-2 flex items-center justify-center" style={{ background: 'rgba(42,29,20,0.06)' }}>
                    <Bell size={18} style={{ color: 'var(--ink-muted)' }} strokeWidth={1.5} />
                  </div>
                  <p className="text-xs" style={{ color: 'var(--ink-muted)' }}>No tienes notificaciones</p>
                </div>
              ) : (
                notifications.map(n => (
                  <div
                    key={n.id}
                    className="flex items-start gap-3 px-4 py-3 transition-colors"
                    style={{
                      background: n.read ? 'transparent' : 'rgba(184,68,42,0.04)',
                      borderBottom: '1px solid var(--line)',
                    }}
                  >
                    <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5" style={{ background: 'var(--bg-soft)' }}>
                      {TYPE_ICON[n.type] ?? <Bell size={14} style={{ color: 'var(--ink-muted)' }} />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold leading-tight" style={{ color: 'var(--ink-strong)' }}>{n.title}</p>
                      <p className="text-xs mt-0.5 line-clamp-2" style={{ color: 'var(--ink-muted)' }}>{n.body}</p>
                      <p className="text-[10px] mt-1" style={{ color: 'var(--ink-muted)' }}>
                        {new Date(n.received_at).toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                    <button
                      onClick={() => dismiss(n.id)}
                      className="flex-shrink-0 mt-0.5 transition-colors"
                      style={{ color: 'var(--ink-muted)' }}
                    >
                      <X size={13} />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
