import React from 'react'
import ReactDOM from 'react-dom/client'
import { IntlProvider } from 'react-intl'
import App from './App.tsx'
import messages from './locales/es-PE.json'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <IntlProvider locale="es-PE" messages={messages} defaultLocale="es-PE">
      <App />
    </IntlProvider>
  </React.StrictMode>,
)
