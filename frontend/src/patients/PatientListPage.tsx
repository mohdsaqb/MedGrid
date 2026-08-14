import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'
import { Layout } from '../components/Layout'
import { useAuth } from '../auth/AuthContext'
import type { PatientPage } from './types'

const PAGE_SIZE = 10

export function PatientListPage() {
  const { user } = useAuth()
  const [data, setData] = useState<PatientPage | null>(null)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [error, setError] = useState<string | null>(null)

  const canCreate = user?.role === 'ADMIN' || user?.role === 'DOCTOR'

  useEffect(() => {
    const params = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE) })
    if (search) params.set('search', search)

    api
      .get<PatientPage>(`/patients?${params}`)
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load patients'))
  }, [page, search])

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1

  return (
    <Layout>
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold tracking-tight text-slate-900">Patients</h1>
        {canCreate && (
          <Link
            to="/patients/new"
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-brand-700"
          >
            + New Patient
          </Link>
        )}
      </div>

      <input
        placeholder="Search by name, patient number, or phone..."
        value={search}
        onChange={(e) => {
          setSearch(e.target.value)
          setPage(1)
        }}
        className="mt-4 w-full max-w-md rounded-lg border border-slate-300 px-3 py-2 text-sm transition-colors focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
      />

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

      <div className="mt-4 overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-slate-500">
            <tr>
              <th className="px-4 py-2">Patient #</th>
              <th className="px-4 py-2">Name</th>
              <th className="px-4 py-2">Phone</th>
              <th className="px-4 py-2">Gender</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((patient) => (
              <tr key={patient.id} className="border-b border-slate-100 transition-colors last:border-0 hover:bg-slate-50">
                <td className="px-4 py-2">
                  <Link to={`/patients/${patient.id}`} className="font-medium text-brand-600 transition-colors hover:text-brand-700 hover:underline">
                    {patient.patient_number}
                  </Link>
                </td>
                <td className="px-4 py-2">
                  {patient.first_name} {patient.last_name}
                </td>
                <td className="px-4 py-2">{patient.phone}</td>
                <td className="px-4 py-2">{patient.gender ?? '-'}</td>
              </tr>
            ))}
            {data?.items.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-slate-400">
                  No patients found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {data && data.total > 0 && (
        <div className="mt-3 flex items-center justify-between text-sm text-slate-500">
          <span>
            Page {data.page} of {totalPages} ({data.total} total)
          </span>
          <div className="flex gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
              className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent"
            >
              Previous
            </button>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </Layout>
  )
}
