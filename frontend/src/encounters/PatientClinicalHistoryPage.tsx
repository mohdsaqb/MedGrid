import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../lib/api'
import { Layout } from '../components/Layout'
import type { Encounter } from './types'

export function PatientClinicalHistoryPage() {
  const { id } = useParams<{ id: string }>()
  const [history, setHistory] = useState<Encounter[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    api
      .get<Encounter[]>(`/patients/${id}/clinical-history`)
      .then(setHistory)
      .catch((err) =>
        setError(err instanceof Error ? err.message : 'Failed to load clinical history'),
      )
  }, [id])

  return (
    <Layout>
      <h1 className="text-xl font-semibold tracking-tight text-slate-900">Clinical History</h1>

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

      {history && (
        <div className="mt-4 max-w-2xl space-y-4">
          {history.length === 0 && (
            <p className="text-sm text-slate-400">No encounters recorded for this patient yet.</p>
          )}
          {history.map((enc) => (
            <div key={enc.id} className="rounded-xl border border-slate-200 bg-white shadow-sm p-4">
              <div className="flex items-center justify-between">
                <Link to={`/encounters/${enc.id}`} className="font-medium text-brand-600 transition-colors hover:text-brand-700 hover:underline">
                  {new Date(enc.encounter_date).toLocaleString()} - {enc.doctor.name}
                </Link>
                <span
                  className={`rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ring-black/5 ${
                    enc.status === 'OPEN'
                      ? 'bg-blue-50 text-blue-700'
                      : 'bg-slate-100 text-slate-500'
                  }`}
                >
                  {enc.status}
                </span>
              </div>
              <p className="mt-2 text-sm text-slate-700">
                <span className="text-slate-500">Diagnosis:</span> {enc.diagnosis}
              </p>
              <p className="mt-1 text-sm text-slate-700">
                <span className="text-slate-500">Symptoms:</span> {enc.symptoms}
              </p>

              {enc.clinical_records.length > 0 && (
                <ul className="mt-3 space-y-1 border-t border-slate-100 pt-2">
                  {enc.clinical_records.map((r) => (
                    <li key={r.id} className="text-sm text-slate-600">
                      <span className="font-medium text-slate-800">{r.record_type}:</span>{' '}
                      {r.description}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      )}
    </Layout>
  )
}
