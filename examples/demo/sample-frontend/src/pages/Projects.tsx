import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'
import { useFetch } from '../lib/useFetch'
import { Button, Card, Empty, Input, PageHeader, Progress, State } from '../components/ui'

export default function Projects() {
  const { data, loading, error, reload } = useFetch(api.projects.list)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [saving, setSaving] = useState(false)

  async function create(e: FormEvent) {
    e.preventDefault()
    if (!name.trim()) return
    setSaving(true)
    try {
      await api.projects.create({ name: name.trim(), description: description.trim() })
      setName('')
      setDescription('')
      reload()
    } finally {
      setSaving(false)
    }
  }

  async function remove(id: number, projectName: string) {
    if (!confirm(`Delete "${projectName}" and all its tasks?`)) return
    await api.projects.remove(id)
    reload()
  }

  return (
    <section>
      <PageHeader title="Projects" subtitle="One card per project, with how far along it is." />
      <form onSubmit={create} className="mb-6 flex flex-wrap gap-2">
        <Input placeholder="Project name" value={name} onChange={(e) => setName(e.target.value)} className="w-56" required />
        <Input placeholder="Short description (optional)" value={description} onChange={(e) => setDescription(e.target.value)} className="flex-1" />
        <Button type="submit" disabled={saving}>Add project</Button>
      </form>
      <State loading={loading} error={error} />
      {data?.length === 0 && <Empty>No projects yet. Add the first one above.</Empty>}
      <div className="grid gap-3 md:grid-cols-2">
        {data?.map((p) => (
          <Card key={p.id} className="flex flex-col gap-3">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <Link to={`/projects/${p.id}`} className="font-medium hover:text-blue-600">{p.name}</Link>
                <p className="mt-0.5 truncate text-sm text-slate-500">{p.description || 'No description'}</p>
              </div>
              <Button variant="danger" onClick={() => remove(p.id, p.name)}>Delete</Button>
            </div>
            <Progress done={p.done_count} total={p.task_count} />
            <p className="text-xs text-slate-500">{p.task_count === 1 ? '1 task' : `${p.task_count} tasks`}</p>
          </Card>
        ))}
      </div>
    </section>
  )
}
