import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'
import { Layout } from '../components/Layout'
import { useAuth } from '../auth/AuthContext'
import type { EncounterPage, EncounterStatus } from './types'

const STATUS_STYLES: Record<EncounterStatus, string> = {
  OPEN: 'bg-blue-50 text-blue-700',
  CLOSED: 'bg-slate-100 text-slate-500',
}

export function EncounterListPage() {
  const { user } = useAuth()
  const [data, setData] = useState<EncounterPage | null>(null)
  const [status, setStatus] = useState<EncounterStatus | ''>('')
  const [error, setError] = useState<string | null>(null)

  const canDocument = user?.role === 'DOCTOR'

  useEffect(() => {
    const params = new URLSearchParams({ page: '1', page_size: '50' })
    if (status) params.set('status', status)

    api
      .get<EncounterPage>(`/encounters?${params}`)
      .then(setData)
      .catch((err) =>
        setError(err instanceof Error ? err.message : 'Failed to load encounters'),
      )
  }, [status])

  return (
    <Layout>
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-slate-900">Encounters</h1>
        {canDocument && (
          <Link
            to="/encounters/new"
            className="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white"
          >
            + New Encounter
          </Link>
        )}
      </div>

      <select
        value={status}
        onChange={(e) => setStatus(e.target.value as EncounterStatus | '')}
        className="mt-4 rounded border border-slate-300 px-3 py-2 text-sm"
      >
        <option value="">All statuses</option>
        <option value="OPEN">OPEN</option>
        <option value="CLOSED">CLOSED</option>
      </select>

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

      <div className="mt-4 overflow-x-auto rounded border border-slate-200 bg-white">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-slate-500">
            <tr>
              <th className="px-4 py-2">Date</th>
              <th className="px-4 py-2">Patient</th>
              <th className="px-4 py-2">Doctor</th>
              <th className="px-4 py-2">Diagnosis</th>
              <th className="px-4 py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((enc) => (
              <tr key={enc.id} className="border-b border-slate-100 last:border-0">
                <td className="px-4 py-2">{new Date(enc.encounter_date).toLocaleString()}</td>
                <td className="px-4 py-2">
                  <Link to={`/encounters/${enc.id}`} className="underline">
                    {enc.patient.first_name} {enc.patient.last_name}
                  </Link>
                </td>
                <td className="px-4 py-2">{enc.doctor.name}</td>
                <td className="px-4 py-2">{enc.diagnosis}</td>
                <td className="px-4 py-2">
                  <span className={`rounded px-2 py-1 text-xs font-medium ${STATUS_STYLES[enc.status]}`}>
                    {enc.status}
                  </span>
                </td>
              </tr>
            ))}
            {data?.items.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-slate-400">
                  No encounters found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </Layout>
  )
}
