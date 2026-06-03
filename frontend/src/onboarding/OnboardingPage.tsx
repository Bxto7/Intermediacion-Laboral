import { useState } from 'react'
import { useIntl } from 'react-intl'
import { useNavigate } from 'react-router-dom'
import {
  Zap, Wrench, Hammer, Building2, Paintbrush, Car,
  Home, Flame, Leaf, ChefHat, Scissors, Briefcase,
  ChevronRight, ChevronLeft, UserCircle,
} from 'lucide-react'
import { useWorkerContext } from '../context/WorkerContext'
import apiClient from '../api/client'
import { LinkuLogoFull } from '../shared/LinkuLogo'

type Step = 'step1' | 'step2'

const TRADE_CATEGORIES = [
  { value: 'Electricidad',            label: 'Electricidad',  Icon: Zap },
  { value: 'Gasfitería',             label: 'Gasfitería',    Icon: Wrench },
  { value: 'Carpintería',            label: 'Carpintería',   Icon: Hammer },
  { value: 'Albañilería',            label: 'Albañilería',   Icon: Building2 },
  { value: 'Pintura',                label: 'Pintura',       Icon: Paintbrush },
  { value: 'Mecánica automotriz',    label: 'Mecánica',      Icon: Car },
  { value: 'Techado',                label: 'Techado',       Icon: Home },
  { value: 'Soldadura y metalurgia', label: 'Soldadura',     Icon: Flame },
  { value: 'Jardinería',             label: 'Jardinería',    Icon: Leaf },
  { value: 'Cocina y pastelería',    label: 'Cocina',        Icon: ChefHat },
  { value: 'Costura y confección',   label: 'Costura',       Icon: Scissors },
  { value: 'Otros oficios',          label: 'Otros',         Icon: Briefcase },
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
    <div className="min-h-screen flex items-center justify-center p-6" style={{ background: 'var(--bg-base)' }}>
      <div className="w-full max-w-lg">

        {/* Header */}
        <div className="flex items-center justify-center mb-10">
          <LinkuLogoFull size={40} variant="default" />
        </div>

        {/* Progress bar */}
        <div className="flex gap-2 mb-8">
          <div className="h-1 flex-1 rounded-full transition-all" style={{ background: 'var(--terra-500)' }} />
          <div
            className="h-1 flex-1 rounded-full transition-all"
            style={{ background: step === 'step2' ? 'var(--terra-500)' : 'var(--bg-warm)' }}
          />
        </div>

        <div className="card-warm p-8 relative">

          {/* PASO 1 */}
          {step === 'step1' && (
            <div className="space-y-7">
              <div className="space-y-2">
                <p className="kicker" style={{ color: 'var(--terra-500)' }}>Paso 1 de 2</p>
                <h1 className="text-2xl font-bold" style={{ color: 'var(--ink-strong)', letterSpacing: '-0.02em' }}>
                  {intl.formatMessage({ id: 'onboarding.step1.question' })}
                </h1>
                <p className="text-sm" style={{ color: 'var(--ink-muted)' }}>
                  Esto nos permite personalizar tu experiencia desde el inicio.
                </p>
              </div>

              <div className="space-y-3">
                {/* Sí, primer empleo */}
                <button
                  onClick={() => submit({ is_first_job: true, is_trade_worker: false })}
                  disabled={isLoading}
                  className="group w-full flex items-center gap-4 p-5 rounded-2xl transition-all disabled:opacity-50 text-left"
                  style={{ background: 'var(--bg-soft)', border: '1px solid var(--line)' }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--terra-500)'; e.currentTarget.style.background = 'rgba(184,68,42,0.04)' }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--line)'; e.currentTarget.style.background = 'var(--bg-soft)' }}
                >
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 transition-colors"
                    style={{ background: 'var(--terra-100)' }}
                  >
                    <UserCircle size={20} style={{ color: 'var(--terra-500)' }} />
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold text-sm" style={{ color: 'var(--ink-strong)' }}>
                      {intl.formatMessage({ id: 'onboarding.step1.yes' })}
                    </p>
                    <p className="text-xs mt-0.5" style={{ color: 'var(--ink-muted)' }}>
                      Te ayudaremos a crear tu primer CV paso a paso
                    </p>
                  </div>
                  <ChevronRight size={16} style={{ color: 'var(--ink-muted)' }} />
                </button>

                {/* No, tengo experiencia */}
                <button
                  onClick={() => setStep('step2')}
                  disabled={isLoading}
                  className="group w-full flex items-center gap-4 p-5 rounded-2xl transition-all disabled:opacity-50 text-left"
                  style={{ background: 'var(--bg-soft)', border: '1px solid var(--line)' }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--line-strong)'; e.currentTarget.style.background = 'rgba(42,29,20,0.03)' }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--line)'; e.currentTarget.style.background = 'var(--bg-soft)' }}
                >
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                    style={{ background: 'rgba(42,29,20,0.06)' }}
                  >
                    <Briefcase size={20} style={{ color: 'var(--ink-warm)' }} />
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold text-sm" style={{ color: 'var(--ink-strong)' }}>
                      {intl.formatMessage({ id: 'onboarding.step1.no' })}
                    </p>
                    <p className="text-xs mt-0.5" style={{ color: 'var(--ink-muted)' }}>Ya tengo experiencia laboral</p>
                  </div>
                  <ChevronRight size={16} style={{ color: 'var(--ink-muted)' }} />
                </button>
              </div>
            </div>
          )}

          {/* PASO 2 */}
          {step === 'step2' && (
            <div className="space-y-6">
              <button
                onClick={() => setStep('step1')}
                className="flex items-center gap-1 text-sm transition-colors"
                style={{ color: 'var(--ink-muted)' }}
              >
                <ChevronLeft size={15} />
                Volver
              </button>

              <div className="space-y-2">
                <p className="kicker" style={{ color: 'var(--terra-500)' }}>Paso 2 de 2</p>
                <h2 className="text-2xl font-bold" style={{ color: 'var(--ink-strong)', letterSpacing: '-0.02em' }}>
                  {intl.formatMessage({ id: 'onboarding.step2.question' })}
                </h2>
                <p className="text-sm" style={{ color: 'var(--ink-muted)' }}>
                  {intl.formatMessage({ id: 'onboarding.step2.examples' })}
                </p>
              </div>

              <div className="grid grid-cols-3 gap-2 max-h-64 overflow-y-auto pr-1">
                {TRADE_CATEGORIES.map(({ value, label, Icon }) => {
                  const active = selectedTrade === value
                  return (
                    <button
                      key={value}
                      onClick={() => setSelectedTrade(value)}
                      className="flex flex-col items-center gap-1.5 p-3 rounded-xl border transition-all text-center"
                      style={{
                        borderColor: active ? 'var(--terra-500)' : 'var(--line)',
                        background:  active ? 'var(--terra-100)' : 'var(--bg-elevated)',
                      }}
                    >
                      <div
                        className="w-8 h-8 rounded-xl flex items-center justify-center"
                        style={{ background: active ? 'rgba(184,68,42,0.15)' : 'rgba(42,29,20,0.05)' }}
                      >
                        <Icon size={15} style={{ color: active ? 'var(--terra-500)' : 'var(--ink-warm)' }} />
                      </div>
                      <span className="text-[11px] font-medium leading-tight" style={{ color: active ? 'var(--terra-700)' : 'var(--ink-warm)' }}>
                        {label}
                      </span>
                    </button>
                  )
                })}
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
            <div
              className="absolute inset-0 rounded-2xl flex items-center justify-center"
              style={{ background: 'rgba(247,241,232,0.85)' }}
            >
              <div
                className="h-7 w-7 animate-spin rounded-full border-[3px]"
                style={{ borderColor: 'var(--bg-warm)', borderTopColor: 'var(--terra-500)' }}
              />
            </div>
          )}
        </div>

        <p className="text-center text-[11px] mt-6 font-mono uppercase tracking-widest" style={{ color: 'var(--ink-muted)' }}>
          Linku · DRTPE-Junín · Huancayo, Perú · 2026
        </p>
      </div>
    </div>
  )
}
