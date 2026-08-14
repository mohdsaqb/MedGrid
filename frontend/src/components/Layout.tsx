import type { ReactNode } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { Logo } from './Logo'

const NAV_LINK_BASE =
  'rounded-lg px-3 py-1.5 text-sm font-medium transition-colors whitespace-nowrap'
const NAV_LINK_ACTIVE = 'bg-brand-50 text-brand-700'
const NAV_LINK_INACTIVE = 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'

function navLinkClass({ isActive }: { isActive: boolean }) {
  return `${NAV_LINK_BASE} ${isActive ? NAV_LINK_ACTIVE : NAV_LINK_INACTIVE}`
}

function initials(fullName: string) {
  return fullName
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('')
}

export function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-3">
          <div className="flex min-w-0 items-center gap-6">
            <NavLink to="/patients" className="flex shrink-0 items-center gap-2">
              <Logo size={26} />
              <span className="text-base font-semibold tracking-tight text-slate-900">
                MedGrid
              </span>
            </NavLink>
            {user && (
              <nav className="flex flex-wrap items-center gap-1 overflow-x-auto">
                <NavLink to="/patients" className={navLinkClass}>
                  Patients
                </NavLink>
                <NavLink to="/doctors" className={navLinkClass}>
                  Doctors
                </NavLink>
                <NavLink to="/appointments" className={navLinkClass}>
                  Appointments
                </NavLink>
                {(user.role === 'ADMIN' || user.role === 'DOCTOR') && (
                  <NavLink to="/encounters" className={navLinkClass}>
                    Encounters
                  </NavLink>
                )}
                <NavLink to="/lab-tests" className={navLinkClass}>
                  Lab Tests
                </NavLink>
                {(user.role === 'ADMIN' ||
                  user.role === 'DOCTOR' ||
                  user.role === 'LAB_TECHNICIAN') && (
                  <NavLink to="/lab-orders" className={navLinkClass}>
                    Lab Dashboard
                  </NavLink>
                )}
                {(user.role === 'ADMIN' || user.role === 'BILLING_STAFF') && (
                  <NavLink to="/invoices" className={navLinkClass}>
                    Billing
                  </NavLink>
                )}
                {user.role === 'ADMIN' && (
                  <NavLink to="/reports" className={navLinkClass}>
                    Reports
                  </NavLink>
                )}
              </nav>
            )}
          </div>
          {user && (
            <div className="flex shrink-0 items-center gap-3">
              <div className="hidden items-center gap-2 sm:flex">
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-100 text-xs font-semibold text-brand-700">
                  {initials(user.full_name)}
                </span>
                <div className="text-sm leading-tight">
                  <p className="font-medium text-slate-900">{user.full_name}</p>
                  <p className="text-xs text-slate-500">{user.role.replace('_', ' ')}</p>
                </div>
              </div>
              <button
                onClick={handleLogout}
                className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50 hover:text-slate-900"
              >
                Sign out
              </button>
            </div>
          )}
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
    </div>
  )
}
