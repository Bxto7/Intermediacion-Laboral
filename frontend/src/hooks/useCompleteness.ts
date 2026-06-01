import { useEffect, useState } from 'react'
import apiClient from '../api/client'

export interface Completeness {
  percentage: number
  missing_fields: string[]
  next_action: string
}

/** Obtiene la completitud real del perfil del trabajador, incluyendo qué falta. */
export const useCompleteness = (enabled = true) => {
  const [data, setData] = useState<Completeness | null>(null)
  const [isLoading, setIsLoading] = useState(enabled)

  useEffect(() => {
    if (!enabled) return
    let active = true
    apiClient.get('/workers/me/completeness')
      .then(({ data }) => { if (active) setData(data) })
      .catch(() => { if (active) setData(null) })
      .finally(() => { if (active) setIsLoading(false) })
    return () => { active = false }
  }, [enabled])

  return { completeness: data, isLoading }
}
