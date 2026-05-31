import apiClient from '../api/client'

/**
 * Descarga el CV del trabajador como PDF.
 *
 * El endpoint /cv/download/{id} requiere el token JWT en la cabecera
 * Authorization. Por eso NO se puede abrir como enlace directo (el navegador
 * no envía el token de localStorage) — hay que pedirlo con apiClient, que sí
 * adjunta el Bearer, y descargar el blob resultante.
 */
export async function downloadCV(workerId: string): Promise<void> {
  const res = await apiClient.get(`/cv/download/${workerId}`, {
    responseType: 'blob',
  })
  const blob = new Blob([res.data], { type: 'application/pdf' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'mi-cv-linku.pdf'
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 10000)
}
