import { useNavigate } from 'react-router-dom'
import { useIntl } from 'react-intl'

interface Props {
  step: number
  onNext?: () => void | Promise<void>
  isLoading?: boolean
  disabled?: boolean
}

export const WizardNavigation: React.FC<Props> = ({ step, onNext, isLoading, disabled }) => {
  const intl = useIntl()
  const navigate = useNavigate()

  const handleNext = async () => {
    if (onNext) await onNext()
    if (step < 6) navigate(`/wizard/step/${step + 1}`)
    else navigate('/dashboard')
  }

  return (
    <div className="flex items-center justify-between pt-4 border-t border-gray-100">
      {step > 1 ? (
        <button
          onClick={() => navigate(`/wizard/step/${step - 1}`)}
          className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 transition-colors"
        >
          ← {intl.formatMessage({ id: 'common.back' })}
        </button>
      ) : <div />}
      <button
        onClick={handleNext}
        disabled={isLoading || disabled}
        className="flex items-center gap-2 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white font-semibold px-6 py-2.5 rounded-xl transition-colors shadow-sm"
      >
        {isLoading && <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />}
        {step === 6 ? 'Finalizar' : 'Siguiente →'}
      </button>
    </div>
  )
}
