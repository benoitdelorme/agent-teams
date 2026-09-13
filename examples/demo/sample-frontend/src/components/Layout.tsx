import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth-context'
import { Button } from './ui'

const links = [
  { to: '/', label: 'Overview' },
  { to: '/projects', label: 'Projects' },
  { to: '/about', label: 'About' },
]

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <nav className="mx-auto flex max-w-4xl items-center gap-6 px-4 py-3">
          <NavLink to="/" className="flex items-center gap-2 font-semibold tracking-tight">
            <span className="inline-block h-2.5 w-2.5 rounded-full bg-blue-600" aria-hidden />
            Milestone
          </NavLink>
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === '/'}
              className={({ isActive }) => `text-sm ${isActive ? 'font-medium text-blue-600' : 'text-slate-500 hover:text-slate-900'}`}
            >
              {l.label}
            </NavLink>
          ))}
          <div className="ml-auto flex items-center gap-3">
            {user && <span className="text-sm text-slate-500">{user.name}</span>}
            <Button variant="ghost" onClick={handleLogout}>Sign out</Button>
          </div>
        </nav>
      </header>
      <main className="mx-auto max-w-4xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}
