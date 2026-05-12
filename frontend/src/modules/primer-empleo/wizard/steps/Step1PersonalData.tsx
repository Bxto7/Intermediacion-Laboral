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
          <h2 className="text-2xl font-bold text-gray-900">{intl.formatMessage({ id: 'wizard.step1.title' })}</h2>
          <p className="text-gray-500 text-sm mt-1">{intl.formatMessage({ id: 'wizard.step1.subtitle' })}</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            {intl.formatMessage({ id: 'wizard.step1.district_label' })}
          </label>
          <div className="grid grid-cols-3 gap-3">
            {DISTRICTS.map((d) => (
              <label key={d} className="cursor-pointer">
                <input {...register('district')} type="radio" value={d} className="sr-only" />
                <div className={`p-4 rounded-xl border-2 text-center transition-all hover:border-primary-400 ${
                  answers.district === d ? 'border-primary-500 bg-primary-50' : 'border-gray-200'
                }`}>
                  <span className="text-2xl block mb-1">
                    {d === 'Huancayo' ? '🏔️' : d === 'El Tambo' ? '🌆' : '🏘️'}
                  </span>
                  <span className="text-sm font-medium text-gray-700">{d}</span>
                </div>
              </label>
            ))}
          </div>
          {errors.district && <p className="text-red-500 text-xs mt-1">{errors.district.message}</p>}
        </div>

        <WizardNavigation step={1} onNext={handleSubmit(onNext)} />
      </div>
    </form>
  )
}
