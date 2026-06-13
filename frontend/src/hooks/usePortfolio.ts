import { useState, useEffect, useCallback } from 'react'
import apiClient from '../api/client'
import { useWorkerContext } from '../context/WorkerContext'

export interface PortfolioEntry {
  id: string
  title: string
  description: string
  extracted_skills: string[]
  photos: string[]
  period_start: string | null
  period_end: string | null
  client_rating: number | null
  is_public: boolean
}

export const usePortfolio = () => {
  const { worker } = useWorkerContext()
  const [entries, setEntries] = useState<PortfolioEntry[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const load = useCallback(async () => {
    if (!worker?.id) return
    setIsLoading(true)
    try {
      const { data } = await apiClient.get('/portfolio/entries')
      setEntries(data || [])
    } catch { /* ignore */ }
    finally { setIsLoading(false) }
  }, [worker?.id])

  useEffect(() => { load() }, [load])

  /**
   * Crea una entrada de portafolio. El backend espera el trabajo como JSON
   * (title/description) y las fotos en un endpoint multipart aparte, así que
   * se hace en dos pasos: crear la entrada y luego subir las fotos.
   */
  const addEntry = async (data: { title: string; description: string; files: File[] }) => {
    const { data: entry } = await apiClient.post('/portfolio/entries', {
      title: data.title,
      description: data.description,
    })
    if (data.files.length > 0 && entry?.id) {
      const fd = new FormData()
      data.files.forEach((f) => fd.append('files', f))
      // axios fija automáticamente el Content-Type multipart con boundary al detectar FormData
      await apiClient.post(`/portfolio/entries/${entry.id}/photos`, fd)
    }
    await load()
  }

  const deleteEntry = async (id: string) => {
    await apiClient.delete(`/portfolio/entries/${id}`)
    setEntries(prev => prev.filter(e => e.id !== id))
  }

  return { entries, isLoading, worker, addEntry, deleteEntry, refresh: load }
}
