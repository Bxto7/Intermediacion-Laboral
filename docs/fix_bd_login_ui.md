Lee el CLAUDE.md en la raíz antes de tocar cualquier archivo. Para el backend usa Bash. Para el frontend también usa Bash.

Tienes tres bloques de trabajo. Hazlos en orden: primero el backend (BD y login), luego las librerías y diseño del frontend.

---

## BLOQUE A — ARREGLAR LA BASE DE DATOS Y EL LOGIN (hacer primero)

### A1 — El .env tiene AES_KEY en texto plano pero el código espera base64

Archivo: backend/.env

El problema es que el archivo tiene:
  AES_KEY=cambia-esto-exactamente-32bytes!

Pero app/core/config.py tiene un validator que hace base64.b64decode(AES_KEY) y verifica que el resultado tenga exactamente 32 bytes. La cadena "cambia-esto-exactamente-32bytes!" tiene 32 bytes, pero no está en base64, así que el decode falla y el backend no arranca.

Reemplaza esa línea en backend/.env por:
  AES_KEY=Y2FtYmlhLWVzdG8tZXhhY3RhbWVudGUtMzJieXRlcyE=

Eso es base64("cambia-esto-exactamente-32bytes!") y decodifica a exactamente 32 bytes.

### A2 — RegisterRequest no tiene los campos dni ni full_name que el frontend envía

Archivos: backend/app/schemas/auth.py y backend/app/api/v1/auth.py

El frontend (RegisterPage.tsx) envía al POST /auth/register:
  { email, password, role, dni, full_name }

Pero RegisterRequest en app/schemas/auth.py solo tiene email, password y role. Los campos dni y full_name son ignorados silenciosamente. El registro funciona pero crea un usuario sin datos de identidad, y el worker_profile queda con valores placeholder para siempre.

Corrección en app/schemas/auth.py — agrega los campos a RegisterRequest:
```python
class RegisterRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole = UserRole.WORKER
    full_name: str = Field(default="", min_length=0, max_length=100)
    dni: str = Field(default="", min_length=0, max_length=8)
```

Corrección en app/api/v1/auth.py — en el endpoint POST /auth/register, después de crear el User y hacer flush, si body.full_name y body.dni están presentes, guárdalos temporalmente en Redis para que el onboarding los use. Agrega esto después del await db.flush():

```python
# Guardar datos de identidad para el onboarding
if body.full_name or body.dni:
    redis = get_redis()
    await redis.setex(
        f"reg_identity:{user.id}",
        3600,
        f"{body.full_name}|{body.dni}"
    )
```

Corrección en app/services/onboarding/detector.py — en la función create_worker_profile, antes de crear el Worker, intenta leer los datos de identidad de Redis:

```python
async def create_worker_profile(
    user_id: str,
    worker_type: WorkerType,
    trade_category: TradeCategory | None,
    db: AsyncSession,
) -> Worker:
    from app.core.redis_client import get_redis
    from app.core.security import encrypt_field

    # Intentar recuperar datos de identidad del registro
    redis = get_redis()
    identity_raw = await redis.get(f"reg_identity:{user_id}")
    full_name_plain = "pendiente"
    dni_plain = "00000000"
    if identity_raw:
        parts = identity_raw.split("|", 1)
        if len(parts) == 2:
            full_name_plain = parts[0] or "pendiente"
            dni_plain = parts[1] or "00000000"
        await redis.delete(f"reg_identity:{user_id}")

    username = await _generate_unique_username(full_name_plain, db)
    worker = Worker(
        user_id=user_id,
        worker_type=worker_type.value,
        full_name=encrypt_field(full_name_plain),
        dni=encrypt_field(dni_plain),
        trade_category=trade_category.value if trade_category else None,
        profile_completeness=0,
        username=username,
    )
    db.add(worker)
    await db.flush()
    # ... resto igual
```

### A3 — Verificar y aplicar migraciones pendientes

Ejecuta estos comandos en orden y muéstrame la salida completa de cada uno:

```bash
# 1. Verificar que el contenedor de BD está corriendo
docker-compose ps

# 2. Si no está corriendo, levantarlo
docker-compose up -d db redis

# 3. Esperar que esté healthy
sleep 15

# 4. Verificar estado de migraciones
docker-compose exec api alembic history --verbose 2>/dev/null || \
  docker-compose run --rm api alembic history --verbose

# 5. Aplicar migraciones pendientes
docker-compose exec api alembic upgrade head 2>/dev/null || \
  docker-compose run --rm api alembic upgrade head

# 6. Reiniciar el backend para que tome el nuevo .env
docker-compose restart api celery_worker

# 7. Verificar que arranca sin errores
sleep 10
docker-compose logs api --tail=30

# 8. Probar el health endpoint
curl -s http://localhost:8000/api/v1/health | python3 -m json.tool

# 9. Probar el login con usuario de prueba
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@linku.pe","password":"test12345","role":"worker","full_name":"Juan Pérez","dni":"12345678"}' \
  | python3 -m json.tool

# 10. Probar login
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@linku.pe","password":"test12345"}' \
  | python3 -m json.tool
```

Si el paso 9 devuelve access_token y el paso 10 también, el login está funcionando. Si hay errores, corrígelos antes de continuar con el Bloque B.

### A4 — Crear usuario admin de prueba para la DRTPE

Una vez que el login funciona, crea un script backend/scripts/create_admin.py que registre un usuario admin:

```python
"""Crea usuario admin DRTPE-Junín para pruebas. Ejecutar una sola vez."""
import asyncio
import sys
sys.path.insert(0, "/app")

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == "admin@drtpe-junin.gob.pe"))
        if result.scalar_one_or_none():
            print("Admin ya existe")
            return
        admin = User(
            email="admin@drtpe-junin.gob.pe",
            hashed_password=hash_password("Admin2026!"),
            role="admin",
            is_active=True,
            email_verified=True,
        )
        db.add(admin)
        await db.commit()
        print("Admin creado: admin@drtpe-junin.gob.pe / Admin2026!")

asyncio.run(main())
```

Ejecútalo:
```bash
docker-compose exec api python scripts/create_admin.py
```

---

## BLOQUE B — INSTALAR LIBRERÍAS UI Y ACTUALIZAR EL DISEÑO

### B1 — Instalar dependencias

```bash
cd frontend

# shadcn/ui — componentes accesibles que se integran con Tailwind
npx shadcn@latest init --defaults

# Instalar los componentes de shadcn que el proyecto necesita
npx shadcn@latest add dialog tabs toast tooltip badge select skeleton sheet dropdown-menu

# Framer Motion — animaciones
npm install framer-motion

# React Three Fiber — gráficos 3D (solo para el panel admin)
npm install three @react-three/fiber @react-three/drei
npm install --save-dev @types/three
```

Verifica que todo instaló sin errores:
```bash
npm run build 2>&1 | tail -20
```

### B2 — Ampliar la paleta de colores y agregar gradientes

Archivo: frontend/src/index.css

Agrega estas variables nuevas dentro del bloque :root, después de las existentes:

```css
/* ── Terracota — escala completa ── */
--terra-50:  #fdf2ee;
--terra-200: #f5c4b0;
--terra-300: #eba07e;
--terra-600: #a8421e;
--terra-800: #6b2a12;
--terra-900: #4d1c0a;

/* ── Azul — escala completa ── */
--blue-50:   #eef4fa;
--blue-200:  #b8d0e8;
--blue-300:  #7aaac8;
--blue-400:  #4d82a8;
--blue-500:  #2d5a82;
--blue-600:  #1e3f5e;
--blue-700:  #152d42;

/* ── Oliva — escala completa ── */
--olive-50:  #f3f5ee;
--olive-200: #c8d4b0;
--olive-300: #a8bc84;
--olive-400: #8fa06e;
--olive-700: #434e33;

/* ── Dorado — escala completa ── */
--gold-50:   #fdf7ed;
--gold-200:  #f0d49a;
--gold-300:  #e4bc6a;
--gold-400:  #d4a44a;
--gold-600:  #956d28;

/* ── Superficies para secciones oscuras ── */
--surface-dark-1:    rgba(255,255,255,0.04);
--surface-dark-2:    rgba(255,255,255,0.07);
--surface-dark-3:    rgba(255,255,255,0.11);
--surface-dark-hover:rgba(255,255,255,0.16);

/* ── Bordes para secciones oscuras ── */
--line-dark-1: rgba(255,255,255,0.08);
--line-dark-2: rgba(255,255,255,0.16);
--line-dark-3: rgba(255,255,255,0.28);

/* ── Colores nuevos ── */
--purple-500: #6c4fa3;
--purple-100: rgba(108,79,163,0.10);
--red-500:    #c0392b;
--red-100:    rgba(192,57,43,0.10);

/* ── Neutros cálidos adicionales ── */
--warm-50:  #fefdfb;
--warm-200: #f7edd8;
--warm-300: #ede0c4;
--warm-400: #ddd0b8;
--warm-500: #c8b89e;

/* ══════════════════════════════
   GRADIENTES — uso: background: var(--grad-X)
══════════════════════════════ */

/* Hero landing — cálido editorial */
--grad-hero: linear-gradient(135deg, #fdf6ea 0%, #f5e8d0 40%, #ebe0cd 100%);

/* Mesh gradient para el hero (efecto moderno) */
--grad-mesh:
  radial-gradient(ellipse at 20% 20%, rgba(194,86,46,0.10) 0%, transparent 55%),
  radial-gradient(ellipse at 80% 75%, rgba(45,90,130,0.08) 0%, transparent 55%),
  radial-gradient(ellipse at 55% 50%, rgba(184,137,58,0.05) 0%, transparent 65%),
  #f7f1e8;

/* Secciones oscuras editoriales */
--grad-dark:    linear-gradient(160deg, #2d1f14 0%, #3d2818 50%, #4a3120 100%);
--grad-dark-2:  linear-gradient(135deg, #1a1208 0%, #2d1f14 100%);

/* Panel auth (Register / Login) */
--grad-auth:    linear-gradient(160deg, #1a2f47 0%, #2d5a82 60%, #3a6b96 100%);

/* Marketplace hero */
--grad-market:  linear-gradient(160deg, #2d1f14 0%, #3d2818 60%, #5a2e18 100%);

/* Dashboard PRIMER_EMPLEO */
--grad-primer:  linear-gradient(135deg, #fdf6ea 0%, #fce8d5 100%);

/* Portfolio OFICIO */
--grad-oficio:  linear-gradient(135deg, #3d2818 0%, #5a3d2b 100%);
--grad-portfolio:linear-gradient(135deg, #5d6b46 0%, #7a8c5c 100%);

/* Badge DRTPE institucional */
--grad-drtpe:   linear-gradient(135deg, #1e3a5f 0%, #2d5a82 100%);

/* Stats cards dorado */
--grad-gold:    linear-gradient(135deg, #b8893a 0%, #e8b45a 100%);

/* Cards de matching ML */
--grad-ml:      linear-gradient(135deg, #6c4fa3 0%, #8b6cc4 100%);

/* Glow de fondo (usar con opacity baja) */
--grad-glow-terra: radial-gradient(ellipse at center, rgba(194,86,46,0.15) 0%, transparent 70%);
--grad-glow-blue:  radial-gradient(ellipse at center, rgba(45,90,130,0.12) 0%, transparent 70%);
```

### B3 — Mejorar el panel oscuro de RegisterPage con el gradiente correcto

Archivo: frontend/src/pages/RegisterPage.tsx

Localiza el panel azul derecho del registro (el div con `background: 'linear-gradient(160deg, #1e3a5f 0%, #2d5a82 100%)'`) y actualízalo para usar el gradiente de la variable y agregar un efecto mesh más rico:

```tsx
style={{ background: 'var(--grad-auth)', position: 'relative', overflow: 'hidden' }}
```

Además agrega más elementos decorativos dentro del panel para darle profundidad. Localiza el bloque de glows existente (los dos divs con `absolute` y `blur-3xl`) y reemplázalos por:

```tsx
{/* Glows de fondo */}
<div className="absolute -top-20 -left-20 w-72 h-72 rounded-full opacity-20 blur-3xl pointer-events-none"
  style={{ background: 'var(--grad-glow-blue)' }} />
<div className="absolute -bottom-20 -right-20 w-80 h-80 rounded-full opacity-15 blur-3xl pointer-events-none"
  style={{ background: 'var(--grad-glow-terra)' }} />
<div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 rounded-full opacity-10 blur-3xl pointer-events-none"
  style={{ background: 'radial-gradient(ellipse, rgba(122,140,92,0.4) 0%, transparent 70%)' }} />

{/* Grid de puntos decorativo */}
<div className="absolute inset-0 opacity-5 pointer-events-none"
  style={{
    backgroundImage: 'radial-gradient(circle, rgba(255,255,255,0.6) 1px, transparent 1px)',
    backgroundSize: '28px 28px',
  }} />
```

### B4 — Agregar gradiente mesh al hero de la landing

Archivo: frontend/src/pages/LandingPage.tsx

Localiza la sección hero principal (el primer `<section>` con `pt-32`). Agrega este fondo al div contenedor principal de la página (el que tiene `className="glow-bg grain min-h-screen"`):

```tsx
// Cambia el className y agrega style:
<div
  className="grain min-h-screen"
  style={{ background: 'var(--grad-mesh)' }}
>
```

Esto reemplaza el fondo plano por el mesh gradient que da profundidad con los glows de terracota, azul y dorado.

### B5 — Gráfico 3D para el panel admin DRTPE

Crea el archivo frontend/src/admin/KPIGlobe.tsx con un gráfico de esferas 3D que visualiza los KPIs del sistema. Este componente se usa en el AdminDashboard solo en la sección de estadísticas generales:

```tsx
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Text, Sphere } from '@react-three/drei'
import { useRef } from 'react'
import * as THREE from 'three'

interface KPINode {
  label: string
  value: number
  color: string
  position: [number, number, number]
}

const NODE_DATA: KPINode[] = [
  { label: 'Trabajadores', value: 2400, color: '#c2562e', position: [0, 0, 0] },
  { label: 'Ofertas',      value: 180,  color: '#2d5a82', position: [3, 1, -1] },
  { label: 'Contratos',    value: 95,   color: '#7a8c5c', position: [-2.5, 1.5, 1] },
  { label: 'Matching',     value: 87,   color: '#b8893a', position: [1.5, -2, 1.5] },
  { label: 'Empresas',     value: 340,  color: '#6c4fa3', position: [-1.5, -1.5, -2] },
]

const FloatingNode = ({ node }: { node: KPINode }) => {
  const meshRef = useRef<THREE.Mesh>(null)
  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.position.y = node.position[1] + Math.sin(state.clock.elapsedTime + node.position[0]) * 0.15
    }
  })
  const scale = 0.3 + (node.value / 2400) * 0.7

  return (
    <group position={node.position}>
      <Sphere ref={meshRef} args={[scale, 32, 32]}>
        <meshStandardMaterial color={node.color} roughness={0.2} metalness={0.4} />
      </Sphere>
      <Text
        position={[0, scale + 0.3, 0]}
        fontSize={0.22}
        color="white"
        anchorX="center"
        anchorY="bottom"
      >
        {node.label}
      </Text>
      <Text
        position={[0, scale + 0.05, 0]}
        fontSize={0.18}
        color={node.color}
        anchorX="center"
        anchorY="top"
      >
        {node.value.toLocaleString()}
      </Text>
    </group>
  )
}

export const KPIGlobe: React.FC = () => (
  <div style={{ width: '100%', height: 340, borderRadius: 16, overflow: 'hidden', background: 'linear-gradient(160deg, #1a1208 0%, #2d1f14 100%)' }}>
    <Canvas camera={{ position: [0, 0, 8], fov: 50 }}>
      <ambientLight intensity={0.4} />
      <pointLight position={[10, 10, 10]} intensity={1.2} color="#c2562e" />
      <pointLight position={[-10, -5, -5]} intensity={0.6} color="#2d5a82" />
      {NODE_DATA.map(n => <FloatingNode key={n.label} node={n} />)}
      <OrbitControls enableZoom={false} autoRotate autoRotateSpeed={0.8} />
    </Canvas>
  </div>
)
```

Agrega este componente al AdminDashboard. En frontend/src/admin/AdminDashboard.tsx, importa KPIGlobe con lazy loading:

```tsx
const KPIGlobe = lazy(() => import('./KPIGlobe').then(m => ({ default: m.KPIGlobe })))
```

Y agrégalo en la sección de estadísticas del dashboard, dentro de un Suspense:

```tsx
<div className="card-warm p-4 space-y-3">
  <h3 className="font-semibold text-sm" style={{ color: 'var(--ink-strong)' }}>
    Vista de red — KPIs del sistema
  </h3>
  <Suspense fallback={<div style={{ height: 340, display: 'grid', placeItems: 'center' }}><LoadingSpinner /></div>}>
    <KPIGlobe />
  </Suspense>
</div>
```

### B6 — Usar Framer Motion en el wizard de PRIMER_EMPLEO

Archivo: frontend/src/modules/primer-empleo/wizard/WizardLayout.tsx

Importa motion al inicio:
```tsx
import { motion, AnimatePresence } from 'framer-motion'
```

Envuelve el contenido del paso actual con AnimatePresence y motion.div para que cada paso entre con una animación suave. Localiza el lugar donde se renderiza el step actual y reemplázalo por:

```tsx
<AnimatePresence mode="wait">
  <motion.div
    key={currentStep}
    initial={{ opacity: 0, x: 24 }}
    animate={{ opacity: 1, x: 0 }}
    exit={{ opacity: 0, x: -24 }}
    transition={{ duration: 0.22, ease: 'easeInOut' }}
  >
    {/* contenido del step actual */}
  </motion.div>
</AnimatePresence>
```

---

## VERIFICACIÓN FINAL

Ejecuta estos comandos y muéstrame la salida de cada uno:

```bash
# Backend
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@linku.pe","password":"test12345"}' | python3 -m json.tool

# Frontend — sin errores TypeScript
cd frontend && npx tsc --noEmit 2>&1 | head -20

# Frontend — build exitoso
npm run build 2>&1 | tail -10
```

El sprint de corrección está completo cuando:
1. El login devuelve access_token sin errores.
2. `npx tsc --noEmit` pasa sin errores de tipos.
3. `npm run build` termina exitosamente.
4. El panel admin muestra el KPIGlobe con las esferas 3D.
5. El wizard de PRIMER_EMPLEO tiene animación de transición entre pasos.
