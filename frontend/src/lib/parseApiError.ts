/** Traduce errores del API (incluido el 422 de FastAPI/Pydantic) a un mensaje claro en español. */

const FIELD_LABEL: Record<string, string> = {
  title: 'El título',
  description: 'La descripción',
  email: 'El correo',
  password: 'La contraseña',
  full_name: 'El nombre',
  dni: 'El DNI',
}

function humanizeDetail(d: { loc?: (string | number)[]; msg?: string; type?: string }): string {
  const field = String(d.loc?.[d.loc.length - 1] ?? '')
  const label = FIELD_LABEL[field] ?? 'Este campo'
  switch (d.type) {
    case 'string_too_long': {
      const max = d.msg?.match(/at most (\d+)/)?.[1]
      return `${label} es demasiado larga${max ? ` (máximo ${max} caracteres)` : ''}.`
    }
    case 'string_too_short': {
      const min = d.msg?.match(/at least (\d+)/)?.[1]
      return `${label} es demasiado corta${min ? ` (mínimo ${min} caracteres)` : ''}.`
    }
    case 'missing':
      return `${label} es obligatorio.`
    case 'value_error':
    case 'string_pattern_mismatch':
      return `${label} no tiene un formato válido.`
    default:
      return `${label}: ${d.msg ?? 'dato inválido'}.`
  }
}

export function parseApiError(err: unknown, fallback = 'No se pudo completar la acción. Intenta de nuevo.'): string {
  const resp = (err as { response?: { status?: number; data?: { detail?: unknown } } })?.response
  const detail = resp?.data?.detail

  if (Array.isArray(detail) && detail.length > 0) {
    return humanizeDetail(detail[0] as { loc?: (string | number)[]; msg?: string; type?: string })
  }
  if (typeof detail === 'string') return detail
  if (resp?.status === 429) return 'Demasiados intentos. Espera unos minutos.'
  if (resp?.status === 401) return 'Tu sesión expiró. Vuelve a iniciar sesión.'
  if (resp?.status === 413) return 'El archivo es demasiado grande.'
  return fallback
}
