import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../lib/api'
import { Layout } from '../components/Layout'
import { useAuth } from '../auth/AuthContext'
import type { Patient } from './types'

export function PatientDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { user } = useAuth()
  const navigate = useNavigate()
  const [patient, setPatient] = useState<Patient | null>(null)
  const [error, setError] = useState<string | null>(null)

  const canEdit = user?.role === 'ADMIN' || user?.role === 'DOCTOR'
  const canDelete = user?.role === 'ADMIN'
  const canViewClinicalHistory = user?.role === 'ADMIN' || user?.role === 'DOCTOR'

  useEffect(() => {
    if (!id) return
    api
      .get<Patient>(`/patients/${id}`)
      .then(setPatient)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load patient'))
  }, [id])

  async function handleDelete() {
    if (!id || !confirm('Delete this patient record? This cannot be undone.')) return
    await api.delete(`/patients/${id}`)
    navigate('/patients')
  }

  if (error) {
    return (
      <Layout>
        <p className="text-sm text-red-600">{error}</p>
      </Layout>
    )
  }

  if (!patient) {
    return (
      <Layout>
        <p className="text-sm text-slate-500">Loading...</p>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-slate-900">
          {patient.first_name} {patient.last_name}
        </h1>
        <div className="flex gap-2">
          {canViewClinicalHistory && (
            <Link
              to={`/patients/${patient.id}/clinical-history`}
              className="rounded border border-slate-300 px-3 py-2 text-sm"
            >
              Clinical History
            </Link>
          )}
          {canEdit && (
            <Link
              to={`/patients/${patient.id}/edit`}
              className="rounded border border-slate-300 px-3 py-2 text-sm"
            >
              Edit
            </Link>
          )}
          {canDelete && (
            <button
              onClick={handleDelete}
              className="rounded border border-red-300 px-3 py-2 text-sm text-red-600"
            >
              Delete
            </button>
          )}
        </div>
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-x-6 gap-y-3 rounded border border-slate-200 bg-white p-4 text-sm max-w-lg">
        <dt className="text-slate-500">Patient #</dt>
        <dd className="text-slate-900">{patient.patient_number}</dd>

        <dt className="text-slate-500">Date of birth</dt>
        <dd className="text-slate-900">{patient.date_of_birth}</dd>

        <dt className="text-slate-500">Gender</dt>
        <dd className="text-slate-900">{patient.gender ?? '-'}</dd>

        <dt className="text-slate-500">Phone</dt>
        <dd className="text-slate-900">{patient.phone}</dd>

        <dt className="text-slate-500">Email</dt>
        <dd className="text-slate-900">{patient.email ?? '-'}</dd>

        <dt className="text-slate-500">Blood group</dt>
        <dd className="text-slate-900">{patient.blood_group ?? '-'}</dd>

        <dt className="text-slate-500">Address</dt>
        <dd className="text-slate-900">{patient.address ?? '-'}</dd>
      </dl>

      <Link to="/patients" className="mt-4 inline-block text-sm text-slate-500 underline">
        ← Back to patients
      </Link>
    </Layout>
  )
}
