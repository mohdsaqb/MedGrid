import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'
import { Layout } from '../components/Layout'
import type { DoctorPage } from './types'

export function DoctorListPage() {
  const [data, setData] = useState<DoctorPage | null>(null)
  const [search, setSearch] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const params = new URLSearchParams({ page: '1', page_size: '50' })
    if (search) params.set('search', search)

    api
      .get<DoctorPage>(`/doctors?${params}`)
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load doctors'))
  }, [search])

  return (
    <Layout>
      <h1 className="text-lg font-semibold text-slate-900">Doctors</h1>

      <input
        placeholder="Search by name or license number..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="mt-4 w-full max-w-md rounded border border-slate-300 px-3 py-2 text-sm"
      />

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {data?.items.map((doctor) => (
          <Link
            key={doctor.id}
            to={`/doctors/${doctor.id}`}
            className="rounded border border-slate-200 bg-white p-4 hover:border-slate-400"
          >
            <p className="font-medium text-slate-900">{doctor.name}</p>
            <p className="text-sm text-slate-500">{doctor.specialization}</p>
            <p className="text-xs text-slate-400">{doctor.department}</p>
          </Link>
        ))}
        {data?.items.length === 0 && (
          <p className="text-sm text-slate-400">No doctors found.</p>
        )}
      </div>
    </Layout>
  )
}
