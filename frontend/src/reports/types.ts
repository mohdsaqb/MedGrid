export type GenderCount = { gender: string; count: number }
export type DepartmentPatientCount = { department: string; patient_count: number }

export type PatientsReport = {
  total_patients: number
  patients_by_gender: GenderCount[]
  patients_by_department: DepartmentPatientCount[]
}

export type StatusCount = { status: string; count: number }
export type DailyCount = { day: string; count: number }

export type AppointmentsReport = {
  total_appointments: number
  appointments_by_status: StatusCount[]
  appointments_by_day: DailyCount[]
}

export type PendingLabOrder = {
  id: string
  patient_name: string
  doctor_name: string
  test_name: string
  ordered_at: string
}

export type LabsReport = {
  total_orders: number
  orders_by_status: StatusCount[]
  completed_tests: number
  pending_orders: PendingLabOrder[]
}

export type DailyRevenue = { day: string; revenue: string }

export type RevenueReport = {
  total_revenue: string
  total_invoiced: string
  outstanding_balance: string
  revenue_by_day: DailyRevenue[]
}

export type DoctorPerformance = {
  id: string
  name: string
  specialization: string
  department: string
  appointment_count: number
  revenue: string
}

export type DoctorPerformanceReport = {
  doctors: DoctorPerformance[]
}
