import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, ApiError } from '../lib/api'
import { Layout } from '../components/Layout'
import { useAuth } from '../auth/AuthContext'
import type { LabOrderPage, LabStatus } from './types'

const STATUS_STYLES: Record<LabStatus, string> = {
  PENDING: 'bg-amber-50 text-amber-700',
  PROCESSING: 'bg-blue-50 text-blue-700',
  COMPLETED: 'bg-emerald-50 text-emerald-700',
  FAILED: 'bg-red-50 text-red-700',
}

export function LabDashboardPage() {
  const { user } = useAuth()
  const [data, setData] = useState<LabOrderPage | null>(null)
  const [status, setStatus] = useState<LabStatus | ''>('')
  const [error, setError] = useState<string | null>(null)
  const [processingId, setProcessingId] = useState<string | null>(null)
  const [rowErrors, setRowErrors] = useState<Record<string, string>>({})

  const canOrder = user?.role === 'DOCTOR'
  const canProcess = user?.role === 'LAB_TECHNICIAN'

  const load = useCallback(() => {
    const params = new URLSearchParams({ page: '1', page_size: '50' })
    if (status) params.set('status', status)

    api
      .get<LabOrderPage>(`/lab-orders?${params}`)
      .then(setData)
      .catch((err) =>
        setError(err instanceof Error ? err.message : 'Failed to load lab orders'),
      )
  }, [status])

  useEffect(() => {
    load()
  }, [load])

  async function handleProcess(orderId: string) {
    setProcessingId(orderId)
    setRowErrors((prev) => ({ ...prev, [orderId]: '' }))
    try {
      await api.post(`/lab-orders/${orderId}/process`, { simulate_failure: false })
      load()
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Processing failed'
      setRowErrors((prev) => ({ ...prev, [orderId]: message }))
      load() // refresh so the row picks up the new FAILED status
    } finally {
      setProcessingId(null)
    }
  }

  return (
    <Layout>
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-slate-900">Lab Dashboard</h1>
        {canOrder && (
          <Link
            to="/lab-orders/new"
            className="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white"
          >
            + Order Test
          </Link>
        )}
      </div>

      <div className="mt-4 flex gap-2">
        {(['', 'PENDING', 'PROCESSING', 'COMPLETED', 'FAILED'] as const).map((s) => (
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
              <th className="px-4 py-2">Ordered</th>
              <th className="px-4 py-2">Patient</th>
              <th className="px-4 py-2">Doctor</th>
              <th className="px-4 py-2">Test</th>
              <th className="px-4 py-2">Result</th>
              <th className="px-4 py-2">Status</th>
              {canProcess && <th className="px-4 py-2">Action</th>}
            </tr>
          </thead>
          <tbody>
            {data?.items.map((order) => (
              <tr key={order.id} className="border-b border-slate-100 last:border-0">
                <td className="px-4 py-2">{new Date(order.ordered_at).toLocaleString()}</td>
                <td className="px-4 py-2">
                  {order.patient.first_name} {order.patient.last_name}
                </td>
                <td className="px-4 py-2">{order.doctor.name}</td>
                <td className="px-4 py-2">{order.test.name}</td>
                <td className="px-4 py-2">
                  {order.result
                    ? `${order.result.result}${order.result.unit ? ' ' + order.result.unit : ''}`
                    : '-'}
                </td>
                <td className="px-4 py-2">
                  <span
                    className={`rounded px-2 py-1 text-xs font-medium ${STATUS_STYLES[order.status]}`}
                  >
                    {order.status}
                  </span>
                  {rowErrors[order.id] && (
                    <p className="mt-1 text-xs text-red-600">{rowErrors[order.id]}</p>
                  )}
                </td>
                {canProcess && (
                  <td className="px-4 py-2">
                    {(order.status === 'PENDING' || order.status === 'FAILED') && (
                      <button
                        onClick={() => handleProcess(order.id)}
                        disabled={processingId === order.id}
                        className="rounded border border-slate-300 px-3 py-1 text-xs disabled:opacity-50"
                      >
                        {processingId === order.id
                          ? 'Processing...'
                          : order.status === 'FAILED'
                            ? 'Retry'
                            : 'Process'}
                      </button>
                    )}
                  </td>
                )}
              </tr>
            ))}
            {data?.items.length === 0 && (
              <tr>
                <td colSpan={canProcess ? 7 : 6} className="px-4 py-6 text-center text-slate-400">
                  No lab orders found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </Layout>
  )
}
