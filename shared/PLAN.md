# Feature: Login + Dashboard protégé

## Goal (2 lines)
Email/password login (seeded user `admin@example.com` / `admin`) returning a Bearer JWT; existing `/api/*` data routes require it.
Frontend: `/login` page, auth context with token in localStorage, protected routes; `/` dashboard shows current user + existing stats + logout.

## Tasks
| id | team | task (1 line) | criteria (1 line) | status | notes |
| T1 | backend | Users table (id,email,password_hash,name,created_at) seeded with admin; POST /api/auth/login → {access_token, token_type:"bearer", user}; 401 on bad creds; GET /api/auth/me (Bearer) → user | contract in CONTRACTS.md#auth agreed by frontend; `uv run pytest` green incl. login ok/ko + me | todo | password hashing (passlib/bcrypt or hashlib pbkdf2), JWT via python-jose or PyJWT; secret via env with dev default |
| T2 | backend | Require Bearer JWT on /api/projects*, /api/tasks*, /api/stats (401 without/invalid); /health stays public | tests updated: unauth → 401, auth flow passes; `uv run pytest` green | todo | depends T1 |
| T3 | frontend | Auth layer: `lib/auth.tsx` (context: user, token, login, logout; token in localStorage), api.ts sends Authorization header + on 401 clears token → redirect /login; `pages/Login.tsx` (email/password form, error state, redirects to /) | `pnpm build` + `pnpm lint` green; manual: wrong creds shows error, right creds lands on / | todo | can start against CONTRACTS.md#auth once agreed, before T1 done |
| T4 | frontend | Protect all routes except /login via `RequireAuth`; Dashboard shows "Bonjour {user.name}", existing stats, Logout button in Layout | build/lint green; manual e2e: unauth → /login, login → dashboard with stats from real backend, logout → /login | todo | depends T2, T3 |

## Contracts → CONTRACTS.md#auth
