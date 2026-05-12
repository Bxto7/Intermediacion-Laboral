import { NavBar } from '../shared/NavBar'
import { BriefcaseFilled } from '../shared/BriefcaseIcon'
import { useAuthContext } from '../context/AuthContext'

export const EmployerDashboard: React.FC = () => {
  const { user } = useAuthContext()
  const initial = user?.email?.charAt(0).toUpperCase() ?? 'E'

  return (
    <div className="min-h-screen bg-warm-50 pb-16">
      <NavBar />
      <div className="max-w-6xl mx-auto px-5 py-8 space-y-6">

        {/* ── BANNER DRTPE ── */}
        <div className="card-warm relative overflow-hidden flex flex-col sm:flex-row items-center justify-between p-6 sm:p-8"
             style={{ background: 'linear-gradient(135deg, #1e3a5f 0%, #2d5a82 100%)', border: 'none' }}>
          <div className="absolute top-0 right-0 w-64 h-64 bg-white opacity-5 rounded-full blur-3xl transform translate-x-1/3 -translate-y-1/3 pointer-events-none" />
          
          <div className="relative z-10 flex items-center gap-5">
            <div className="w-14 h-14 rounded-full bg-white/20 flex items-center justify-center flex-shrink-0 border border-white/20">
              <span className="text-white text-xl font-bold">{initial}</span>
            </div>
            <div>
              <p className="text-blue-100 text-sm">Bienvenido de nuevo</p>
              <h1 className="text-2xl font-bold text-white tracking-tight">{user?.email}</h1>
            </div>
          </div>
          
          <button className="mt-6 sm:mt-0 bg-white text-blue-900 font-semibold text-sm px-6 py-3 rounded-xl hover:bg-blue-50 transition-colors">
            + Publicar empleo
          </button>
        </div>

        {/* ── MÉTRICAS ── */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { label: 'Ofertas Activas', val: '12', icon: 'M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z', c: 'text-primary-600', bg: 'bg-primary-50' },
            { label: 'Candidatos Nuevos', val: '48', icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z', c: 'text-drtpe-600', bg: 'bg-drtpe-50' },
            { label: 'Efectividad', val: '84%', icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z', c: 'text-olive-600', bg: 'bg-olive-50' },
          ].map(m => (
            <div key={m.label} className="card-warm p-5 flex items-center gap-4">
              <div className={`p-3 rounded-xl ${m.bg} ${m.c}`}>
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d={m.icon} />
                </svg>
              </div>
              <div>
                <p className="text-bark-500 text-sm font-medium">{m.label}</p>
                <p className="text-2xl font-bold text-bark-900">{m.val}</p>
              </div>
            </div>
          ))}
        </div>

        {/* ── MAIN CONTENT (OFERTAS) ── */}
        <div className="card-warm p-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
            <div>
              <h2 className="text-lg font-bold text-bark-900 tracking-tight">Ofertas publicadas</h2>
              <p className="text-sm text-bark-500 mt-1">Gestiona tus vacantes y revisa candidatos postulados.</p>
            </div>
            <span className="tag-warm">0 activas</span>
          </div>

          {/* Empty state con ilustración */}
          <div className="text-center py-14 space-y-4">
            <div className="w-16 h-16 mx-auto rounded-2xl bg-warm-100 border border-warm-200 flex items-center justify-center">
              <BriefcaseFilled className="w-8 h-8 text-bark-300" />
            </div>
            <div>
              <p className="font-semibold text-bark-700">Aún no tienes ofertas publicadas</p>
              <p className="text-bark-400 text-sm mt-1">Publica tu primera oferta para comenzar a recibir postulantes</p>
            </div>
            <button className="btn-primary text-sm px-6 py-2.5">
              Publicar primera oferta
            </button>
          </div>
        </div>

        {/* ── Tip DRTPE ── */}
        <div className="bg-primary-50 border border-primary-200 rounded-2xl p-5 flex items-start gap-4">
          <div className="w-9 h-9 rounded-xl bg-primary-600 flex items-center justify-center flex-shrink-0">
            <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <p className="font-semibold text-primary-800 text-sm">Plataforma oficial DRTPE-Junín</p>
            <p className="text-primary-700 text-xs mt-0.5 leading-relaxed">
              Al publicar aquí, tus ofertas quedan registradas en la Bolsa de Trabajo oficial de la Dirección Regional de Trabajo y Promoción del Empleo de Junín.
            </p>
          </div>
        </div>

      </div>
    </div>
  )
}
