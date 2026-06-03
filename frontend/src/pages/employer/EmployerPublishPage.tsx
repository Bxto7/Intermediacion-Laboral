import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { CheckCircle, AlertCircle, Plus, X } from 'lucide-react'
import { useEmployerJobs } from '../../hooks/useEmployer'

const DISTRICTS = ['Huancayo', 'El Tambo', 'Chilca']
const MODALITIES = [
  { value: 'presencial', label: 'Presencial' },
  { value: 'remoto',     label: 'Remoto' },
  { value: 'mixto',      label: 'Mixto' },
]
const WORKER_TYPES = [
  { value: 'primer_empleo', label: 'Primer empleo (sin experiencia)' },
  { value: 'experiencia',   label: 'Profesional con experiencia' },
  { value: 'oficio',        label: 'Trabajador de oficio' },
  { value: 'all',           label: 'Cualquier perfil' },
]

const fieldStyle: React.CSSProperties = {
  border: '1px solid var(--line-strong)',
  background: 'var(--bg-soft)',
  color: 'var(--ink-strong)',
  borderRadius: '12px',
  fontSize: '14px',
  padding: '10px 14px',
  width: '100%',
  outline: 'none',
  fontFamily: 'inherit',
}

export const EmployerPublishPage: React.FC = () => {
  const navigate = useNavigate()
  const { createJob } = useEmployerJobs()

  const [title, setTitle]           = useState('')
  const [description, setDesc]      = useState('')
  const [district, setDistrict]     = useState('')
  const [modality, setModality]     = useState('')
  const [workerType, setWorkerType] = useState('')
  const [salaryMin, setSalaryMin]   = useState('')
  const [salaryMax, setSalaryMax]   = useState('')
  const [skillInput, setSkillInput] = useState('')
  const [skills, setSkills]         = useState<string[]>([])
  const [saving, setSaving]         = useState(false)
  const [error, setError]           = useState('')

  const onFocus = (e: React.FocusEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    e.currentTarget.style.borderColor = 'var(--terra-500)'
    e.currentTarget.style.boxShadow = '0 0 0 3px rgba(184,68,42,0.12)'
  }
  const onBlur = (e: React.FocusEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    e.currentTarget.style.borderColor = 'var(--line-strong)'
    e.currentTarget.style.boxShadow = 'none'
  }

  const addSkill = () => {
    const s = skillInput.trim()
    if (s && !skills.includes(s) && skills.length < 10) {
      setSkills(prev => [...prev, s])
      setSkillInput('')
    }
  }

  const removeSkill = (s: string) => setSkills(prev => prev.filter(x => x !== s))

  const handleSkillKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') { e.preventDefault(); addSkill() }
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (!title.trim())       { setError('El título es obligatorio'); return }
    if (!description.trim()) { setError('La descripción es obligatoria'); return }
    if (!district)           { setError('Selecciona un distrito'); return }
    if (!modality)           { setError('Selecciona la modalidad'); return }
    if (!workerType)         { setError('Selecciona el tipo de trabajador'); return }

    setSaving(true)
    try {
      await createJob({
        title: title.trim(),
        description: description.trim(),
        district,
        modality,
        salary_min: salaryMin ? Number(salaryMin) : null,
        salary_max: salaryMax ? Number(salaryMax) : null,
        worker_type_target: workerType,
        required_skills: skills,
        preferred_skills: [],
      })
      navigate('/employer/dashboard')
    } catch {
      setError('No se pudo publicar la oferta. Intenta de nuevo.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-5 py-2">
      <div>
        <h1 className="text-xl font-bold" style={{ color: 'var(--ink-strong)', letterSpacing: '-0.02em' }}>
          Publicar empleo
        </h1>
        <p className="text-sm mt-0.5" style={{ color: 'var(--ink-muted)' }}>
          Tu oferta quedará registrada en la Bolsa de Trabajo DRTPE-Junín
        </p>
      </div>

      <form onSubmit={submit} className="card-warm p-6 space-y-5">

        {/* Título */}
        <div>
          <label htmlFor="pub-title" className="block text-xs font-semibold mb-1.5" style={{ color: 'var(--ink-warm)' }}>
            Título del puesto *
          </label>
          <input
            id="pub-title"
            type="text"
            value={title}
            onChange={e => setTitle(e.target.value)}
            placeholder="Ej: Electricista residencial para El Tambo"
            maxLength={200}
            style={fieldStyle}
            onFocus={onFocus} onBlur={onBlur}
          />
        </div>

        {/* Descripción */}
        <div>
          <label htmlFor="pub-desc" className="block text-xs font-semibold mb-1.5" style={{ color: 'var(--ink-warm)' }}>
            Descripción *
          </label>
          <textarea
            id="pub-desc"
            value={description}
            onChange={e => setDesc(e.target.value)}
            placeholder="Describe las tareas, horario, requisitos, beneficios..."
            rows={4}
            maxLength={2000}
            style={{ ...fieldStyle, resize: 'none' }}
            onFocus={onFocus} onBlur={onBlur}
          />
          <p className="text-[11px] mt-0.5 text-right" style={{ color: 'var(--ink-muted)' }}>{description.length}/2000</p>
        </div>

        {/* Distrito + Modalidad */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="pub-district" className="block text-xs font-semibold mb-1.5" style={{ color: 'var(--ink-warm)' }}>Distrito *</label>
            <select id="pub-district" value={district} onChange={e => setDistrict(e.target.value)} style={fieldStyle} onFocus={onFocus} onBlur={onBlur}>
              <option value="">Seleccionar...</option>
              {DISTRICTS.map(d => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="pub-modality" className="block text-xs font-semibold mb-1.5" style={{ color: 'var(--ink-warm)' }}>Modalidad *</label>
            <select id="pub-modality" value={modality} onChange={e => setModality(e.target.value)} style={fieldStyle} onFocus={onFocus} onBlur={onBlur}>
              <option value="">Seleccionar...</option>
              {MODALITIES.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
            </select>
          </div>
        </div>

        {/* Tipo de trabajador */}
        <div>
          <p className="block text-xs font-semibold mb-1.5" style={{ color: 'var(--ink-warm)' }} id="worker-type-label">Perfil buscado *</p>
          <div className="grid grid-cols-2 gap-2" role="radiogroup" aria-labelledby="worker-type-label">
            {WORKER_TYPES.map(wt => (
              <button
                key={wt.value}
                type="button"
                role="radio"
                aria-checked={workerType === wt.value}
                onClick={() => setWorkerType(wt.value)}
                className="py-2.5 px-3 rounded-xl text-xs font-medium text-left transition-all cursor-pointer"
                style={{
                  border: `2px solid ${workerType === wt.value ? 'var(--terra-500)' : 'var(--line)'}`,
                  background: workerType === wt.value ? 'var(--terra-100)' : 'var(--bg-elevated)',
                  color: workerType === wt.value ? 'var(--terra-700)' : 'var(--ink-muted)',
                }}
              >
                {wt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Salario */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="pub-salary-min" className="block text-xs font-semibold mb-1.5" style={{ color: 'var(--ink-warm)' }}>
              Salario mínimo (S/.)
            </label>
            <input
              id="pub-salary-min"
              type="number" min="0" step="50"
              value={salaryMin}
              onChange={e => setSalaryMin(e.target.value)}
              placeholder="Opcional"
              style={fieldStyle}
              onFocus={onFocus} onBlur={onBlur}
            />
          </div>
          <div>
            <label htmlFor="pub-salary-max" className="block text-xs font-semibold mb-1.5" style={{ color: 'var(--ink-warm)' }}>
              Salario máximo (S/.)
            </label>
            <input
              id="pub-salary-max"
              type="number" min="0" step="50"
              value={salaryMax}
              onChange={e => setSalaryMax(e.target.value)}
              placeholder="Opcional"
              style={fieldStyle}
              onFocus={onFocus} onBlur={onBlur}
            />
          </div>
        </div>

        {/* Habilidades requeridas */}
        <div>
          <label htmlFor="pub-skill-input" className="block text-xs font-semibold mb-1.5" style={{ color: 'var(--ink-warm)' }}>
            Habilidades requeridas
          </label>
          <div className="flex gap-2">
            <input
              id="pub-skill-input"
              type="text"
              value={skillInput}
              onChange={e => setSkillInput(e.target.value)}
              onKeyDown={handleSkillKey}
              placeholder="Ej: carpintería, Excel, puntualidad..."
              style={{ ...fieldStyle, flex: 1 }}
              onFocus={onFocus} onBlur={onBlur}
            />
            <button type="button" onClick={addSkill} className="btn-secondary px-3.5 py-2 rounded-xl text-xs flex items-center gap-1">
              <Plus size={13} /> Agregar
            </button>
          </div>
          {skills.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-2" role="list" aria-label="Habilidades agregadas">
              {skills.map(s => (
                <span key={s} role="listitem" className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-full" style={{ background: 'var(--terra-100)', color: 'var(--terra-700)' }}>
                  {s}
                  <button
                    type="button"
                    onClick={() => removeSkill(s)}
                    aria-label={`Eliminar habilidad ${s}`}
                    className="cursor-pointer"
                  >
                    <X size={10} />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {error && (
          <div role="alert" className="flex items-start gap-2 rounded-xl px-3 py-2.5" style={{ background: 'rgba(184,68,42,0.08)', border: '1px solid rgba(184,68,42,0.2)' }}>
            <AlertCircle size={14} className="flex-shrink-0 mt-0.5" style={{ color: 'var(--terra-500)' }} />
            <p className="text-xs" style={{ color: 'var(--terra-700)' }}>{error}</p>
          </div>
        )}

        <div className="flex gap-3 pt-1">
          <button
            type="button"
            onClick={() => navigate('/employer/dashboard')}
            className="btn-secondary flex-1 py-3"
          >
            Cancelar
          </button>
          <button type="submit" disabled={saving} className="btn-primary flex-1 py-3 flex items-center justify-center gap-2">
            {saving ? 'Publicando...' : <><CheckCircle size={15} /> Publicar oferta</>}
          </button>
        </div>
      </form>
    </div>
  )
}
