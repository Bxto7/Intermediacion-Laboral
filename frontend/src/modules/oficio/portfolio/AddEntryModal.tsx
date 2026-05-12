import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useIntl } from 'react-intl'
import { usePortfolio } from '../../../hooks/usePortfolio'

interface Props { onClose: () => void }

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

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-5 border-b border-gray-100">
          <h2 className="font-bold text-gray-900">Agregar trabajo realizado</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">×</button>
        </div>
        <div className="p-5 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Título del trabajo *</label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Ej: Instalación eléctrica residencial en El Tambo"
              className="w-full px-3.5 py-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-amber-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Descripción *</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              placeholder="Describe el trabajo: qué hiciste, cómo lo hiciste, materiales que usaste..."
              className="w-full px-3.5 py-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-amber-500 outline-none resize-none"
            />
            <p className="text-xs text-gray-400 mt-1">El sistema detectará automáticamente tus habilidades</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Fotos del trabajo (máx. 4)</label>
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors ${
                isDragActive ? 'border-amber-500 bg-amber-50' : 'border-gray-300 hover:border-amber-400 hover:bg-amber-50/40'
              }`}
            >
              <input {...getInputProps()} />
              <span className="text-3xl block mb-2">📷</span>
              <p className="text-sm text-gray-500">
                {isDragActive ? 'Suelta las fotos aquí' : 'Arrastra fotos o haz clic para seleccionar'}
              </p>
              <p className="text-xs text-gray-400 mt-1">JPEG, PNG, WEBP · Máx 5 MB c/u</p>
            </div>
            {files.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {files.map((f, i) => (
                  <div key={i} className="relative w-16 h-16 rounded-lg overflow-hidden bg-gray-100">
                    <img src={URL.createObjectURL(f)} alt="" className="w-full h-full object-cover" />
                    <button
                      onClick={() => setFiles((p) => p.filter((_, j) => j !== i))}
                      className="absolute top-0.5 right-0.5 w-4 h-4 bg-red-500 text-white rounded-full text-xs flex items-center justify-center"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
        <div className="flex gap-3 p-5 border-t border-gray-100">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 border border-gray-300 text-gray-700 rounded-xl font-medium text-sm hover:bg-gray-50 transition-colors"
          >
            {intl.formatMessage({ id: 'common.cancel' })}
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSubmitting || !title.trim() || !description.trim()}
            className="flex-1 py-2.5 bg-amber-500 hover:bg-amber-600 disabled:opacity-50 text-white rounded-xl font-semibold text-sm transition-colors"
          >
            {isSubmitting ? 'Guardando...' : 'Guardar trabajo'}
          </button>
        </div>
      </div>
    </div>
  )
}
