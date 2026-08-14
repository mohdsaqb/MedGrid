import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { api, ApiError } from '../lib/api'
import { Layout } from '../components/Layout'
import { useAuth } from '../auth/AuthContext'
import type { LabTest, LabTestPage } from './types'

export function LabTestCatalogPage() {
  const { user } = useAuth()
  const [data, setData] = useState<LabTestPage | null>(null)
  const [error, setError] = useState<string | null>(null)

  const [name, setName] = useState('')
  const [price, setPrice] = useState('')
  const [normalRange, setNormalRange] = useState('')
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const canManage = user?.role === 'ADMIN'

  function load() {
    api
      .get<LabTestPage>('/lab-tests?page_size=100')
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load tests'))
  }

  useEffect(load, [])

  async function handleCreate(event: FormEvent) {
    event.preventDefault()
    setFormError(null)
    setSubmitting(true)
    try {
      await api.post<LabTest>('/lab-tests', {
        name,
        price: Number(price),
        normal_range: normalRange || null,
        description: null,
      })
      setName('')
      setPrice('')
      setNormalRange('')
      load()
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : 'Failed to create test')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Layout>
      <h1 className="text-xl font-semibold tracking-tight text-slate-900">Lab Test Catalog</h1>

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

      <div className="mt-4 overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-slate-500">
            <tr>
              <th className="px-4 py-2">Name</th>
              <th className="px-4 py-2">Price</th>
              <th className="px-4 py-2">Normal Range</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((t) => (
              <tr key={t.id} className="border-b border-slate-100 transition-colors last:border-0 hover:bg-slate-50">
                <td className="px-4 py-2">{t.name}</td>
                <td className="px-4 py-2">${t.price}</td>
                <td className="px-4 py-2">{t.normal_range ?? '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {canManage && (
        <div className="mt-6 max-w-md rounded-xl border border-slate-200 bg-white shadow-sm p-4">
          <h2 className="text-sm font-semibold text-slate-700">Add Test to Catalog</h2>
          <form onSubmit={handleCreate} className="mt-3 space-y-3">
            <input
              required
              placeholder="Test name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm transition-colors focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
            />
            <input
              required
              type="number"
              step="0.01"
              min="0.01"
              placeholder="Price"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm transition-colors focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
            />
            <input
              placeholder="Normal range (optional)"
              value={normalRange}
              onChange={(e) => setNormalRange(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm transition-colors focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
            />
            {formError && <p className="text-sm text-red-600">{formError}</p>}
            <button
              type="submit"
              disabled={submitting}
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {submitting ? 'Adding...' : 'Add Test'}
            </button>
          </form>
        </div>
      )}
    </Layout>
  )
}
