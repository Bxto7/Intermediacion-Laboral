import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://api:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://api:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // React core + router juntos (react-dom requiere react, Rollup los une de todas formas)
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          // Recharts es pesado (~400 kB) y solo se usa en admin
          'vendor-charts': ['recharts'],
          // Internacionalización
          'vendor-intl': ['react-intl'],
          // Formularios
          'vendor-forms': ['react-hook-form', 'zod', '@hookform/resolvers'],
          // Utilidades pequeñas agrupadas
          'vendor-utils': ['axios', 'ts-pattern', 'zustand'],
          // UI
          'vendor-icons': ['lucide-react'],
        },
      },
    },
    // Advertir en chunks > 400 kB (antes era 500 kB por defecto)
    chunkSizeWarningLimit: 400,
  },
})
