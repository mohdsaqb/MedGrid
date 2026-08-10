import { useState } from 'react'
import type { FormEvent } from 'react'
import type { BloodGroup, Gender, PatientInput } from './types'

const GENDERS: Gender[] = ['MALE', 'FEMALE', 'OTHER', 'UNKNOWN']
const BLOOD_GROUPS: BloodGroup[] = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']

type Props = {
  initial?: PatientInput
  submitLabel: string
  onSubmit: (data: PatientInput) => Promise<void>
}

const EMPTY: PatientInput = {
  first_name: '',
  last_name: '',
  date_of_birth: '',
  gender: null,
  email: null,
  phone: '',
  address: null,
  blood_group: null,
}

export function PatientForm({ initial, submitLabel, onSubmit }: Props) {
  const [form, setForm] = useState<PatientInput>(initial ?? EMPTY)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  function set<K extends keyof PatientInput>(key: K, value: PatientInput[K]) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await onSubmit(form)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-w-lg">
      <div className="grid grid-cols-2 gap-4">
        <label className="block text-sm font-medium text-slate-700">
          First name
          <input
            required
            value={form.first_name}
            onChange={(e) => set('first_name', e.target.value)}
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
          />
        </label>
        <label className="block text-sm font-medium text-slate-700">
          Last name
          <input
            required
            value={form.last_name}
            onChange={(e) => set('last_name', e.target.value)}
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
          />
        </label>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <label className="block text-sm font-medium text-slate-700">
          Date of birth
          <input
            type="date"
            required
            value={form.date_of_birth}
            onChange={(e) => set('date_of_birth', e.target.value)}
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
          />
        </label>
        <label className="block text-sm font-medium text-slate-700">
          Gender
          <select
            value={form.gender ?? ''}
            onChange={(e) => set('gender', (e.target.value || null) as Gender | null)}
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
          >
            <option value="">Not specified</option>
            {GENDERS.map((g) => (
              <option key={g} value={g}>
                {g}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <label className="block text-sm font-medium text-slate-700">
          Phone
          <input
            required
            value={form.phone}
            onChange={(e) => set('phone', e.target.value)}
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
          />
        </label>
        <label className="block text-sm font-medium text-slate-700">
          Email
          <input
            type="email"
            value={form.email ?? ''}
            onChange={(e) => set('email', e.target.value || null)}
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
          />
        </label>
      </div>

      <label className="block text-sm font-medium text-slate-700">
        Address
        <textarea
          value={form.address ?? ''}
          onChange={(e) => set('address', e.target.value || null)}
          className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
          rows={2}
        />
      </label>

      <label className="block text-sm font-medium text-slate-700">
        Blood group
        <select
          value={form.blood_group ?? ''}
          onChange={(e) => set('blood_group', (e.target.value || null) as BloodGroup | null)}
          className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
        >
          <option value="">Unknown</option>
          {BLOOD_GROUPS.map((b) => (
            <option key={b} value={b}>
              {b}
            </option>
          ))}
        </select>
      </label>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <button
        type="submit"
        disabled={submitting}
        className="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {submitting ? 'Saving...' : submitLabel}
      </button>
    </form>
  )
}
