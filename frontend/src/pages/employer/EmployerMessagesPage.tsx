import { useState } from 'react'
import { MessageCircle, Send, Zap } from 'lucide-react'

interface MockConversation {
  id: string
  name: string
  jobTitle: string
  lastMsg: string
  time: string
  unread: boolean
  avatar: string
}

interface MockMessage {
  id: string
  from: 'worker' | 'employer'
  text: string
  time: string
}

const MOCK_CONVOS: MockConversation[] = [
  { id: 'c1', name: 'Ana Torres',   jobTitle: 'Electricista residencial', lastMsg: 'Buenos días, estoy interesada en la oferta.', time: 'Hace 2h',  unread: true,  avatar: 'AT' },
  { id: 'c2', name: 'Carlos Quispe', jobTitle: 'Gasfitero',               lastMsg: '¿Cuál es el horario de trabajo?',             time: 'Hace 5h',  unread: true,  avatar: 'CQ' },
  { id: 'c3', name: 'María Huanca', jobTitle: 'Electricista residencial', lastMsg: 'Perfecto, nos vemos el lunes.',               time: 'Ayer',     unread: false, avatar: 'MH' },
  { id: 'c4', name: 'Juan Ríos',    jobTitle: 'Carpintero',               lastMsg: '¿Cuándo podríamos hacer la entrevista?',     time: 'Hace 3d',  unread: false, avatar: 'JR' },
]

const MOCK_MSGS: Record<string, MockMessage[]> = {
  c1: [
    { id: 'm1', from: 'worker',   text: 'Buenos días, estoy interesada en la oferta.',                                     time: '10:15' },
    { id: 'm2', from: 'employer', text: 'Buenos días Ana, muchas gracias por tu interés.',                                 time: '10:30' },
    { id: 'm3', from: 'worker',   text: 'Tengo 3 años de experiencia como asistente eléctrica. ¿Podríamos coordinar?',    time: '10:32' },
  ],
  c2: [
    { id: 'm1', from: 'worker',   text: '¿Cuál es el horario de trabajo?',                time: '08:00' },
    { id: 'm2', from: 'employer', text: 'El horario es de lunes a viernes, 8am a 5pm.',   time: '09:15' },
  ],
  c3: [
    { id: 'm1', from: 'worker',   text: '¿Sigue disponible la oferta?',                  time: 'Lun 09:00' },
    { id: 'm2', from: 'employer', text: 'Sí, la oferta sigue activa.',                   time: 'Lun 10:00' },
    { id: 'm3', from: 'worker',   text: 'Perfecto, nos vemos el lunes.',                 time: 'Lun 10:05' },
  ],
  c4: [
    { id: 'm1', from: 'worker',   text: '¿Cuándo podríamos hacer la entrevista?',        time: 'Mar 14:00' },
  ],
}

export const EmployerMessagesPage: React.FC = () => {
  const [selected, setSelected] = useState<string | null>('c1')
  const [reply, setReply] = useState('')
  const [msgs, setMsgs] = useState(MOCK_MSGS)

  const convo = MOCK_CONVOS.find(c => c.id === selected)
  const thread = selected ? (msgs[selected] ?? []) : []

  const sendMsg = (e: React.FormEvent) => {
    e.preventDefault()
    if (!reply.trim() || !selected) return
    const now = new Date()
    const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`
    setMsgs(prev => ({
      ...prev,
      [selected]: [...(prev[selected] ?? []), { id: `new-${Date.now()}`, from: 'employer', text: reply.trim(), time: timeStr }],
    }))
    setReply('')
  }

  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold" style={{ color: 'var(--ink-strong)', letterSpacing: '-0.02em' }}>Mensajes</h1>
          <p className="text-sm mt-0.5" style={{ color: 'var(--ink-muted)' }}>Conversaciones con candidatos</p>
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs" style={{ background: 'var(--terra-100)', color: 'var(--terra-600)', border: '1px solid rgba(194,86,46,0.2)' }}>
          <Zap size={11} />
          Chat en tiempo real próximamente
        </div>
      </div>

      <div className="flex gap-4" style={{ height: '560px' }}>
        {/* Conversation list */}
        <div className="w-64 flex-shrink-0 flex flex-col rounded-2xl overflow-hidden" style={{ border: '1px solid var(--line)', background: 'var(--bg-elevated)' }}>
          <div className="px-4 py-3" style={{ borderBottom: '1px solid var(--line)' }}>
            <p className="text-xs font-semibold" style={{ color: 'var(--ink-muted)' }}>CONVERSACIONES</p>
          </div>
          <div className="flex-1 overflow-y-auto">
            {MOCK_CONVOS.map(c => (
              <button
                key={c.id}
                onClick={() => setSelected(c.id)}
                className="w-full text-left px-4 py-3 transition-colors"
                style={{
                  background: selected === c.id ? 'var(--terra-100)' : 'transparent',
                  borderBottom: '1px solid var(--line)',
                }}
              >
                <div className="flex items-center gap-2.5">
                  <div
                    className="w-8 h-8 rounded-full flex items-center justify-center text-[11px] font-bold text-white flex-shrink-0"
                    style={{ background: 'linear-gradient(135deg, var(--terra-400), var(--terra-500))' }}
                  >
                    {c.avatar}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-1">
                      <p className="font-semibold text-[12.5px] truncate" style={{ color: selected === c.id ? 'var(--terra-700)' : 'var(--ink-strong)' }}>
                        {c.name}
                      </p>
                      {c.unread && (
                        <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: 'var(--terra-500)' }} />
                      )}
                    </div>
                    <p className="text-[10.5px] truncate mt-0.5" style={{ color: 'var(--ink-muted)' }}>{c.lastMsg}</p>
                    <p className="text-[10px] mt-0.5" style={{ color: 'var(--ink-muted)' }}>{c.time}</p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Chat area */}
        <div className="flex-1 flex flex-col rounded-2xl overflow-hidden" style={{ border: '1px solid var(--line)', background: 'var(--bg-elevated)' }}>
          {convo ? (
            <>
              {/* Header */}
              <div className="px-5 py-3 flex items-center gap-3" style={{ borderBottom: '1px solid var(--line)', background: 'var(--bg-soft)' }}>
                <div
                  className="w-9 h-9 rounded-full flex items-center justify-center text-[11px] font-bold text-white flex-shrink-0"
                  style={{ background: 'linear-gradient(135deg, var(--terra-400), var(--terra-500))' }}
                >
                  {convo.avatar}
                </div>
                <div>
                  <p className="font-semibold text-sm" style={{ color: 'var(--ink-strong)' }}>{convo.name}</p>
                  <p className="text-xs" style={{ color: 'var(--ink-muted)' }}>{convo.jobTitle}</p>
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
                {thread.map(msg => (
                  <div key={msg.id} className={`flex ${msg.from === 'employer' ? 'justify-end' : 'justify-start'}`}>
                    <div
                      className="max-w-[70%] px-4 py-2.5 rounded-2xl text-sm"
                      style={{
                        background: msg.from === 'employer' ? 'var(--terra-500)' : 'var(--bg-warm)',
                        color: msg.from === 'employer' ? '#fff' : 'var(--ink-strong)',
                        borderRadius: msg.from === 'employer' ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
                      }}
                    >
                      {msg.text}
                      <p className="text-[10px] mt-1 opacity-60 text-right">{msg.time}</p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Input */}
              <form onSubmit={sendMsg} className="px-4 py-3 flex gap-2" style={{ borderTop: '1px solid var(--line)' }}>
                <input
                  type="text"
                  value={reply}
                  onChange={e => setReply(e.target.value)}
                  placeholder="Escribe un mensaje..."
                  className="flex-1 px-4 py-2 rounded-full text-sm focus:outline-none"
                  style={{ border: '1px solid var(--line-strong)', background: 'var(--bg-soft)', color: 'var(--ink-strong)' }}
                  onFocus={e => { e.currentTarget.style.borderColor = 'var(--terra-500)' }}
                  onBlur={e => { e.currentTarget.style.borderColor = 'var(--line-strong)' }}
                />
                <button type="submit" disabled={!reply.trim()} className="btn-primary w-9 h-9 rounded-full flex items-center justify-center p-0 flex-shrink-0">
                  <Send size={15} />
                </button>
              </form>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center gap-3">
              <div className="w-14 h-14 rounded-2xl flex items-center justify-center" style={{ background: 'rgba(61,40,24,0.05)', border: '1px solid var(--line)' }}>
                <MessageCircle size={24} style={{ color: 'var(--ink-muted)' }} strokeWidth={1.5} />
              </div>
              <p className="font-semibold text-sm" style={{ color: 'var(--ink-warm)' }}>Selecciona una conversación</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
