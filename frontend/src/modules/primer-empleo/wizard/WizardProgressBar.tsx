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
    <div className="px-4 py-3" style={{ background: 'var(--bg-elevated)', borderBottom: '1px solid var(--line)' }}>
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between">
          {STEPS.map((s, i) => (
            <div key={s.num} className="flex items-center flex-1">
              <Link
                to={`/wizard/step/${s.num}`}
                className={`flex flex-col items-center gap-1 transition-all ${s.num <= current ? 'cursor-pointer' : 'pointer-events-none'}`}
              >
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all"
                  style={{
                    background: s.num < current ? 'var(--olive)' : s.num === current ? 'var(--terra-500)' : 'var(--bg-warm)',
                    color: s.num < current || s.num === current ? '#fff' : 'var(--ink-muted)',
                    boxShadow: s.num === current ? '0 0 0 4px rgba(184,68,42,0.18)' : 'none',
                  }}
                >
                  {s.num < current ? '✓' : s.num}
                </div>
                <span
                  className="text-xs hidden sm:block"
                  style={{ color: s.num === current ? 'var(--terra-500)' : 'var(--ink-muted)', fontWeight: s.num === current ? 600 : 400 }}
                >
                  {intl.formatMessage({ id: s.labelKey })}
                </span>
              </Link>
              {i < STEPS.length - 1 && (
                <div
                  className="flex-1 h-0.5 mx-1 rounded-full"
                  style={{ background: s.num < current ? 'var(--olive)' : 'var(--bg-warm)' }}
                />
              )}
            </div>
          ))}
        </div>
        <p className="text-xs text-center mt-2" style={{ color: 'var(--ink-muted)' }}>
          {intl.formatMessage({ id: 'wizard.progress.label' }, { current, total: 6 })}
        </p>
      </div>
    </div>
  )
}
