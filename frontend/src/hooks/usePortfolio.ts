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
      const { data } = await apiClient.get(`/portfolio/${worker.id}`)
      setEntries(data || [])
    } catch { /* ignore */ }
    finally { setIsLoading(false) }
  }, [worker?.id])

  useEffect(() => { load() }, [load])

  const addEntry = async (payload: FormData) => {
    await apiClient.post('/portfolio/entries', payload, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    await load()
  }

  const deleteEntry = async (id: string) => {
    await apiClient.delete(`/portfolio/entries/${id}`)
    setEntries(prev => prev.filter(e => e.id !== id))
  }

  return { entries, isLoading, worker, addEntry, deleteEntry, refresh: load }
}
