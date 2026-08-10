export type Doctor = {
  id: string
  name: string
  specialization: string
  department: string
  license_number: string
  email: string
  phone: string
  created_at: string
  updated_at: string
}

export type DoctorPage = {
  items: Doctor[]
  total: number
  page: number
  page_size: number
}
