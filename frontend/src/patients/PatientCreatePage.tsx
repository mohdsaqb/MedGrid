import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { Layout } from '../components/Layout'
import { PatientForm } from './PatientForm'
import type { Patient, PatientInput } from './types'

export function PatientCreatePage() {
  const navigate = useNavigate()

  async function handleSubmit(data: PatientInput) {
    const created = await api.post<Patient>('/patients', data)
    navigate(`/patients/${created.id}`)
  }

  return (
    <Layout>
      <h1 className="text-lg font-semibold text-slate-900">New Patient</h1>
      <div className="mt-4">
        <PatientForm submitLabel="Create Patient" onSubmit={handleSubmit} />
      </div>
    </Layout>
  )
}
