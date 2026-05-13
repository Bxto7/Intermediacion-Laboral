import React, { createContext, useContext, useState, useEffect } from 'react'
import apiClient from '../api/client'
import { useAuthContext } from './AuthContext'

type WorkerType = 'primer_empleo' | 'experiencia' | 'oficio' | null

interface WorkerProfile {
  id: string
  worker_type: WorkerType
  district: string | null
  trade_category: string | null
  avg_rating: number
  profile_completeness: number
  display_name?: string
  full_name?: string
  job_title?: string | null
  bio?: string | null
  is_available?: boolean
  years_experience?: number
  slug?: string
}

interface WorkerContextType {
  workerType: WorkerType
  worker: WorkerProfile | null
  isLoading: boolean
  setWorkerType: (t: WorkerType) => void
  refreshWorker: () => Promise<void>
}

const WorkerContext = createContext<WorkerContextType | null>(null)

export const WorkerProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, user } = useAuthContext()
  const [worker, setWorker] = useState<WorkerProfile | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const refreshWorker = async () => {
    if (!isAuthenticated || user?.role !== 'worker') return
    setIsLoading(true)
    try {
      const { data } = await apiClient.get('/workers/me')
      setWorker(data)
    } catch {
      setWorker(null)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => { refreshWorker() }, [isAuthenticated])  // eslint-disable-line

  const setWorkerType = (t: WorkerType) => {
    setWorker(prev => prev ? { ...prev, worker_type: t } : { id: '', worker_type: t, district: null, trade_category: null, avg_rating: 0, profile_completeness: 0 })
  }

  return (
    <WorkerContext.Provider value={{ workerType: worker?.worker_type ?? null, worker, isLoading, setWorkerType, refreshWorker }}>
      {children}
    </WorkerContext.Provider>
  )
}

export const useWorkerContext = () => {
  const ctx = useContext(WorkerContext)
  if (!ctx) throw new Error('useWorkerContext must be inside WorkerProvider')
  return ctx
}
