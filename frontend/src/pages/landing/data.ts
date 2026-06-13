// Datos de empleos de ejemplo
export const JOBS = [
  { id: 1, company: 'Volcan Mining', logo: 'VM', logoColor: '#0f6e6e', title: 'Operario planta concentradora', salary: 'S/. 2,200 – 2,800', tags: ['Full-time', 'Minería'], location: 'Yauli', category: 'Minería', verified: true },
  { id: 2, company: 'Caja Huancayo', logo: 'CH', logoColor: '#c9961f', title: 'Analista soporte TI', salary: 'S/. 2,500 – 3,200', tags: ['Full-time', 'Banca'], location: 'Huancayo', category: 'Banca', verified: true },
  { id: 3, company: 'Constructora Wari', logo: 'CW', logoColor: '#7a8c5c', title: 'Maestro de obra', salary: 'S/. 3,000 – 4,000', tags: ['Full-time', 'Construcción'], location: 'El Tambo', category: 'Construcción', verified: true },
  { id: 4, company: 'Hidrandina', logo: 'HD', logoColor: '#b8442a', title: 'Técnico electricista', salary: 'S/. 1,800 – 2,400', tags: ['Full-time', 'Energía'], location: 'Huancayo', category: 'TI', verified: true },
  { id: 5, company: 'Agroindustria Junín', logo: 'AJ', logoColor: '#7a8c5c', title: 'Operario de campo', salary: 'S/. 1,200 – 1,600', tags: ['Part-time', 'Agricultura'], location: 'Tarma', category: 'Minería', verified: false },
  { id: 6, company: 'Doe Run Perú', logo: 'DR', logoColor: '#147a7a', title: 'Supervisor de planta', salary: 'S/. 4,500 – 5,800', tags: ['Full-time', 'Minería'], location: 'La Oroya', category: 'Minería', verified: true },
]

export const CATEGORIES = ['Todos', 'Minería', 'Banca', 'Construcción', 'TI', 'Gastronomía']

export const COMPANIES = [
  'Cementos Andinos', 'Doe Run', 'Hidrandina', 'Volcan Mining',
  'Agroindustria', 'Caja Huancayo', 'Constructora Wari', 'Peruarbo',
  'Electro Centro', 'SEDAM Huancayo', 'Coop. Tocache', 'SEDAPAL Junín',
]

export const TESTIMONIALS = [
  { name: 'María Quispe', role: 'Electricista · El Tambo', quote: 'Encontré trabajo en dos semanas. El sistema me sugirió empleos que realmente coincidían con mis habilidades.', color: '#b8442a', initial: 'MQ' },
  { name: 'Carlos Huamán', role: 'Analista TI · Huancayo', quote: 'El CV generado con IA me ayudó a destacar. Tres empresas me llamaron la misma semana.', color: '#0f6e6e', initial: 'CH' },
  { name: 'Rosa Lazo', role: 'Cocinera · Tarma', quote: 'Como oficio, nunca pensé tener un perfil digital. Ahora mis clientes me encuentran fácilmente.', color: '#7a8c5c', initial: 'RL' },
]
