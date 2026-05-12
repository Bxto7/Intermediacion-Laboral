import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface WizardAnswers {
  full_name?: string
  phone?: string
  district?: string
  education?: Array<{ institution: string; level: string; year: string }>
  free_text_skills?: string
  activities?: Array<{ description: string }>
  job_interests?: string
  linkedin?: string
}

interface WizardState {
  currentStep: number
  answers: WizardAnswers
  extractedSkills: string[]
  profileCompleteness: number
  setCurrentStep: (step: number) => void
  setAnswer: (key: keyof WizardAnswers, value: unknown) => void
  setExtractedSkills: (skills: string[]) => void
  removeSkill: (skill: string) => void
  setProfileCompleteness: (pct: number) => void
  reset: () => void
}

export const useWizardStore = create<WizardState>()(
  persist(
    (set) => ({
      currentStep: 1,
      answers: {},
      extractedSkills: [],
      profileCompleteness: 0,
      setCurrentStep: (step) => set({ currentStep: step }),
      setAnswer: (key, value) => set((s) => ({ answers: { ...s.answers, [key]: value } })),
      setExtractedSkills: (skills) => set({ extractedSkills: skills }),
      removeSkill: (skill) => set((s) => ({ extractedSkills: s.extractedSkills.filter((sk) => sk !== skill) })),
      setProfileCompleteness: (pct) => set({ profileCompleteness: pct }),
      reset: () => set({ currentStep: 1, answers: {}, extractedSkills: [], profileCompleteness: 0 }),
    }),
    { name: 'wizard-progress' }
  )
)
