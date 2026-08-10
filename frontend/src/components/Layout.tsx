import type { ReactNode } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-3">
          <div className="flex items-center gap-5">
            <Link to="/patients" className="font-semibold text-slate-900">
              MedGrid
            </Link>
            {user && (
              <nav className="flex gap-4 text-sm text-slate-600">
                <Link to="/patients" className="hover:text-slate-900">
                  Patients
                </Link>
                <Link to="/doctors" className="hover:text-slate-900">
                  Doctors
                </Link>
                <Link to="/appointments" className="hover:text-slate-900">
                  Appointments
                </Link>
                {(user.role === 'ADMIN' || user.role === 'DOCTOR') && (
                  <Link to="/encounters" className="hover:text-slate-900">
                    Encounters
                  </Link>
                )}
                <Link to="/lab-tests" className="hover:text-slate-900">
                  Lab Tests
                </Link>
                {(user.role === 'ADMIN' ||
                  user.role === 'DOCTOR' ||
                  user.role === 'LAB_TECHNICIAN') && (
                  <Link to="/lab-orders" className="hover:text-slate-900">
                    Lab Dashboard
                  </Link>
                )}
                {(user.role === 'ADMIN' || user.role === 'BILLING_STAFF') && (
                  <Link to="/invoices" className="hover:text-slate-900">
                    Billing
                  </Link>
                )}
                {user.role === 'ADMIN' && (
                  <Link to="/reports" className="hover:text-slate-900">
                    Reports
                  </Link>
                )}
              </nav>
            )}
          </div>
          {user && (
            <div className="flex items-center gap-3 text-sm text-slate-600">
              <span>
                {user.full_name} <span className="text-slate-400">({user.role})</span>
              </span>
              <button onClick={handleLogout} className="text-slate-500 underline">
                Sign out
              </button>
            </div>
          )}
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-6 py-6">{children}</main>
    </div>
  )
}
