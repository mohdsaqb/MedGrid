import type { DoctorSummary, PatientSummary } from '../appointments/types'

export type LabStatus = 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED'

export type LabTest = {
  id: string
  name: string
  description: string | null
  price: string
  normal_range: string | null
  created_at: string
  updated_at: string
}

export type LabTestPage = {
  items: LabTest[]
  total: number
  page: number
  page_size: number
}

export type LabTestSummary = {
  id: string
  name: string
  price: string
}

export type LabResult = {
  id: string
  result: string
  unit: string | null
  reference_range: string | null
  status: LabStatus
  completed_at: string
}

export type LabOrder = {
  id: string
  patient: PatientSummary
  doctor: DoctorSummary
  test: LabTestSummary
  status: LabStatus
  ordered_at: string
  result: LabResult | null
}

export type LabOrderPage = {
  items: LabOrder[]
  total: number
  page: number
  page_size: number
}
