import type { PatientSummary } from '../appointments/types'

export type InvoiceStatus = 'UNPAID' | 'PARTIALLY_PAID' | 'PAID'
export type PaymentMethod = 'CASH' | 'CARD' | 'BANK_TRANSFER'
export type PaymentStatus = 'PENDING' | 'SUCCESS' | 'FAILED'

export type Payment = {
  id: string
  amount: string
  payment_method: PaymentMethod
  payment_status: PaymentStatus
  recorded_by_user_id: string
  paid_at: string | null
  created_at: string
}

export type Invoice = {
  id: string
  patient: PatientSummary
  appointment_id: string | null
  amount: string
  status: InvoiceStatus
  amount_paid: string
  balance_due: string
  payments: Payment[]
  created_at: string
  updated_at: string
}

export type InvoicePage = {
  items: Invoice[]
  total: number
  page: number
  page_size: number
}
