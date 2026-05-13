import { useState, useEffect, useCallback } from 'react'
import apiClient from '../api/client'

export interface Application {
  id: string
  job_offer_id: string
  worker_id: string
  cover_message: string | null
  proposed_rate: number | null
  status: string
  created_at: string
  offer_title: string
  employer_name: string
}

export const useApplications = () => {
  const [applications, setApplications] = useState<Application[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const load = useCallback(async () => {
    setIsLoading(true)
    try {
      const { data } = await apiClient.get('/applications/my')
      setApplications(data || [])
    } catch { /* ignore */ }
    finally { setIsLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const withdraw = async (id: string) => {
    await apiClient.patch(`/applications/${id}/withdraw`)
    setApplications(prev => prev.map(a => a.id === id ? { ...a, status: 'WITHDRAWN' } : a))
  }

  const apply = async (jobOfferId: string, coverMessage?: string, proposedRate?: number): Promise<'ok' | 'duplicate' | 'error'> => {
    try {
      const { data } = await apiClient.post('/applications', {
        job_offer_id: jobOfferId,
        cover_message: coverMessage || null,
        proposed_rate: proposedRate || null,
      })
      setApplications(prev => [data, ...prev])
      return 'ok'
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status
      if (status === 409) return 'duplicate'
      return 'error'
    }
  }

  return { applications, isLoading, withdraw, apply, refresh: load }
}
