import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { SkillTag } from '../shared/SkillTag'
import apiClient from '../api/client'

interface PublicPortfolio {
  worker: {
    display_name: string
    trade_category: string
    district: string
    avg_rating: number
    years_experience: number
  }
  entries: Array<{
    id: string
    title: string
    description: string
    extracted_skills: string[]
    photos: string[]
    client_rating: number | null
  }>
}

export const PublicPortfolioPage: React.FC = () => {
  const { slug } = useParams()
  const [data, setData] = useState<PublicPortfolio | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    apiClient.get(`/portfolio/public/${slug}`)
      .then(({ data }) => setData(data))
      .catch(() => null)
      .finally(() => setIsLoading(false))
  }, [slug])

  if (isLoading) return (
    <div className="min-h-screen flex items-center justify-center bg-amber-50">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-amber-200 border-t-amber-600" />
    </div>
  )

  if (!data) return (
    <div className="min-h-screen flex items-center justify-center bg-amber-50">
      <div className="text-center">
        <span className="text-5xl block mb-3">🔍</span>
        <p className="text-gray-600">Perfil no encontrado</p>
      </div>
    </div>
  )

  const { worker, entries } = data
  const allSkills = [...new Set(entries.flatMap((e) => e.extracted_skills))]

  return (
    <div className="min-h-screen bg-amber-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-amber-700 to-amber-500 text-white py-10">
        <div className="max-w-3xl mx-auto px-4 text-center">
          <div className="w-20 h-20 rounded-full bg-white/20 flex items-center justify-center text-3xl font-bold mx-auto mb-4">
            {worker.display_name[0]}
          </div>
          <h1 className="text-2xl font-bold">{worker.display_name}</h1>
          <p className="text-amber-100 mt-1">{worker.trade_category} · {worker.district}</p>
          <div className="flex items-center justify-center gap-4 mt-3">
            <span className="text-yellow-300 text-lg">{'★'.repeat(Math.round(worker.avg_rating))}</span>
            <span className="text-amber-100 text-sm">{worker.avg_rating.toFixed(1)}/5.0</span>
            <span className="text-amber-200 text-sm">·</span>
            <span className="text-amber-100 text-sm">{worker.years_experience} años de experiencia</span>
          </div>
          <div className="flex items-center justify-center gap-1.5 mt-3 flex-wrap">
            {allSkills.slice(0, 8).map((s) => (
              <span key={s} className="bg-white/20 text-white text-xs px-2.5 py-1 rounded-full">{s}</span>
            ))}
          </div>
        </div>
      </div>

      {/* Trabajos */}
      <div className="max-w-3xl mx-auto px-4 py-8">
        <h2 className="font-bold text-gray-800 text-lg mb-5">Trabajos realizados ({entries.length})</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {entries.map((entry) => (
            <div key={entry.id} className="bg-white rounded-2xl shadow-sm border border-amber-100 overflow-hidden">
              {entry.photos[0] && (
                <div className="h-44 overflow-hidden">
                  <img src={entry.photos[0]} alt={entry.title} className="w-full h-full object-cover" />
                </div>
              )}
              <div className="p-4">
                <h3 className="font-semibold text-gray-900 mb-1">{entry.title}</h3>
                <p className="text-xs text-gray-500 line-clamp-3 mb-3">{entry.description}</p>
                <div className="flex flex-wrap gap-1">
                  {entry.extracted_skills.slice(0, 4).map((s) => (
                    <SkillTag key={s} label={s} color="amber" />
                  ))}
                </div>
                {entry.client_rating && (
                  <p className="text-yellow-400 text-sm mt-2">{'★'.repeat(Math.round(entry.client_rating))}</p>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-8 text-center">
          <a
            href="/register"
            className="inline-block bg-amber-500 hover:bg-amber-600 text-white font-semibold px-6 py-3 rounded-xl transition-colors shadow-sm"
          >
            Contratar a {worker.display_name.split(' ')[0]}
          </a>
          <p className="text-xs text-gray-400 mt-2">Plataforma DRTPE-Junín</p>
        </div>
      </div>
    </div>
  )
}
