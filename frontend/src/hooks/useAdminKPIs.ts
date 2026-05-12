import { useState, useEffect } from 'react'
import apiClient from '../api/client'

interface KPIData {
  vil: Record<string, { avg_days: number; count: number }>
  tf: Record<string, { tasa_percent: number; total: number; formalized: number }>
  tcc: Record<string, { tcc_percent: number; total: number; with_cv: number }>
  ivm: { ivm_percent: number; active_listings: number; total_oficio: number }
  cold_start: Record<string, { rate_percent: number; total: number; with_matches: number }>
}

export const useAdminKPIs = () => {
  const [kpis, setKpis] = useState<KPIData | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    apiClient.get('/admin/kpis')
      .then(({ data }) => setKpis(data))
      .catch(() => setKpis(null))
      .finally(() => setIsLoading(false))
  }, [])

  return { kpis, isLoading }
}
