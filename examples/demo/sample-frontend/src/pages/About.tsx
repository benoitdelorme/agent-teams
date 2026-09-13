import { Card, PageHeader } from '../components/ui'

export default function About() {
  return (
    <section>
      <PageHeader title="About Milestone" subtitle="A small project tracker that exists to be worked on by agent teams." />
      <div className="space-y-4 text-sm leading-6 text-slate-700">
        <Card>
          <h2 className="font-semibold text-slate-900">What it is</h2>
          <p className="mt-1">
            Projects, tasks with a priority and a status, a progress view. Small enough to read in ten minutes, real enough
            that a new feature touches an API contract, a database schema, a screen and a test.
          </p>
        </Card>
        <Card>
          <h2 className="font-semibold text-slate-900">How it is built</h2>
          <p className="mt-1">
            This interface is React 19, Vite and Tailwind. The API is FastAPI on SQLite. Each side has its own directory,
            its own commands and its own team when the agent teams are running. The frontend talks to the backend through
            the <code className="rounded bg-slate-100 px-1">/api</code> proxy on port 8010.
          </p>
        </Card>
        <Card>
          <h2 className="font-semibold text-slate-900">Try asking the manager for</h2>
          <ul className="mt-1 list-disc space-y-1 pl-5">
            <li>Archiving a project: hidden from the lists, still reachable by id, with a way to restore it.</li>
            <li>Due dates on tasks, with overdue tasks highlighted on the overview.</li>
            <li>A search box on the projects page that filters by name and description.</li>
          </ul>
        </Card>
      </div>
    </section>
  )
}
