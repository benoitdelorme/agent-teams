import type { ReactNode } from 'react'
import { STATUS_LABEL, type Status } from '../lib/api'

export const Card = ({ children, className = '' }: { children: ReactNode; className?: string }) => (
  <div className={`rounded-xl border border-slate-200 bg-white p-4 shadow-sm ${className}`}>{children}</div>
)

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'ghost' | 'danger' }
export const Button = ({ children, variant = 'primary', className = '', ...p }: ButtonProps) => {
  const look = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700',
    ghost: 'text-slate-600 hover:bg-slate-100',
    danger: 'text-red-600 hover:bg-red-50',
  }[variant]
  return (
    <button className={`rounded-lg px-3 py-1.5 text-sm font-medium transition disabled:opacity-50 ${look} ${className}`} {...p}>
      {children}
    </button>
  )
}

const field = 'rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200'
export const Input = ({ className = '', ...p }: React.InputHTMLAttributes<HTMLInputElement>) => (
  <input className={`${field} ${className}`} {...p} />
)
export const Select = ({ className = '', ...p }: React.SelectHTMLAttributes<HTMLSelectElement>) => (
  <select className={`${field} ${className}`} {...p} />
)

const badge: Record<Status, string> = {
  todo: 'bg-slate-100 text-slate-700',
  doing: 'bg-amber-100 text-amber-800',
  done: 'bg-emerald-100 text-emerald-800',
}
export const StatusBadge = ({ status }: { status: Status }) => (
  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${badge[status]}`}>{STATUS_LABEL[status]}</span>
)

export const Progress = ({ done, total }: { done: number; total: number }) => {
  const pct = total ? Math.round((done / total) * 100) : 0
  return (
    <div className="flex items-center gap-2" title={`${done} of ${total} tasks done`}>
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-100">
        <div className="h-full rounded-full bg-emerald-500 transition-all" style={{ width: `${pct}%` }} />
      </div>
      <span className="w-9 text-right text-xs tabular-nums text-slate-500">{pct}%</span>
    </div>
  )
}

export const PageHeader = ({ title, subtitle, children }: { title: string; subtitle?: string; children?: ReactNode }) => (
  <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
    <div>
      <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
      {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
    </div>
    {children}
  </div>
)

export const State = ({ loading, error }: { loading: boolean; error: string | null }) =>
  loading ? (
    <p className="text-sm text-slate-500">Loading…</p>
  ) : error ? (
    <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
  ) : null

export const Empty = ({ children }: { children: ReactNode }) => (
  <p className="rounded-xl border border-dashed border-slate-300 px-4 py-8 text-center text-sm text-slate-500">{children}</p>
)
