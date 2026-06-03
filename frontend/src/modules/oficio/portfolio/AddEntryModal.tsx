import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useIntl } from 'react-intl'
import { Camera, X } from 'lucide-react'
import { usePortfolio } from '../../../hooks/usePortfolio'
import { parseApiError } from '../../../lib/parseApiError'

interface Props { onClose: () => void }

const fieldStyle = {
  border: '1px solid rgba(42,29,20,0.14)',
  background: 'var(--bg-soft)',
  color: 'var(--ink-strong)',
  borderRadius: '12px',
  fontSize: '14px',
  outline: 'none',
  width: '100%',
  padding: '10px 14px',
}

export const AddEntryModal: React.FC<Props> = ({ onClose }) => {
  const intl = useIntl()
  const { addEntry } = usePortfolio()
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')

  const onDrop = useCallback((accepted: File[]) => {
    setFiles((prev) => [...prev, ...accepted].slice(0, 4))
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/jpeg': [], 'image/png': [], 'image/webp': [] },
    maxSize: 5 * 1024 * 1024,
    maxFiles: 4,
  })

  const handleSubmit = async () => {
    setError('')
    const t = title.trim()
    const d = description.trim()
    if (t.length < 3) { setError('El título debe tener al menos 3 caracteres.'); return }
    if (t.length > 200) { setError('El título no debe superar 200 caracteres.'); return }
    if (d.length < 20) { setError('La descripción debe tener al menos 20 caracteres.'); return }
    if (d.length > 2000) { setError(`La descripción es muy larga (${d.length}/2000). Acórtala un poco.`); return }
    setIsSubmitting(true)
    try {
      await addEntry({ title: t, description: d, files })
      onClose()
    } catch (err) {
      setError(parseApiError(err))
    } finally { setIsSubmitting(false) }
  }

  const focusStyle = (e: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    e.currentTarget.style.borderColor = 'var(--terra-500)'
    e.currentTarget.style.boxShadow = '0 0 0 3px rgba(184,68,42,0.12)'
  }
  const blurStyle = (e: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    e.currentTarget.style.borderColor = 'rgba(42,29,20,0.14)'
    e.currentTarget.style.boxShadow = 'none'
  }

  return (
    <div
      className="fixed inset-0 flex items-center justify-center p-4 z-50"
      style={{ background: 'rgba(26,15,10,0.55)', backdropFilter: 'blur(8px)' }}
    >
      <div
        className="w-full max-w-lg max-h-[90vh] overflow-y-auto"
        style={{ background: 'var(--bg-elevated)', borderRadius: '20px', boxShadow: '0 40px 80px -20px rgba(0,0,0,0.4)' }}
      >
        <div className="flex items-center justify-between p-5" style={{ borderBottom: '1px solid var(--line)' }}>
          <h2 className="font-bold" style={{ color: 'var(--ink-strong)' }}>Agregar trabajo realizado</h2>
          <button
            onClick={onClose}
            aria-label="Cerrar modal"
            className="w-11 h-11 rounded-full flex items-center justify-center transition-colors cursor-pointer"
            style={{ color: 'var(--ink-muted)' }}
            onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.background = 'rgba(42,29,20,0.07)' }}
            onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.background = 'transparent' }}
          >
            <X size={16} />
          </button>
        </div>

        <div className="p-5 space-y-4">
          <div>
            <label htmlFor="entry-title" className="block text-sm font-medium mb-1" style={{ color: 'var(--ink-warm)' }}>Título del trabajo *</label>
            <input
              id="entry-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              maxLength={200}
              placeholder="Ej: Instalación eléctrica residencial en El Tambo"
              style={fieldStyle}
              onFocus={focusStyle}
              onBlur={blurStyle}
            />
          </div>
          <div>
            <label htmlFor="entry-desc" className="block text-sm font-medium mb-1" style={{ color: 'var(--ink-warm)' }}>Descripción *</label>
            <textarea
              id="entry-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              maxLength={2000}
              placeholder="Describe el trabajo: qué hiciste, cómo lo hiciste, materiales que usaste..."
              style={{ ...fieldStyle, resize: 'none' }}
              onFocus={focusStyle as unknown as React.FocusEventHandler<HTMLTextAreaElement>}
              onBlur={blurStyle as unknown as React.FocusEventHandler<HTMLTextAreaElement>}
            />
            <div className="flex items-center justify-between mt-1">
              <p className="text-xs" style={{ color: 'var(--ink-muted)' }}>El sistema detectará automáticamente tus habilidades</p>
              <span className="text-xs" style={{ color: description.length > 2000 ? '#9e2b25' : 'var(--ink-muted)' }}>{description.length}/2000</span>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--ink-warm)' }}>Fotos del trabajo (máx. 4)</label>
            <div
              {...getRootProps()}
              className="border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors"
              style={{
                borderColor: isDragActive ? 'var(--terra-500)' : 'rgba(42,29,20,0.18)',
                background: isDragActive ? 'rgba(184,68,42,0.04)' : 'var(--bg-soft)',
              }}
            >
              <input {...getInputProps()} />
              <Camera size={28} className="mx-auto mb-2" style={{ color: 'var(--ink-muted)' }} strokeWidth={1.5} />
              <p className="text-sm" style={{ color: 'var(--ink-muted)' }}>
                {isDragActive ? 'Suelta las fotos aquí' : 'Arrastra fotos o haz clic para seleccionar'}
              </p>
              <p className="text-xs mt-1" style={{ color: 'var(--ink-muted)' }}>JPEG, PNG, WEBP · Máx 5 MB c/u</p>
            </div>
            {files.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {files.map((f, i) => (
                  <div key={i} className="relative w-16 h-16 rounded-xl overflow-hidden" style={{ background: 'var(--bg-warm)' }}>
                    <img src={URL.createObjectURL(f)} alt="" className="w-full h-full object-cover" />
                    <button
                      onClick={() => setFiles((p) => p.filter((_, j) => j !== i))}
                      aria-label={`Eliminar foto ${i + 1}`}
                      className="absolute top-0.5 right-0.5 w-5 h-5 rounded-full flex items-center justify-center text-white cursor-pointer"
                      style={{ background: 'var(--terra-500)' }}
                    >
                      <X size={10} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {error && (
          <div className="mx-5 mb-1 flex gap-2 px-3 py-2.5 rounded-xl text-sm" style={{ background: '#fbeceb', border: '1px solid #f3d4d2', color: '#9e2b25' }}>
            <svg className="w-4 h-4 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><circle cx="12" cy="12" r="10"/><path d="M12 8v4m0 4h.01"/></svg>
            {error}
          </div>
        )}

        <div className="flex gap-3 p-5" style={{ borderTop: '1px solid var(--line)' }}>
          <button onClick={onClose} className="btn-secondary flex-1 py-2.5 text-sm">
            {intl.formatMessage({ id: 'common.cancel' })}
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSubmitting || !title.trim() || !description.trim()}
            className="btn-primary flex-1 py-2.5 text-sm"
          >
            {isSubmitting ? 'Guardando...' : 'Guardar trabajo'}
          </button>
        </div>
      </div>
    </div>
  )
}
