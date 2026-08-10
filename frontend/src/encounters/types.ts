import type { DoctorSummary, PatientSummary } from '../appointments/types'

export type EncounterStatus = 'OPEN' | 'CLOSED'

export type RecordType = 'DIAGNOSIS' | 'PRESCRIPTION' | 'PROCEDURE' | 'VITALS' | 'GENERAL_NOTE'

export type ClinicalRecord = {
  id: string
  record_type: RecordType
  description: string
  created_by_user_id: string
  created_at: string
}

export type Encounter = {
  id: string
  patient: PatientSummary
  doctor: DoctorSummary
  appointment_id: string | null
  encounter_date: string
  diagnosis: string
  symptoms: string
  notes: string | null
  status: EncounterStatus
  created_at: string
  updated_at: string
  clinical_records: ClinicalRecord[]
}

export type EncounterListItem = Omit<Encounter, 'symptoms' | 'notes' | 'updated_at' | 'clinical_records'>

export type EncounterPage = {
  items: EncounterListItem[]
  total: number
  page: number
  page_size: number
}

export type EncounterInput = {
  patient_id: string
  doctor_id: string
  appointment_id: string | null
  encounter_date: string
  diagnosis: string
  symptoms: string
  notes: string | null
}
