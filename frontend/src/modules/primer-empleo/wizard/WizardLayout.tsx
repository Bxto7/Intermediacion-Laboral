import { Routes, Route, Navigate } from 'react-router-dom'
import { WizardProgressBar } from './WizardProgressBar'
import { CVLivePreview } from './CVLivePreview'
import { Step1PersonalData } from './steps/Step1PersonalData'
import { Step2Education } from './steps/Step2Education'
import { Step3Skills } from './steps/Step3Skills'
import { Step4Activities } from './steps/Step4Activities'
import { Step5Interests } from './steps/Step5Interests'
import { Step6Preview } from './steps/Step6Preview'

export const WizardLayout: React.FC = () => (
  <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
    <WizardProgressBar />
    <div className="max-w-5xl mx-auto p-4 grid grid-cols-1 lg:grid-cols-5 gap-6 mt-4">
      <div className="lg:col-span-3 bg-white rounded-2xl shadow-md border border-gray-100 p-6">
        <Routes>
          <Route index element={<Navigate to="step/1" replace />} />
          <Route path="step/1" element={<Step1PersonalData />} />
          <Route path="step/2" element={<Step2Education />} />
          <Route path="step/3" element={<Step3Skills />} />
          <Route path="step/4" element={<Step4Activities />} />
          <Route path="step/5" element={<Step5Interests />} />
          <Route path="step/6" element={<Step6Preview />} />
        </Routes>
      </div>
      <div className="hidden lg:block lg:col-span-2 bg-white rounded-2xl shadow-md border border-gray-100 p-6">
        <CVLivePreview />
      </div>
    </div>
  </div>
)
