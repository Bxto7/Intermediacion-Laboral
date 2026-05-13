import { useState } from 'react'
import { MessageCircle, Shield, X, Send, CheckCircle } from 'lucide-react'
import apiClient from '../api/client'

interface Props {
  listingId?: string
  workerUsername?: string
  workerName: string
  listingTitle: string
  onClose: () => void
}

export const ContactModal: React.FC<Props> = ({ listingId, workerUsername, workerName, listingTitle, onClose }) => {
  const [message, setMessage] = useState('')
  const [sending, setSending] = useState(false)
  const [sent, setSent] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (message.trim().length < 10) {
      setError('El mensaje debe tener al menos 10 caracteres')
      return
    }
    setSending(true)
    try {
      const endpoint = listingId
        ? `/marketplace/listings/${listingId}/contact`
        : `/portfolio/${workerUsername}/contact`
      await apiClient.post(endpoint, { message: message.trim() })
      setSent(true)
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(detail || 'No se pudo enviar el mensaje. Intenta de nuevo.')
    } finally {
      setSending(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4 modal-backdrop"
      style={{ background: 'rgba(26,15,10,0.55)', backdropFilter: 'blur(8px)' }}
    >
      <div
        className="modal-panel w-full max-w-md overflow-hidden"
        style={{
          background: 'var(--bg-elevated)',
          borderRadius: '24px',
          boxShadow: '0 50px 100px -30px rgba(0,0,0,0.4)',
          border: '1px solid var(--line)',
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 pt-6 pb-4" style={{ borderBottom: '1px solid var(--line)' }}>
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-2xl flex items-center justify-center flex-shrink-0"
              style={{ background: 'var(--terra-100)' }}
            >
              <MessageCircle size={18} style={{ color: 'var(--terra-500)' }} />
            </div>
            <div>
              <h2 className="font-bold text-sm leading-tight" style={{ color: 'var(--ink-strong)' }}>
                Contactar a {workerName || 'el trabajador'}
              </h2>
              <p className="text-xs truncate max-w-[200px]" style={{ color: 'var(--ink-muted)' }}>{listingTitle}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full flex items-center justify-center transition-colors"
            style={{ color: 'var(--ink-muted)' }}
            onMouseEnter={e => (e.currentTarget.style.background = 'rgba(61,40,24,0.06)')}
            onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
          >
            <X size={16} />
          </button>
        </div>

        {sent ? (
          <div className="px-6 py-10 text-center space-y-4">
            <div
              className="w-16 h-16 rounded-full mx-auto flex items-center justify-center"
              style={{ background: 'var(--olive-100)' }}
            >
              <CheckCircle size={28} style={{ color: 'var(--olive-deep)' }} />
            </div>
            <div>
              <h3 className="font-bold text-base" style={{ color: 'var(--ink-strong)' }}>Mensaje enviado</h3>
              <p className="text-sm mt-1" style={{ color: 'var(--ink-muted)' }}>
                El trabajador recibirá tu solicitud y podrá responderte.
              </p>
            </div>
            <button onClick={onClose} className="btn-primary w-full py-3">
              Cerrar
            </button>
          </div>
        ) : (
          <form onSubmit={submit} className="px-6 py-5 space-y-4">
            <div>
              <label className="block text-xs font-semibold mb-1.5" style={{ color: 'var(--ink-strong)' }}>
                ¿Qué necesitas?
              </label>
              <textarea
                value={message}
                onChange={e => setMessage(e.target.value)}
                placeholder={`Ej: "Necesito que instales tomacorrientes en mi casa de El Tambo. Son 3 habitaciones. ¿Cuándo podrías venir?"`}
                rows={5}
                maxLength={500}
                className="w-full rounded-xl px-4 py-3 text-sm resize-none transition-all duration-150 focus:outline-none"
                style={{
                  border: '1px solid #d6c5a8',
                  background: 'var(--bg-soft)',
                  color: 'var(--ink-strong)',
                }}
                onFocus={e => { e.currentTarget.style.borderColor = 'var(--terra-500)'; e.currentTarget.style.boxShadow = '0 0 0 3px rgba(194,86,46,0.14)' }}
                onBlur={e => { e.currentTarget.style.borderColor = '#d6c5a8'; e.currentTarget.style.boxShadow = 'none' }}
              />
              <p className="text-right text-[11px] mt-0.5" style={{ color: 'var(--ink-muted)' }}>{message.length}/500</p>
            </div>

            <div
              className="rounded-xl px-4 py-3 flex items-start gap-2.5"
              style={{ background: 'var(--blue-100)', border: '1px solid rgba(45,90,130,0.15)' }}
            >
              <Shield size={15} className="flex-shrink-0 mt-0.5" style={{ color: 'var(--blue)' }} />
              <p className="text-xs leading-relaxed" style={{ color: 'var(--blue)' }}>
                Plataforma oficial <strong>Linku · DRTPE-Junín</strong>. Tus datos están protegidos y la identidad del trabajador está verificada.
              </p>
            </div>

            {error && (
              <p
                className="text-xs rounded-xl px-4 py-2.5"
                style={{ background: 'rgba(168,63,63,0.08)', color: 'var(--error)', border: '1px solid rgba(168,63,63,0.18)' }}
              >
                {error}
              </p>
            )}

            <div className="flex gap-3 pt-1">
              <button type="button" onClick={onClose} className="btn-secondary flex-1 py-3">
                Cancelar
              </button>
              <button type="submit" disabled={sending} className="btn-primary flex-1 py-3 gap-2">
                {sending ? (
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                  </svg>
                ) : <Send size={14} />}
                {sending ? 'Enviando...' : 'Enviar mensaje'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
