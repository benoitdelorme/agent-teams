// Typed client for the Milestone API. Every call goes through the Vite proxy (/api → :8010).
export type Status = 'todo' | 'doing' | 'done'
export type Priority = 1 | 2 | 3
export interface Project { id: number; name: string; description: string; created_at: string; task_count: number; done_count: number }
export interface Task { id: number; project_id: number; title: string; status: Status; priority: Priority; created_at: string }
export interface Stats { projects: number; tasks: number; by_status: Record<Status, number> }
export interface User { id: number; email: string; name: string; created_at: string }

export const STATUSES: Status[] = ['todo', 'doing', 'done']
export const STATUS_LABEL: Record<Status, string> = { todo: 'To do', doing: 'In progress', done: 'Done' }
export const PRIORITY_LABEL: Record<Priority, string> = { 1: 'High', 2: 'Medium', 3: 'Low' }

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const token = localStorage.getItem('token')
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) headers.Authorization = `Bearer ${token}`
  const res = await fetch(`/api${path}`, { headers, ...init })
  if (res.status === 401) {
    localStorage.removeItem('token')
    if (window.location.pathname !== '/login') window.location.assign('/login')
  }
  if (!res.ok) {
    let detail = res.statusText
    try {
      detail = (await res.json()).detail ?? detail
    } catch {
      // not JSON: keep the status text
    }
    throw new ApiError(res.status, typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  return res.status === 204 ? (undefined as T) : res.json()
}

export const api = {
  auth: {
    login: (email: string, password: string) =>
      req<{ access_token: string; token_type: string; user: User }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }),
    me: () => req<User>('/auth/me'),
  },
  stats: () => req<Stats>('/stats'),
  projects: {
    list: () => req<Project[]>('/projects'),
    get: (id: number) => req<Project>(`/projects/${id}`),
    create: (body: { name: string; description?: string }) =>
      req<Project>('/projects', { method: 'POST', body: JSON.stringify(body) }),
    remove: (id: number) => req<void>(`/projects/${id}`, { method: 'DELETE' }),
  },
  tasks: {
    list: (projectId: number, status?: Status) =>
      req<Task[]>(`/projects/${projectId}/tasks${status ? `?status=${status}` : ''}`),
    create: (projectId: number, body: { title: string; status?: Status; priority?: Priority }) =>
      req<Task>(`/projects/${projectId}/tasks`, { method: 'POST', body: JSON.stringify(body) }),
    patch: (id: number, body: Partial<Pick<Task, 'title' | 'status' | 'priority'>>) =>
      req<Task>(`/tasks/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
    remove: (id: number) => req<void>(`/tasks/${id}`, { method: 'DELETE' }),
  },
}
