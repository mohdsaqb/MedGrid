export type Gender = 'MALE' | 'FEMALE' | 'OTHER' | 'UNKNOWN'

export type BloodGroup = 'A+' | 'A-' | 'B+' | 'B-' | 'AB+' | 'AB-' | 'O+' | 'O-'

export type Patient = {
  id: string
  patient_number: string
  first_name: string
  last_name: string
  date_of_birth: string
  gender: Gender | null
  email: string | null
  phone: string
  address: string | null
  blood_group: BloodGroup | null
  created_at: string
  updated_at: string
}

// Matches PatientCreate / PatientUpdate on the backend - patient_number,
// id, created_at, updated_at are all server-controlled, never sent by us.
export type PatientInput = {
  first_name: string
  last_name: string
  date_of_birth: string
  gender: Gender | null
  email: string | null
  phone: string
  address: string | null
  blood_group: BloodGroup | null
}

export type PatientPage = {
  items: Patient[]
  total: number
  page: number
  page_size: number
}
