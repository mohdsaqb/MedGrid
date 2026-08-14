import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../lib/api'
import { Layout } from '../components/Layout'
import { PatientForm } from './PatientForm'
import type { Patient, PatientInput } from './types'

export function PatientEditPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [patient, setPatient] = useState<Patient | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    api
      .get<Patient>(`/patients/${id}`)
      .then(setPatient)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load patient'))
  }, [id])

  async function handleSubmit(data: PatientInput) {
    if (!id) return
    await api.put<Patient>(`/patients/${id}`, data)
    navigate(`/patients/${id}`)
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
      <h1 className="text-xl font-semibold tracking-tight text-slate-900">
        Edit {patient.first_name} {patient.last_name}
      </h1>
      <div className="mt-4">
        <PatientForm
          submitLabel="Save Changes"
          initial={{
            first_name: patient.first_name,
            last_name: patient.last_name,
            date_of_birth: patient.date_of_birth,
            gender: patient.gender,
            email: patient.email,
            phone: patient.phone,
            address: patient.address,
            blood_group: patient.blood_group,
          }}
          onSubmit={handleSubmit}
        />
      </div>
    </Layout>
  )
}
