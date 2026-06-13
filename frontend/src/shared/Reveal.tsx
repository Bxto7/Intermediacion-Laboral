import { motion, useReducedMotion } from 'framer-motion'
import type { ReactNode } from 'react'

interface Props {
  children: ReactNode
  delay?: number
  y?: number
  className?: string
}

/**
 * Animación de entrada al hacer scroll (fade + subida suave).
 * Respeta prefers-reduced-motion: si está activo, no anima.
 * Duración 120–400ms, una sola vez por elemento.
 */
export const Reveal: React.FC<Props> = ({ children, delay = 0, y = 18, className }) => {
  const reduce = useReducedMotion()
  if (reduce) return <div className={className}>{children}</div>
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.2 }}
      transition={{ duration: 0.38, delay, ease: [0.16, 1, 0.3, 1] }}
    >
      {children}
    </motion.div>
  )
}
