import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { useIntl } from 'react-intl'
import { useWizardStore } from '../../../../store/wizardStore'
import { WizardNavigation } from '../WizardNavigation'
import apiClient from '../../../../api/client'

const schema = z.object({
  district: z.string().min(1, 'Selecciona tu distrito'),
})
type F = z.infer<typeof schema>

const DISTRICTS = ['Huancayo', 'El Tambo', 'Chilca']

export const Step1PersonalData: React.FC = () => {
  const intl = useIntl()
  const { setAnswer, answers } = useWizardStore()
  const { register, handleSubmit, formState: { errors } } = useForm<F>({
    resolver: zodResolver(schema),
    defaultValues: { district: answers.district || '' },
  })

  const onNext = async (data: F) => {
    setAnswer('district', data.district)
    await apiClient.post('/wizard/step/1', { step: 1, answers: { district: data.district } }).catch(() => null)
  }

  return (
    <form onSubmit={handleSubmit(() => {})}>
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold" style={{ color: 'var(--ink-strong)' }}>
            {intl.formatMessage({ id: 'wizard.step1.title' })}
          </h2>
          <p className="text-sm mt-1" style={{ color: 'var(--ink-muted)' }}>
            {intl.formatMessage({ id: 'wizard.step1.subtitle' })}
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: 'var(--ink-warm)' }}>
            {intl.formatMessage({ id: 'wizard.step1.district_label' })}
          </label>
          <div className="grid grid-cols-3 gap-3">
            {DISTRICTS.map((d) => {
              const active = answers.district === d
              return (
                <label key={d} className="cursor-pointer">
                  <input {...register('district')} type="radio" value={d} className="sr-only" />
                  <div
                    className="p-4 rounded-xl text-center transition-all"
                    style={{
                      border: `2px solid ${active ? 'var(--terra-500)' : 'var(--line)'}`,
                      background: active ? 'var(--terra-100)' : 'var(--bg-elevated)',
                    }}
                  >
                    <span className="text-sm font-medium" style={{ color: active ? 'var(--terra-700)' : 'var(--ink-warm)' }}>
                      {d}
                    </span>
                  </div>
                </label>
              )
            })}
          </div>
          {errors.district && (
            <p className="text-xs mt-1" style={{ color: 'var(--terra-500)' }}>{errors.district.message}</p>
          )}
        </div>

        <WizardNavigation step={1} onNext={handleSubmit(onNext)} />
      </div>
    </form>
  )
}
