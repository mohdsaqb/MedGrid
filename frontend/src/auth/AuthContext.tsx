import { createContext, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { api, login as apiLogin } from '../lib/api'

export type CurrentUser = {
  id: string
  email: string
  full_name: string
  role: 'ADMIN' | 'DOCTOR' | 'PATIENT' | 'LAB_TECHNICIAN' | 'BILLING_STAFF'
  is_active: boolean
}

type AuthContextValue = {
  user: CurrentUser | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null)
  // Starts true: on page load we don't yet know if the stored token is
  // still valid until /auth/me responds - avoids a flash of "logged out".
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      setLoading(false)
      return
    }
    api
      .get<CurrentUser>('/auth/me')
      .then(setUser)
      .catch(() => localStorage.removeItem('access_token'))
      .finally(() => setLoading(false))
  }, [])

  async function login(email: string, password: string) {
    const token = await apiLogin(email, password)
    localStorage.setItem('access_token', token)
    const me = await api.get<CurrentUser>('/auth/me')
    setUser(me)
  }

  function logout() {
    localStorage.removeItem('access_token')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider')
  return ctx
}
