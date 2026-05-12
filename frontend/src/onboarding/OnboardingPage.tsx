import { useState } from 'react'
import { useIntl } from 'react-intl'
import { useNavigate } from 'react-router-dom'
import { useWorkerContext } from '../context/WorkerContext'
import apiClient from '../api/client'
import { BriefcaseFilled } from '../shared/BriefcaseIcon'

type Step = 'step1' | 'step2'

const TRADE_CATEGORIES = [
  { value: 'Electricidad',             icon: '⚡', label: 'Electricidad' },
  { value: 'Gasfitería',              icon: '🔧', label: 'Gasfitería' },
  { value: 'Carpintería',             icon: '🪚', label: 'Carpintería' },
  { value: 'Albañilería',             icon: '🧱', label: 'Albañilería' },
  { value: 'Pintura',                 icon: '🖌️', label: 'Pintura' },
  { value: 'Mecánica automotriz',     icon: '🚗', label: 'Mecánica' },
  { value: 'Techado',                 icon: '🏠', label: 'Techado' },
  { value: 'Soldadura y metalurgia',  icon: '🔥', label: 'Soldadura' },
  { value: 'Jardinería',              icon: '🌿', label: 'Jardinería' },
  { value: 'Cocina y pastelería',     icon: '👨‍🍳', label: 'Cocina' },
  { value: 'Costura y confección',    icon: '🧵', label: 'Costura' },
  { value: 'Otros oficios',           icon: '🛠️', label: 'Otros' },
]

export const OnboardingPage: React.FC = () => {
  const intl = useIntl()
  const navigate = useNavigate()
  const { setWorkerType, refreshWorker } = useWorkerContext()
  const [step, setStep] = useState<Step>('step1')
  const [isLoading, setIsLoading] = useState(false)
  const [selectedTrade, setSelectedTrade] = useState<string | null>(null)

  const submit = async (payload: {
    is_first_job: boolean
    is_trade_worker: boolean
    trade_category?: string
  }) => {
    setIsLoading(true)
    try {
      const { data } = await apiClient.post('/onboarding/detect-type', payload)
      setWorkerType(data.worker_type)
      await refreshWorker()
      if (data.worker_type === 'primer_empleo') navigate('/wizard/step/1')
      else if (data.worker_type === 'oficio') navigate('/oficio/portfolio')
      else navigate('/dashboard')
    } catch (err: unknown) {
      // 409 = perfil ya existe → redirigir según el tipo que ya tiene
      const status = (err as { response?: { status?: number } })?.response?.status
      if (status === 409) {
        await refreshWorker()
        const { data: statusData } = await apiClient.get('/onboarding/status')
        const wt = statusData?.worker_type
        setWorkerType(wt)
        if (wt === 'primer_empleo') navigate('/wizard/step/1')
        else if (wt === 'oficio') navigate('/oficio/portfolio')
        else navigate('/dashboard')
      }
    } finally {
      setIsLoading(false)
    }
  }


  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-lg">

        {/* Header */}
        <div className="flex items-center justify-center gap-3 mb-10">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center shadow-warm-sm"
               style={{ background: 'linear-gradient(135deg, #d97757, #c2562e)' }}>
            <BriefcaseFilled className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold text-bark-900 text-xl tracking-tight">DRTPE Junín</span>
        </div>

        {/* Progress bar */}
        <div className="flex gap-2 mb-8">
          <div className="h-1 flex-1 rounded-full bg-primary-500 transition-all" />
          <div className={`h-1 flex-1 rounded-full transition-all ${step === 'step2' ? 'bg-primary-500' : 'bg-warm-300'}`} />
        </div>

        <div className="card-warm p-8">

          {/* PASO 1 */}
          {step === 'step1' && (
            <div className="space-y-7">
              <div className="space-y-2">
                <p className="kicker" style={{ color: '#c2562e' }}>Paso 1 de 2</p>
                <h1 className="text-2xl font-bold text-bark-900" style={{ letterSpacing: '-0.02em' }}>
                  {intl.formatMessage({ id: 'onboarding.step1.question' })}
                </h1>
                <p className="text-bark-500 text-sm">Esto nos permite personalizar tu experiencia desde el inicio.</p>
              </div>

              <div className="space-y-3">
                <button
                  onClick={() => submit({ is_first_job: true, is_trade_worker: false })}
                  disabled={isLoading}
                  className="group w-full flex items-center gap-4 p-5 rounded-xl transition-all disabled:opacity-50 text-left"
                  style={{ background: 'rgba(255,255,255,0.4)', border: '1px solid rgba(61,40,24,0.15)' }}
                >
                  <div className="w-10 h-10 rounded-xl bg-warm-100 group-hover:bg-primary-100 flex items-center justify-center flex-shrink-0 transition-colors">
                    <svg viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5 text-bark-500 group-hover:text-primary-600 transition-colors">
                      <path d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold text-bark-900">{intl.formatMessage({ id: 'onboarding.step1.yes' })}</p>
                    <p className="text-sm text-bark-500">Te ayudaremos a crear tu primer CV paso a paso</p>
                  </div>
                  <svg className="w-4 h-4 text-bark-300 group-hover:text-primary-500 group-hover:translate-x-0.5 transition-all" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                  </svg>
                </button>

                <button
                  onClick={() => setStep('step2')}
                  disabled={isLoading}
                  className="group w-full flex items-center gap-4 p-5 rounded-xl transition-all disabled:opacity-50 text-left"
                  style={{ background: 'rgba(255,255,255,0.4)', border: '1px solid rgba(61,40,24,0.15)' }}
                >
                  <div className="w-10 h-10 rounded-xl bg-warm-100 group-hover:bg-warm-200 flex items-center justify-center flex-shrink-0 transition-colors">
                    <BriefcaseFilled className="w-5 h-5 text-bark-500 transition-colors" />
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold text-bark-900">{intl.formatMessage({ id: 'onboarding.step1.no' })}</p>
                    <p className="text-sm text-bark-500">Ya tengo experiencia laboral</p>
                  </div>
                  <svg className="w-4 h-4 text-bark-300 group-hover:text-bark-600 group-hover:translate-x-0.5 transition-all" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </div>
            </div>
          )}

          {/* PASO 2 */}
          {step === 'step2' && (
            <div className="space-y-6">
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setStep('step1')}
                  className="flex items-center gap-1 text-sm text-bark-500 hover:text-bark-700 transition-colors"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
                  </svg>
                  Volver
                </button>
              </div>

              <div className="space-y-2">
                <p className="kicker" style={{ color: '#c2562e' }}>Paso 2 de 2</p>
                <h2 className="text-2xl font-bold text-bark-900" style={{ letterSpacing: '-0.02em' }}>
                  {intl.formatMessage({ id: 'onboarding.step2.question' })}
                </h2>
                <p className="text-bark-500 text-sm">
                  {intl.formatMessage({ id: 'onboarding.step2.examples' })}
                </p>
              </div>

              <div className="grid grid-cols-3 gap-2 max-h-60 overflow-y-auto pr-1">
                {TRADE_CATEGORIES.map((cat) => (
                  <button
                    key={cat.value}
                    onClick={() => setSelectedTrade(cat.value)}
                    className={`flex flex-col items-center gap-1.5 p-3 rounded-xl border transition-all text-center ${
                      selectedTrade === cat.value
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-warm-300 hover:border-primary-400 bg-white/40'
                    }`}
                  >
                    <span className="text-xl">{cat.icon}</span>
                    <span className={`text-xs font-medium leading-tight ${
                      selectedTrade === cat.value ? 'text-primary-700' : 'text-bark-700'
                    }`}>{cat.label}</span>
                  </button>
                ))}
              </div>

              <div className="grid grid-cols-2 gap-3 pt-1">
                <button
                  onClick={() =>
                    selectedTrade &&
                    submit({ is_first_job: false, is_trade_worker: true, trade_category: selectedTrade })
                  }
                  disabled={!selectedTrade || isLoading}
                  className="btn-primary py-3"
                >
                  {intl.formatMessage({ id: 'onboarding.step2.yes' })}
                </button>
                <button
                  onClick={() => submit({ is_first_job: false, is_trade_worker: false })}
                  disabled={isLoading}
                  className="btn-secondary py-3"
                >
                  {intl.formatMessage({ id: 'onboarding.step2.no' })}
                </button>
              </div>
            </div>
          )}

          {/* Loading overlay */}
          {isLoading && (
            <div className="absolute inset-0 bg-white/80 rounded-2xl flex items-center justify-center">
              <div className="h-7 w-7 animate-spin rounded-full border-[3px] border-warm-200 border-t-primary-600" />
            </div>
          )}
        </div>

        <p className="text-center text-bark-400 text-xs mt-6">DRTPE-Junín · Huancayo, Perú · 2026</p>
      </div>
    </div>
  )
}
