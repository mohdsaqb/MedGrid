import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { useParams } from 'react-router-dom'
import { api, ApiError } from '../lib/api'
import { Layout } from '../components/Layout'
import { useAuth } from '../auth/AuthContext'
import type { Encounter, RecordType } from './types'

const RECORD_TYPES: RecordType[] = ['VITALS', 'DIAGNOSIS', 'PRESCRIPTION', 'PROCEDURE', 'GENERAL_NOTE']

export function EncounterDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { user } = useAuth()
  const [encounter, setEncounter] = useState<Encounter | null>(null)
  const [error, setError] = useState<string | null>(null)

  const [recordType, setRecordType] = useState<RecordType>('GENERAL_NOTE')
  const [description, setDescription] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  const canDocument = user?.role === 'DOCTOR'

  const load = useCallback(() => {
    if (!id) return
    api
      .get<Encounter>(`/encounters/${id}`)
      .then(setEncounter)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load encounter'))
  }, [id])

  useEffect(() => {
    load()
  }, [load])

  async function handleAddRecord(event: FormEvent) {
    event.preventDefault()
    if (!id) return
    setActionError(null)
    setSubmitting(true)
    try {
      await api.post(`/encounters/${id}/clinical-records`, {
        record_type: recordType,
        description,
      })
      setDescription('')
      load()
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : 'Failed to add clinical record')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleClose() {
    if (!id || !confirm('Close this encounter? No further clinical records can be added afterward.'))
      return
    setActionError(null)
    try {
      await api.patch(`/encounters/${id}/close`, {})
      load()
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : 'Failed to close encounter')
    }
  }

  if (error) {
    return (
      <Layout>
        <p className="text-sm text-red-600">{error}</p>
      </Layout>
    )
  }
  if (!encounter) {
    return (
      <Layout>
        <p className="text-sm text-slate-500">Loading...</p>
      </Layout>
    )
  }

  const isOpen = encounter.status === 'OPEN'

  return (
    <Layout>
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-slate-900">
          Encounter - {encounter.patient.first_name} {encounter.patient.last_name}
        </h1>
        <span
          className={`rounded px-2 py-1 text-xs font-medium ${
            isOpen ? 'bg-blue-50 text-blue-700' : 'bg-slate-100 text-slate-500'
          }`}
        >
          {encounter.status}
        </span>
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-x-6 gap-y-3 rounded border border-slate-200 bg-white p-4 text-sm max-w-2xl">
        <dt className="text-slate-500">Doctor</dt>
        <dd className="text-slate-900">{encounter.doctor.name}</dd>

        <dt className="text-slate-500">Date</dt>
        <dd className="text-slate-900">{new Date(encounter.encounter_date).toLocaleString()}</dd>

        <dt className="text-slate-500">Symptoms</dt>
        <dd className="text-slate-900">{encounter.symptoms}</dd>

        <dt className="text-slate-500">Diagnosis</dt>
        <dd className="text-slate-900">{encounter.diagnosis}</dd>

        {encounter.notes && (
          <>
            <dt className="text-slate-500">Notes</dt>
            <dd className="text-slate-900">{encounter.notes}</dd>
          </>
        )}
      </dl>

      <div className="mt-6 max-w-2xl">
        <h2 className="text-sm font-semibold text-slate-700">Clinical Records</h2>
        <ul className="mt-2 space-y-2">
          {encounter.clinical_records.map((r) => (
            <li key={r.id} className="rounded border border-slate-200 bg-white p-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="font-medium text-slate-900">{r.record_type}</span>
                <span className="text-xs text-slate-400">
                  {new Date(r.created_at).toLocaleString()}
                </span>
              </div>
              <p className="mt-1 text-slate-700">{r.description}</p>
            </li>
          ))}
          {encounter.clinical_records.length === 0 && (
            <p className="text-sm text-slate-400">No clinical records yet.</p>
          )}
        </ul>
      </div>

      {canDocument && isOpen && (
        <div className="mt-6 max-w-2xl rounded border border-slate-200 bg-white p-4">
          <h2 className="text-sm font-semibold text-slate-700">Add Clinical Note</h2>
          <form onSubmit={handleAddRecord} className="mt-3 space-y-3">
            <select
              value={recordType}
              onChange={(e) => setRecordType(e.target.value as RecordType)}
              className="rounded border border-slate-300 px-3 py-2 text-sm"
            >
              {RECORD_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
            <textarea
              required
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe the finding, prescription, procedure, or note..."
              className="w-full rounded border border-slate-300 px-3 py-2 text-sm"
              rows={3}
            />
            {actionError && <p className="text-sm text-red-600">{actionError}</p>}
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={submitting}
                className="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
              >
                {submitting ? 'Adding...' : 'Add Record'}
              </button>
              <button
                type="button"
                onClick={handleClose}
                className="rounded border border-red-300 px-4 py-2 text-sm text-red-600"
              >
                Close Encounter
              </button>
            </div>
          </form>
        </div>
      )}
    </Layout>
  )
}
