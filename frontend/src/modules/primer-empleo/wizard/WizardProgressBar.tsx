import { useLocation, Link } from 'react-router-dom'
import { useIntl } from 'react-intl'

const STEPS = [
  { num: 1, labelKey: 'wizard.progress.step1' },
  { num: 2, labelKey: 'wizard.progress.step2' },
  { num: 3, labelKey: 'wizard.progress.step3' },
  { num: 4, labelKey: 'wizard.progress.step4' },
  { num: 5, labelKey: 'wizard.progress.step5' },
  { num: 6, labelKey: 'wizard.progress.step6' },
]

export const WizardProgressBar: React.FC = () => {
  const intl = useIntl()
  const location = useLocation()
  const match = location.pathname.match(/step\/(\d)/)
  const current = match ? parseInt(match[1]) : 1

  return (
    <div className="bg-white border-b border-gray-200 shadow-sm px-4 py-3">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between">
          {STEPS.map((s, i) => (
            <div key={s.num} className="flex items-center flex-1">
              <Link
                to={`/wizard/step/${s.num}`}
                className={`flex flex-col items-center gap-1 transition-all ${s.num <= current ? 'cursor-pointer' : 'pointer-events-none'}`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all ${
                  s.num < current ? 'bg-green-500 text-white'
                  : s.num === current ? 'bg-primary-600 text-white ring-4 ring-primary-100'
                  : 'bg-gray-100 text-gray-400'
                }`}>
                  {s.num < current ? '✓' : s.num}
                </div>
                <span className={`text-xs hidden sm:block ${s.num === current ? 'text-primary-600 font-semibold' : 'text-gray-400'}`}>
                  {intl.formatMessage({ id: s.labelKey })}
                </span>
              </Link>
              {i < STEPS.length - 1 && (
                <div className={`flex-1 h-0.5 mx-1 rounded-full ${s.num < current ? 'bg-green-400' : 'bg-gray-200'}`} />
              )}
            </div>
          ))}
        </div>
        <p className="text-xs text-gray-500 text-center mt-2">
          {intl.formatMessage({ id: 'wizard.progress.label' }, { current, total: 6 })}
        </p>
      </div>
    </div>
  )
}
