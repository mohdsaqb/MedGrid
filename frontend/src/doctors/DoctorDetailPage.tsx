import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../lib/api'
import { Layout } from '../components/Layout'
import { AppointmentTable } from '../appointments/AppointmentTable'
import type { AppointmentPage } from '../appointments/types'
import type { Doctor } from './types'

export function DoctorDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [doctor, setDoctor] = useState<Doctor | null>(null)
  const [appointments, setAppointments] = useState<AppointmentPage | null>(null)
  const [error, setError] = useState<string | null>(null)

  const loadAppointments = useCallback(() => {
    if (!id) return
    api
      .get<AppointmentPage>(`/appointments?doctor_id=${id}&page_size=50`)
      .then(setAppointments)
      .catch(() => {
        // Non-fatal: BILLING_STAFF etc. can view the doctor but appointment
        // read access differs by role - just hide the dashboard section.
      })
  }, [id])

  useEffect(() => {
    if (!id) return
    api
      .get<Doctor>(`/doctors/${id}`)
      .then(setDoctor)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load doctor'))
    loadAppointments()
  }, [id, loadAppointments])

  if (error) {
    return (
      <Layout>
        <p className="text-sm text-red-600">{error}</p>
      </Layout>
    )
  }

  if (!doctor) {
    return (
      <Layout>
        <p className="text-sm text-slate-500">Loading...</p>
      </Layout>
    )
  }

  return (
    <Layout>
      <h1 className="text-xl font-semibold tracking-tight text-slate-900">{doctor.name}</h1>

      <dl className="mt-4 grid grid-cols-2 gap-x-6 gap-y-3 rounded-xl border border-slate-200 bg-white shadow-sm p-4 text-sm max-w-lg">
        <dt className="text-slate-500">Specialization</dt>
        <dd className="text-slate-900">{doctor.specialization}</dd>

        <dt className="text-slate-500">Department</dt>
        <dd className="text-slate-900">{doctor.department}</dd>

        <dt className="text-slate-500">License #</dt>
        <dd className="text-slate-900">{doctor.license_number}</dd>

        <dt className="text-slate-500">Email</dt>
        <dd className="text-slate-900">{doctor.email}</dd>

        <dt className="text-slate-500">Phone</dt>
        <dd className="text-slate-900">{doctor.phone}</dd>
      </dl>

      {appointments && (
        <div className="mt-6">
          <h2 className="text-sm font-semibold text-slate-700">
            Appointments ({appointments.total})
          </h2>
          <div className="mt-2">
            <AppointmentTable
              appointments={appointments.items}
              onStatusChanged={loadAppointments}
            />
          </div>
        </div>
      )}

      <Link to="/doctors" className="mt-4 inline-block text-sm text-slate-500 transition-colors hover:text-brand-600 hover:underline">
        ← Back to doctors
      </Link>
    </Layout>
  )
}
