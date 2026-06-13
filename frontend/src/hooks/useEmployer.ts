import { useState, useEffect, useCallback } from 'react'
import apiClient from '../api/client'

export interface JobOffer {
  id: string
  title: string
  description: string
  district: string | null
  modality: string | null
  salary_min: number | null
  salary_max: number | null
  worker_type_target: string | null
  required_skills: string[]
  is_active: boolean
  views_count: number
  applications_count: number
  created_at: string
  days_until_expiry: number | null
}

export interface JobOfferCreate {
  title: string
  description: string
  district: string
  modality: string
  salary_min: number | null
  salary_max: number | null
  worker_type_target: string
  required_skills: string[]
  preferred_skills: string[]
}

export interface CandidateApplication {
  id: string
  job_offer_id: string
  worker_id: string
  status: string
  match_score: number | null
  cover_note: string | null
  applied_at: string
  job_title: string
  worker_name?: string
}

export const useEmployerJobs = () => {
  const [jobs, setJobs] = useState<JobOffer[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const load = useCallback(async () => {
    setIsLoading(true)
    try {
      const { data } = await apiClient.get('/employers/jobs')
      setJobs(data || [])
    } catch { /* ignore */ }
    finally { setIsLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const createJob = async (payload: JobOfferCreate): Promise<JobOffer> => {
    const { data } = await apiClient.post('/employers/jobs', payload)
    setJobs(prev => [data, ...prev])
    return data
  }

  const deleteJob = async (id: string) => {
    await apiClient.delete(`/employers/jobs/${id}`)
    setJobs(prev => prev.filter(j => j.id !== id))
  }

  return { jobs, isLoading, createJob, deleteJob, refresh: load }
}

export const useJobApplications = (jobId: string | null) => {
  const [applications, setApplications] = useState<CandidateApplication[]>([])
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    if (!jobId) return
    setIsLoading(true)
    apiClient.get(`/employers/jobs/${jobId}/applications`)
      .then(({ data }) => setApplications(data || []))
      .catch(() => setApplications([]))
      .finally(() => setIsLoading(false))
  }, [jobId])

  const updateStatus = async (appId: string, newStatus: string) => {
    await apiClient.patch(`/employers/jobs/${jobId}/applications/${appId}/status`, { status: newStatus })
    setApplications(prev => prev.map(a => a.id === appId ? { ...a, status: newStatus } : a))
  }

  return { applications, isLoading, updateStatus }
}
