import { useState, useEffect, useCallback } from 'react'
import apiClient from '../api/client'

export interface ServiceListing {
  id: string
  worker_id: string
  trade_category: string
  title: string
  description: string
  enriched_keywords: string[]
  districts: string[]
  price_reference: number | null
  price_unit: string | null
  availability: string | null
  is_active: boolean
  views_count: number
  created_at: string
  worker_name: string
  worker_district: string
  worker_avg_rating: number
  worker_years_experience: number
  worker_username: string | null
  relevance_score: number | null
}

export interface ListingCreate {
  trade_category: string
  title: string
  description: string
  districts: string[]
  price_reference?: number | null
  price_unit?: string | null
  availability?: string | null
}

export const useMyListings = () => {
  const [listings, setListings] = useState<ServiceListing[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const load = useCallback(async () => {
    setIsLoading(true)
    try {
      const { data } = await apiClient.get('/marketplace/listings')
      setListings(data || [])
    } catch { /* ignore */ }
    finally { setIsLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const create = async (payload: ListingCreate) => {
    const { data } = await apiClient.post('/marketplace/listings', payload)
    setListings(prev => [data, ...prev])
    return data as ServiceListing
  }

  const update = async (id: string, payload: Partial<ListingCreate>) => {
    const { data } = await apiClient.patch(`/marketplace/listings/${id}`, payload)
    setListings(prev => prev.map(l => l.id === id ? data : l))
  }

  const remove = async (id: string) => {
    await apiClient.delete(`/marketplace/listings/${id}`)
    setListings(prev => prev.filter(l => l.id !== id))
  }

  return { listings, isLoading, create, update, remove, refresh: load }
}

export const useMarketplaceSearch = () => {
  const [results, setResults] = useState<ServiceListing[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const search = useCallback(async (params: {
    query?: string
    district?: string
    trade_category?: string
    availability?: string
    limit?: number
    offset?: number
  }) => {
    setIsLoading(true)
    try {
      const { data } = await apiClient.get('/marketplace/search', { params })
      setResults(data || [])
    } catch { /* ignore */ }
    finally { setIsLoading(false) }
  }, [])

  return { results, isLoading, search }
}
