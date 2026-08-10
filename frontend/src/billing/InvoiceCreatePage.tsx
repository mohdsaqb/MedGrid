import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, ApiError } from '../lib/api'
import { Layout } from '../components/Layout'
import type { Invoice } from './types'

type PatientOption = { id: string; first_name: string; last_name: string; patient_number: string }
type PatientSearchResult = { items: PatientOption[] }

export function InvoiceCreatePage() {
  const navigate = useNavigate()
  const [patientSearch, setPatientSearch] = useState('')
  const [patientResults, setPatientResults] = useState<PatientOption[]>([])
  const [selectedPatient, setSelectedPatient] = useState<PatientOption | null>(null)
  const [amount, setAmount] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!patientSearch) {
      setPatientResults([])
      return
    }
    const timeout = setTimeout(() => {
      api
        .get<PatientSearchResult>(
          `/patients?search=${encodeURIComponent(patientSearch)}&page_size=5`,
        )
        .then((page) => setPatientResults(page.items))
        .catch(() => setPatientResults([]))
    }, 300)
    return () => clearTimeout(timeout)
  }, [patientSearch])

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    if (!selectedPatient) {
      setError('Please select a patient')
      return
    }
    setSubmitting(true)
    try {
      const created = await api.post<Invoice>('/invoices', {
        patient_id: selectedPatient.id,
        amount: Number(amount),
      })
      navigate(`/invoices/${created.id}`)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to create invoice')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Layout>
      <h1 className="text-lg font-semibold text-slate-900">New Invoice</h1>

      <form onSubmit={handleSubmit} className="mt-4 max-w-lg space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700">Patient</label>
          {selectedPatient ? (
            <div className="mt-1 flex items-center justify-between rounded border border-slate-300 px-3 py-2 text-sm">
              <span>
                {selectedPatient.first_name} {selectedPatient.last_name}{' '}
                <span className="text-slate-400">({selectedPatient.patient_number})</span>
              </span>
              <button
                type="button"
                onClick={() => {
                  setSelectedPatient(null)
                  setPatientSearch('')
                }}
                className="text-xs text-slate-500 underline"
              >
                Change
              </button>
            </div>
          ) : (
            <>
              <input
                value={patientSearch}
                onChange={(e) => setPatientSearch(e.target.value)}
                placeholder="Search patient by name, number, or phone..."
                className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
              />
              {patientResults.length > 0 && (
                <ul className="mt-1 rounded border border-slate-200 bg-white text-sm shadow-sm">
                  {patientResults.map((p) => (
                    <li key={p.id}>
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedPatient(p)
                          setPatientResults([])
                        }}
                        className="w-full px-3 py-2 text-left hover:bg-slate-50"
                      >
                        {p.first_name} {p.last_name}{' '}
                        <span className="text-slate-400">({p.patient_number})</span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </>
          )}
        </div>

        <label className="block text-sm font-medium text-slate-700">
          Amount ($)
          <input
            required
            type="number"
            step="0.01"
            min="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
          />
        </label>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {submitting ? 'Creating...' : 'Create Invoice'}
        </button>
      </form>
    </Layout>
  )
}
