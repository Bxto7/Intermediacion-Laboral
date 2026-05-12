import { useState, useEffect } from 'react'
import apiClient from '../api/client'
import { useWorkerContext } from '../context/WorkerContext'

interface MatchExplanation {
  matching_skills: string[]
  missing_skills: string[]
  compatibility_label: 'Alta' | 'Media' | 'Baja'
  message: string
}

export interface JobMatch {
  job_id: string
  title: string
  district: string | null
  combined_score: number
  rank: number
  explanation: MatchExplanation
}

export const useMatches = (topK = 10) => {
  const { worker } = useWorkerContext()
  const [matches, setMatches] = useState<JobMatch[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!worker?.id) return
    setIsLoading(true)
    apiClient.get(`/match/${worker.id}`, { params: { top_k: topK } })
      .then(({ data }) => setMatches(data.matches || []))
      .catch(() => setError('No se pudieron cargar las recomendaciones'))
      .finally(() => setIsLoading(false))
  }, [worker?.id, topK])

  return { matches, isLoading, error }
}
