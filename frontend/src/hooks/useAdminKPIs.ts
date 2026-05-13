import { useState, useEffect } from 'react'
import apiClient from '../api/client'

export interface KPIData {
  vil: Record<string, { avg_days: number; n: number }>
  ivp: Record<string, unknown>
  tf: Record<string, number>
  rbs: { avg_pct: number; n_pairs: number }
  tcc: Record<string, number>
  ivm: { ivm_pct: number; total_oficio: number }
  tcss: Record<string, number>
  calculated_at: string
}

export const useAdminKPIs = () => {
  const [kpis, setKpis] = useState<KPIData | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    apiClient.get('/admin/dashboard')
      .then(({ data }) => setKpis(data))
      .catch(() => setKpis(null))
      .finally(() => setIsLoading(false))
  }, [])

  return { kpis, isLoading }
}
