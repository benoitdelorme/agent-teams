import { useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, PRIORITY_LABEL, STATUS_LABEL, STATUSES, type Priority, type Status } from '../lib/api'
import { useFetch } from '../lib/useFetch'
import { Button, Card, Empty, Input, PageHeader, Progress, Select, State, StatusBadge } from '../components/ui'

export default function ProjectDetail() {
  const id = Number(useParams().id)
  const [filter, setFilter] = useState<Status | undefined>()
  const project = useFetch(() => api.projects.get(id), [id])
  const tasks = useFetch(() => api.tasks.list(id, filter), [id, filter])
  const [title, setTitle] = useState('')
  const [priority, setPriority] = useState<Priority>(2)

  function refresh() {
    project.reload()
    tasks.reload()
  }

  async function add(e: FormEvent) {
    e.preventDefault()
    if (!title.trim()) return
    await api.tasks.create(id, { title: title.trim(), priority })
    setTitle('')
    refresh()
  }

  return (
    <section>
      <Link to="/projects" className="text-sm text-slate-500 hover:text-slate-900">← All projects</Link>
      <State loading={project.loading} error={project.error} />
      {project.data && (
        <div className="mt-2">
          <PageHeader title={project.data.name} subtitle={project.data.description || undefined} />
          <Card className="mb-6"><Progress done={project.data.done_count} total={project.data.task_count} /></Card>
        </div>
      )}

      <form onSubmit={add} className="mb-4 flex flex-wrap gap-2">
        <Input placeholder="New task" value={title} onChange={(e) => setTitle(e.target.value)} className="flex-1" required />
        <Select value={priority} onChange={(e) => setPriority(Number(e.target.value) as Priority)} aria-label="Priority">
          {([1, 2, 3] as Priority[]).map((p) => <option key={p} value={p}>{PRIORITY_LABEL[p]} priority</option>)}
        </Select>
        <Button type="submit">Add task</Button>
      </form>

      <div className="mb-3 flex gap-1">
        <Chip active={!filter} onClick={() => setFilter(undefined)}>All</Chip>
        {STATUSES.map((s) => <Chip key={s} active={filter === s} onClick={() => setFilter(s)}>{STATUS_LABEL[s]}</Chip>)}
      </div>

      <State loading={tasks.loading} error={tasks.error} />
      {tasks.data?.length === 0 && <Empty>{filter ? `No task is ${STATUS_LABEL[filter].toLowerCase()}.` : 'No tasks yet. Add the first one above.'}</Empty>}
      <ul className="space-y-2">
        {tasks.data?.map((t) => (
          <Card key={t.id} className="flex items-center gap-3">
            <span className={`w-14 text-xs font-medium ${t.priority === 1 ? 'text-red-600' : t.priority === 3 ? 'text-slate-400' : 'text-slate-500'}`}>
              {PRIORITY_LABEL[t.priority]}
            </span>
            <span className={`flex-1 ${t.status === 'done' ? 'text-slate-400 line-through' : ''}`}>{t.title}</span>
            <StatusBadge status={t.status} />
            <Select value={t.status} aria-label="Status" onChange={(e) => api.tasks.patch(t.id, { status: e.target.value as Status }).then(refresh)}>
              {STATUSES.map((s) => <option key={s} value={s}>{STATUS_LABEL[s]}</option>)}
            </Select>
            <Button variant="danger" aria-label="Delete task" onClick={() => api.tasks.remove(t.id).then(refresh)}>✕</Button>
          </Card>
        ))}
      </ul>
    </section>
  )
}

const Chip = ({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) => (
  <button
    onClick={onClick}
    className={`rounded-full px-3 py-1 text-xs font-medium transition ${active ? 'bg-slate-900 text-white' : 'bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-100'}`}
  >
    {children}
  </button>
)
