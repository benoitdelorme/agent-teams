# Milestone web app

The frontend of the Milestone demo: React 19, Vite, Tailwind v4, react-router. It talks to the API through the Vite proxy (`/api` → `http://localhost:8010`).

```bash
pnpm install
pnpm dev        # http://localhost:5173
pnpm build      # type-check + production build
pnpm lint       # oxlint
```

Demo account: `admin@example.com` / `admin`.

| Route | Page |
| --- | --- |
| `/login` | Sign in. |
| `/` | Overview: counts by status and progress per project. |
| `/projects` | Projects: create, delete, progress. |
| `/projects/:id` | Tasks of a project: add with a priority, filter by status, change status, delete. |
| `/about` | What the demo is and a few features to ask the teams for. |

Code map: `src/lib/api.ts` typed client and labels, `src/lib/auth.tsx` session provider, `src/components/ui.tsx` the handful of shared components, `src/pages/` one file per route.
