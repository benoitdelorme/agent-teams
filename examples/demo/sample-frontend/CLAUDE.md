# Milestone web app — working rules

- Stack: React 19 + TypeScript, Vite, Tailwind v4 (utility classes only, no CSS modules), react-router v7, pnpm.
- Run: `pnpm dev`. Verify before reporting done: `pnpm build` (type-check + build) and `pnpm lint`.
- Layout: `src/pages/<Route>.tsx` one component per route, `src/components/ui.tsx` shared primitives, `src/lib/api.ts` the only place that calls `fetch`.
- Data: pages load with `useFetch` and call `reload()` after a mutation. Add new endpoints to `api.ts` with their types; keep them in sync with the backend (`sample-backend/app/main.py`).
- Auth: a stored token is validated on start by `AuthProvider`; a 401 clears it and returns to `/login`.
- Copy: English, sentence case, short labels. Status and priority labels come from `STATUS_LABEL` / `PRIORITY_LABEL`, never hard-coded.
- No new dependencies without a note in the DONE message.
