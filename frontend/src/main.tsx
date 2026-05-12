import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { IntlProvider } from 'react-intl'
import { AuthProvider } from './context/AuthContext'
import { WorkerProvider } from './context/WorkerContext'
import App from './App.tsx'
import messages from './i18n/es-PE.json'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <IntlProvider locale="es-PE" messages={messages} defaultLocale="es-PE">
        <AuthProvider>
          <WorkerProvider>
            <App />
          </WorkerProvider>
        </AuthProvider>
      </IntlProvider>
    </BrowserRouter>
  </React.StrictMode>,
)
