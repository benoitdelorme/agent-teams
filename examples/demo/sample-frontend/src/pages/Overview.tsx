import { Link } from 'react-router-dom'
import { api } from '../lib/api'
import { useFetch } from '../lib/useFetch'
import { useAuth } from '../lib/auth-context'
import { Card, Empty, PageHeader, Progress, State } from '../components/ui'

export default function Overview() {
  const { user } = useAuth()
  const stats = useFetch(api.stats)
  const projects = useFetch(api.projects.list)

  return (
    <section>
      <PageHeader title={`Hello ${user?.name ?? 'there'}`} subtitle="Where every project stands right now." />
      <State loading={stats.loading} error={stats.error} />
      {stats.data && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
          <Stat label="Projects" value={stats.data.projects} />
          <Stat label="Tasks" value={stats.data.tasks} />
          <Stat label="To do" value={stats.data.by_status.todo} />
          <Stat label="In progress" value={stats.data.by_status.doing} />
          <Stat label="Done" value={stats.data.by_status.done} />
        </div>
      )}

      <h2 className="mb-3 mt-8 text-sm font-semibold uppercase tracking-wide text-slate-500">Progress by project</h2>
      <State loading={projects.loading} error={projects.error} />
      {projects.data?.length === 0 && <Empty>No projects yet. Create one from the Projects page.</Empty>}
      <div className="space-y-2">
        {projects.data?.map((p) => (
          <Card key={p.id} className="flex items-center gap-4">
            <Link to={`/projects/${p.id}`} className="w-48 shrink-0 truncate font-medium hover:text-blue-600">{p.name}</Link>
            <div className="flex-1"><Progress done={p.done_count} total={p.task_count} /></div>
            <span className="w-24 text-right text-xs text-slate-500">{p.done_count}/{p.task_count} done</span>
          </Card>
        ))}
      </div>
    </section>
  )
}

const Stat = ({ label, value }: { label: string; value: number }) => (
  <Card>
    <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
    <p className="mt-1 text-2xl font-semibold tabular-nums">{value}</p>
  </Card>
)
