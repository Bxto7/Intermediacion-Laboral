import { useIntl } from 'react-intl'

export default function App() {
  const intl = useIntl()

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
      <div className="bg-white rounded-2xl shadow-lg p-10 max-w-lg w-full text-center">
        <div className="mb-4">
          <span className="inline-block bg-primary-100 text-primary-700 text-sm font-semibold px-3 py-1 rounded-full">
            {intl.formatMessage({ id: 'app.sprint' })}
          </span>
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          {intl.formatMessage({ id: 'app.title' })}
        </h1>
        <p className="text-gray-500 mb-6">
          {intl.formatMessage({ id: 'app.subtitle' })}
        </p>
        <div className="flex flex-col gap-3">
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="bg-primary-600 hover:bg-primary-700 text-white font-medium py-2 px-6 rounded-lg transition-colors"
          >
            {intl.formatMessage({ id: 'app.api_docs' })}
          </a>
          <a
            href="http://localhost:8000/health"
            target="_blank"
            rel="noreferrer"
            className="border border-gray-300 hover:bg-gray-50 text-gray-700 font-medium py-2 px-6 rounded-lg transition-colors"
          >
            {intl.formatMessage({ id: 'app.health_check' })}
          </a>
        </div>
        <p className="text-xs text-gray-400 mt-6">
          {intl.formatMessage({ id: 'app.footer' })}
        </p>
      </div>
    </div>
  )
}
