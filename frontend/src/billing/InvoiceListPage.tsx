import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'
import { Layout } from '../components/Layout'
import type { InvoicePage, InvoiceStatus } from './types'

const STATUS_STYLES: Record<InvoiceStatus, string> = {
  UNPAID: 'bg-amber-50 text-amber-700',
  PARTIALLY_PAID: 'bg-blue-50 text-blue-700',
  PAID: 'bg-emerald-50 text-emerald-700',
}

export function InvoiceListPage() {
  const [data, setData] = useState<InvoicePage | null>(null)
  const [status, setStatus] = useState<InvoiceStatus | ''>('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const params = new URLSearchParams({ page: '1', page_size: '50' })
    if (status) params.set('status', status)

    api
      .get<InvoicePage>(`/invoices?${params}`)
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load invoices'))
  }, [status])

  return (
    <Layout>
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-slate-900">Billing Dashboard</h1>
        <Link
          to="/invoices/new"
          className="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white"
        >
          + New Invoice
        </Link>
      </div>

      <div className="mt-4 flex gap-2">
        {(['', 'UNPAID', 'PARTIALLY_PAID', 'PAID'] as const).map((s) => (
          <button
            key={s || 'ALL'}
            onClick={() => setStatus(s)}
            className={`rounded px-3 py-1 text-xs font-medium ${
              status === s ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600'
            }`}
          >
            {s || 'ALL'}
          </button>
        ))}
      </div>

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

      <div className="mt-4 overflow-x-auto rounded border border-slate-200 bg-white">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-slate-500">
            <tr>
              <th className="px-4 py-2">Created</th>
              <th className="px-4 py-2">Patient</th>
              <th className="px-4 py-2">Amount</th>
              <th className="px-4 py-2">Paid</th>
              <th className="px-4 py-2">Balance</th>
              <th className="px-4 py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((inv) => (
              <tr key={inv.id} className="border-b border-slate-100 last:border-0">
                <td className="px-4 py-2">{new Date(inv.created_at).toLocaleDateString()}</td>
                <td className="px-4 py-2">
                  <Link to={`/invoices/${inv.id}`} className="underline">
                    {inv.patient.first_name} {inv.patient.last_name}
                  </Link>
                </td>
                <td className="px-4 py-2">${inv.amount}</td>
                <td className="px-4 py-2">${inv.amount_paid}</td>
                <td className="px-4 py-2">${inv.balance_due}</td>
                <td className="px-4 py-2">
                  <span
                    className={`rounded px-2 py-1 text-xs font-medium ${STATUS_STYLES[inv.status]}`}
                  >
                    {inv.status}
                  </span>
                </td>
              </tr>
            ))}
            {data?.items.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-slate-400">
                  No invoices found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </Layout>
  )
}
