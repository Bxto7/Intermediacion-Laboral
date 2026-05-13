import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useIntl } from 'react-intl'
import { Camera, X } from 'lucide-react'
import { usePortfolio } from '../../../hooks/usePortfolio'

interface Props { onClose: () => void }

const fieldStyle = {
  border: '1px solid rgba(61,40,24,0.14)',
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
    if (!title.trim() || !description.trim()) return
    setIsSubmitting(true)
    try {
      const fd = new FormData()
      fd.append('title', title)
      fd.append('description', description)
      files.forEach((f) => fd.append('photos', f))
      await addEntry(fd)
      onClose()
    } catch { /* ignore */ }
    finally { setIsSubmitting(false) }
  }

  const focusStyle = (e: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    e.currentTarget.style.borderColor = 'var(--terra-500)'
    e.currentTarget.style.boxShadow = '0 0 0 3px rgba(194,86,46,0.12)'
  }
  const blurStyle = (e: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    e.currentTarget.style.borderColor = 'rgba(61,40,24,0.14)'
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
            onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.background = 'rgba(61,40,24,0.07)' }}
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
              placeholder="Describe el trabajo: qué hiciste, cómo lo hiciste, materiales que usaste..."
              style={{ ...fieldStyle, resize: 'none' }}
              onFocus={focusStyle as unknown as React.FocusEventHandler<HTMLTextAreaElement>}
              onBlur={blurStyle as unknown as React.FocusEventHandler<HTMLTextAreaElement>}
            />
            <p className="text-xs mt-1" style={{ color: 'var(--ink-muted)' }}>El sistema detectará automáticamente tus habilidades</p>
          </div>
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--ink-warm)' }}>Fotos del trabajo (máx. 4)</label>
            <div
              {...getRootProps()}
              className="border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors"
              style={{
                borderColor: isDragActive ? 'var(--terra-500)' : 'rgba(61,40,24,0.18)',
                background: isDragActive ? 'rgba(194,86,46,0.04)' : 'var(--bg-soft)',
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
