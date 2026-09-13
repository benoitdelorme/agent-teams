import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../lib/auth-context'

export default function RequireAuth() {
  const { token, loading } = useAuth()
  if (loading) return <p className="p-6 text-sm text-slate-500">Loading…</p>
  if (!token) return <Navigate to="/login" replace />
  return <Outlet />
}
