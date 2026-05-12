import { useIntl } from 'react-intl'
import { Link } from 'react-router-dom'
import { useMatches } from '../../hooks/useMatches'
import { JobMatchCard } from '../../matching/JobMatchCard'
import { LoadingSpinner } from '../../shared/LoadingSpinner'
import { useWorkerContext } from '../../context/WorkerContext'

const tips = [
  { emoji: '👔', title: '¿Cómo ir a una entrevista?', desc: 'Viste de forma limpia y ordenada. Llega 10 minutos antes.' },
  { emoji: '💰', title: '¿Cómo negociar mi primer sueldo?', desc: 'Investiga el sueldo promedio del sector antes de la entrevista.' },
  { emoji: '📄', title: '¿Cómo presentar mi CV?', desc: 'Sé breve y honesto. Destaca tus habilidades y disposición de aprender.' },
]

export const PrimerEmpleoDashboard: React.FC = () => {
  const intl = useIntl()
  const { matches, isLoading } = useMatches(5)
  const { worker } = useWorkerContext()

  const completeness = worker?.profile_completeness || 0

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      <div className="max-w-5xl mx-auto px-4 py-6 space-y-6">

        {/* Banner de bienvenida */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl p-6 text-white shadow-lg">
          <h1 className="text-2xl font-bold">{intl.formatMessage({ id: 'primer_empleo.dashboard.welcome' })}</h1>
          <p className="opacity-90 mt-1">{intl.formatMessage({ id: 'primer_empleo.dashboard.subtitle' })}</p>
          <div className="mt-4 flex items-center gap-3">
            <div className="flex-1 h-2 bg-white/30 rounded-full overflow-hidden">
              <div className="h-full bg-white rounded-full transition-all" style={{ width: `${completeness}%` }} />
            </div>
            <span className="text-sm font-bold">{completeness}%</span>
          </div>
          <p className="text-xs text-blue-100 mt-1">Completitud de tu perfil</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {/* Mi CV */}
          <div className="bg-white rounded-2xl shadow-md border border-gray-100 p-5">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
                <span className="text-xl">📄</span>
              </div>
              <h2 className="font-bold text-gray-800">{intl.formatMessage({ id: 'primer_empleo.dashboard.my_cv' })}</h2>
            </div>
            <div className="space-y-2">
              <Link
                to="/wizard/step/1"
                className="block w-full text-center py-2.5 bg-primary-600 hover:bg-primary-700 text-white rounded-xl font-medium text-sm transition-colors"
              >
                {intl.formatMessage({ id: 'primer_empleo.dashboard.continue_wizard' })}
              </Link>
              {worker?.id && (
                <a
                  href={`/api/v1/cv/download/${worker.id}`}
                  target="_blank"
                  rel="noreferrer"
                  className="block w-full text-center py-2.5 border border-primary-300 text-primary-600 hover:bg-primary-50 rounded-xl font-medium text-sm transition-colors"
                >
                  Descargar CV (PDF)
                </a>
              )}
            </div>
          </div>

          {/* Orientación laboral */}
          <div className="bg-white rounded-2xl shadow-md border border-gray-100 p-5">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center">
                <span className="text-xl">🎓</span>
              </div>
              <h2 className="font-bold text-gray-800">Orientación laboral</h2>
            </div>
            <div className="space-y-3">
              {tips.map((t) => (
                <div key={t.title} className="flex gap-3 p-3 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors cursor-pointer">
                  <span className="text-xl flex-shrink-0">{t.emoji}</span>
                  <div>
                    <p className="text-sm font-semibold text-gray-800">{t.title}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{t.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Recomendaciones */}
        <div className="bg-white rounded-2xl shadow-md border border-gray-100 p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
                <span className="text-xl">✨</span>
              </div>
              <h2 className="font-bold text-gray-800">{intl.formatMessage({ id: 'primer_empleo.dashboard.recommendations' })}</h2>
            </div>
            <Link to="/matches" className="text-xs text-primary-600 font-medium hover:underline">
              Ver todos →
            </Link>
          </div>
          {isLoading ? <LoadingSpinner size="sm" /> : matches.length > 0 ? (
            <div className="space-y-3">
              {matches.map((m) => <JobMatchCard key={m.job_id} match={m} workerType="primer_empleo" />)}
            </div>
          ) : (
            <div className="text-center py-8">
              <span className="text-4xl block mb-2">🔍</span>
              <p className="text-gray-500 text-sm">{intl.formatMessage({ id: 'primer_empleo.dashboard.no_matches_yet' })}</p>
              <Link to="/wizard/step/1" className="text-primary-600 text-sm font-medium hover:underline mt-1 block">
                Completar mi perfil
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
