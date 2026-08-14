import { useState } from 'react'
import { api, ApiError } from '../lib/api'
import { useAuth } from '../auth/AuthContext'
import type { Appointment, AppointmentStatus } from './types'

const STATUS_OPTIONS: AppointmentStatus[] = ['SCHEDULED', 'COMPLETED', 'CANCELLED', 'NO_SHOW']

const STATUS_STYLES: Record<AppointmentStatus, string> = {
  SCHEDULED: 'bg-blue-50 text-blue-700',
  COMPLETED: 'bg-emerald-50 text-emerald-700',
  CANCELLED: 'bg-slate-100 text-slate-500',
  NO_SHOW: 'bg-amber-50 text-amber-700',
}

const TERMINAL: AppointmentStatus[] = ['COMPLETED', 'CANCELLED']

type Props = {
  appointments: Appointment[]
  onStatusChanged: () => void
}

export function AppointmentTable({ appointments, onStatusChanged }: Props) {
  const { user } = useAuth()
  const [error, setError] = useState<string | null>(null)
  const canUpdateStatus = user?.role === 'ADMIN' || user?.role === 'DOCTOR'

  async function handleStatusChange(id: string, status: AppointmentStatus) {
    setError(null)
    try {
      await api.patch(`/appointments/${id}/status`, { status })
      onStatusChanged()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to update status')
    }
  }

  return (
    <div>
      {error && <p className="mb-2 text-sm text-red-600">{error}</p>}
      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-slate-500">
            <tr>
              <th className="px-4 py-2">Date</th>
              <th className="px-4 py-2">Time</th>
              <th className="px-4 py-2">Patient</th>
              <th className="px-4 py-2">Doctor</th>
              <th className="px-4 py-2">Reason</th>
              <th className="px-4 py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {appointments.map((appt) => (
              <tr key={appt.id} className="border-b border-slate-100 transition-colors last:border-0 hover:bg-slate-50">
                <td className="px-4 py-2">{appt.appointment_date}</td>
                <td className="px-4 py-2">{appt.appointment_time}</td>
                <td className="px-4 py-2">
                  {appt.patient.first_name} {appt.patient.last_name}{' '}
                  <span className="text-slate-400">({appt.patient.patient_number})</span>
                </td>
                <td className="px-4 py-2">{appt.doctor.name}</td>
                <td className="px-4 py-2">{appt.reason}</td>
                <td className="px-4 py-2">
                  {canUpdateStatus && !TERMINAL.includes(appt.status) ? (
                    <select
                      value={appt.status}
                      onChange={(e) =>
                        handleStatusChange(appt.id, e.target.value as AppointmentStatus)
                      }
                      className={`cursor-pointer rounded-full border-0 px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ring-black/5 transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500/30 ${STATUS_STYLES[appt.status]}`}
                    >
                      {STATUS_OPTIONS.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ring-black/5 ${STATUS_STYLES[appt.status]}`}
                    >
                      {appt.status}
                    </span>
                  )}
                </td>
              </tr>
            ))}
            {appointments.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-slate-400">
                  No appointments found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
