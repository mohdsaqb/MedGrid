import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { useParams } from 'react-router-dom'
import { api, ApiError } from '../lib/api'
import { Layout } from '../components/Layout'
import type { Invoice, PaymentMethod, PaymentStatus } from './types'

const PAYMENT_METHODS: PaymentMethod[] = ['CASH', 'CARD', 'BANK_TRANSFER']

const PAYMENT_STATUS_STYLES: Record<PaymentStatus, string> = {
  PENDING: 'bg-amber-50 text-amber-700',
  SUCCESS: 'bg-emerald-50 text-emerald-700',
  FAILED: 'bg-red-50 text-red-700',
}

export function InvoiceDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [invoice, setInvoice] = useState<Invoice | null>(null)
  const [error, setError] = useState<string | null>(null)

  const [amount, setAmount] = useState('')
  const [method, setMethod] = useState<PaymentMethod>('CASH')
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [confirmingId, setConfirmingId] = useState<string | null>(null)

  const load = useCallback(() => {
    if (!id) return
    api
      .get<Invoice>(`/invoices/${id}`)
      .then(setInvoice)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load invoice'))
  }, [id])

  useEffect(() => {
    load()
  }, [load])

  async function handleRecordPayment(event: FormEvent) {
    event.preventDefault()
    if (!id) return
    setFormError(null)
    setSubmitting(true)
    try {
      await api.post(`/invoices/${id}/payments`, {
        amount: Number(amount),
        payment_method: method,
      })
      setAmount('')
      load()
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : 'Failed to record payment')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleConfirm(paymentId: string) {
    setConfirmingId(paymentId)
    try {
      await api.patch(`/payments/${paymentId}/status`, { simulate_failure: false })
    } catch {
      // Error surfaces via the payment's own status turning FAILED on reload.
    } finally {
      load()
      setConfirmingId(null)
    }
  }

  if (error) {
    return (
      <Layout>
        <p className="text-sm text-red-600">{error}</p>
      </Layout>
    )
  }
  if (!invoice) {
    return (
      <Layout>
        <p className="text-sm text-slate-500">Loading...</p>
      </Layout>
    )
  }

  const isSettled = invoice.status === 'PAID'

  return (
    <Layout>
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold tracking-tight text-slate-900">
          Invoice - {invoice.patient.first_name} {invoice.patient.last_name}
        </h1>
        <span
          className={`rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ring-black/5 ${
            invoice.status === 'PAID'
              ? 'bg-emerald-50 text-emerald-700'
              : invoice.status === 'PARTIALLY_PAID'
                ? 'bg-blue-50 text-blue-700'
                : 'bg-amber-50 text-amber-700'
          }`}
        >
          {invoice.status}
        </span>
      </div>

      <dl className="mt-4 grid grid-cols-3 gap-x-6 gap-y-3 rounded-xl border border-slate-200 bg-white shadow-sm p-4 text-sm max-w-lg">
        <dt className="text-slate-500">Total</dt>
        <dd className="col-span-2 text-slate-900">${invoice.amount}</dd>

        <dt className="text-slate-500">Paid</dt>
        <dd className="col-span-2 text-slate-900">${invoice.amount_paid}</dd>

        <dt className="text-slate-500">Balance Due</dt>
        <dd className="col-span-2 font-semibold text-slate-900">${invoice.balance_due}</dd>
      </dl>

      <div className="mt-6 max-w-2xl">
        <h2 className="text-sm font-semibold text-slate-700">Payment History</h2>
        <div className="mt-2 overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-slate-500">
              <tr>
                <th className="px-4 py-2">Recorded</th>
                <th className="px-4 py-2">Amount</th>
                <th className="px-4 py-2">Method</th>
                <th className="px-4 py-2">Status</th>
                <th className="px-4 py-2">Action</th>
              </tr>
            </thead>
            <tbody>
              {invoice.payments.map((p) => (
                <tr key={p.id} className="border-b border-slate-100 transition-colors last:border-0 hover:bg-slate-50">
                  <td className="px-4 py-2">{new Date(p.created_at).toLocaleString()}</td>
                  <td className="px-4 py-2">${p.amount}</td>
                  <td className="px-4 py-2">{p.payment_method}</td>
                  <td className="px-4 py-2">
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ring-black/5 ${PAYMENT_STATUS_STYLES[p.payment_status]}`}
                    >
                      {p.payment_status}
                    </span>
                  </td>
                  <td className="px-4 py-2">
                    {p.payment_status === 'PENDING' && (
                      <button
                        onClick={() => handleConfirm(p.id)}
                        disabled={confirmingId === p.id}
                        className="rounded-lg border border-slate-300 px-3 py-1 text-xs font-medium transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-transparent"
                      >
                        {confirmingId === p.id ? 'Confirming...' : 'Confirm'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {invoice.payments.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-6 text-center text-slate-400">
                    No payments recorded yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {!isSettled && (
        <div className="mt-6 max-w-md rounded-xl border border-slate-200 bg-white shadow-sm p-4">
          <h2 className="text-sm font-semibold text-slate-700">Record Payment</h2>
          <form onSubmit={handleRecordPayment} className="mt-3 space-y-3">
            <input
              required
              type="number"
              step="0.01"
              min="0.01"
              placeholder={`Amount (balance due: $${invoice.balance_due})`}
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm transition-colors focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
            />
            <select
              value={method}
              onChange={(e) => setMethod(e.target.value as PaymentMethod)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm transition-colors focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
            >
              {PAYMENT_METHODS.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
            {formError && <p className="text-sm text-red-600">{formError}</p>}
            <button
              type="submit"
              disabled={submitting}
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {submitting ? 'Recording...' : 'Record Payment'}
            </button>
          </form>
        </div>
      )}
    </Layout>
  )
}
