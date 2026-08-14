import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'
import { Layout } from '../components/Layout'
import { useAuth } from '../auth/AuthContext'
import { AppointmentTable } from './AppointmentTable'
import type { AppointmentPage, AppointmentStatus } from './types'

const STATUS_OPTIONS: AppointmentStatus[] = ['SCHEDULED', 'COMPLETED', 'CANCELLED', 'NO_SHOW']

export function AppointmentListPage() {
  const { user } = useAuth()
  const [data, setData] = useState<AppointmentPage | null>(null)
  const [status, setStatus] = useState<AppointmentStatus | ''>('')
  const [date, setDate] = useState('')
  const [error, setError] = useState<string | null>(null)

  const canBook = user?.role === 'ADMIN' || user?.role === 'DOCTOR'

  const load = useCallback(() => {
    const params = new URLSearchParams({ page: '1', page_size: '50' })
    if (status) params.set('status', status)
    if (date) params.set('appointment_date', date)

    api
      .get<AppointmentPage>(`/appointments?${params}`)
      .then(setData)
      .catch((err) =>
        setError(err instanceof Error ? err.message : 'Failed to load appointments'),
      )
  }, [status, date])

  useEffect(() => {
    load()
  }, [load])

  return (
    <Layout>
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold tracking-tight text-slate-900">Appointments</h1>
        {canBook && (
          <Link
            to="/appointments/new"
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-brand-700"
          >
            + Book Appointment
          </Link>
        )}
      </div>

      <div className="mt-4 flex gap-3">
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value as AppointmentStatus | '')}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm transition-colors focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
        >
          <option value="">All statuses</option>
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm transition-colors focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
        />
      </div>

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

      <div className="mt-4">
        {data && <AppointmentTable appointments={data.items} onStatusChanged={load} />}
      </div>
    </Layout>
  )
}
