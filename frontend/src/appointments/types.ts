export type AppointmentStatus = 'SCHEDULED' | 'COMPLETED' | 'CANCELLED' | 'NO_SHOW'

export type PatientSummary = {
  id: string
  first_name: string
  last_name: string
  patient_number: string
}

export type DoctorSummary = {
  id: string
  name: string
  specialization: string
}

export type Appointment = {
  id: string
  patient: PatientSummary
  doctor: DoctorSummary
  appointment_date: string
  appointment_time: string
  reason: string
  status: AppointmentStatus
  created_at: string
  updated_at: string
}

export type AppointmentPage = {
  items: Appointment[]
  total: number
  page: number
  page_size: number
}

export type AppointmentInput = {
  patient_id: string
  doctor_id: string
  appointment_date: string
  appointment_time: string
  reason: string
}
