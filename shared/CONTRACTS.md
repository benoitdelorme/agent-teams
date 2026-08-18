# API contracts (frontend ↔ backend)

Format per section:
```
## <anchor>  [proposed by <team>] | [agreed]
METHOD /path
req:  {...}          (or none)
res:  200 {...}
err:  404 not found, 400 ...
```
Current baseline: see sample-backend/app/main.py + sample-frontend/src/lib/api.ts.

## auth  [proposed by backend] [agreed]
User: {id:int, email:str, name:str, created_at:str}

POST /api/auth/login
req:  {email:str, password:str}
res:  200 {access_token:str, token_type:"bearer", user:User}
err:  401 {detail:"invalid credentials"}, 422 validation

GET /api/auth/me   (header: Authorization: Bearer <access_token>)
res:  200 User
err:  401 {detail:"not authenticated"} (missing/invalid/expired token)

Guard: all /api/* except /api/health and /api/auth/login require Bearer → 401 {detail:"not authenticated"} otherwise.
Token: JWT HS256, exp 24h. Seed user: admin@example.com / admin.
