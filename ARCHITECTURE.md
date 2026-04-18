# Memòria de projecte — Arquitectura i decisions tècniques
# Versió 2 — actualitzada amb lliçons del Sprint 1

---

## 1. Identitat i abast

### Stack tecnològic

| Capa | Tecnologia | Versió | Notes |
|---|---|---|---|
| Frontend web | Next.js / React | 14+ App Router | TypeScript strict |
| Estils | Tailwind CSS | 3+ | |
| Backend API | FastAPI | 0.116+ | Python 3.12+ |
| Base de dades | PostgreSQL | 16+ | Producció + tests |
| Migracions | Alembic | 1.14+ | Async, amb rollback |
| Auth | Supabase Auth | 2+ | JWT access 15min + refresh 7 dies |
| Temps real | WebSockets | FastAPI natiu | Per col·laboració |
| Estat global | Zustand | 4+ | |
| Dades servidor | TanStack Query | 5+ | |
| Tests backend | pytest + asyncpg | 8+ | BD PostgreSQL real al CI |
| Tests frontend | Jest + babel-jest | | jest.config.js (no .ts) |
| Linting backend | ruff | 0.8+ | |
| Linting frontend | ESLint | Next.js config | |
| Android proves | TWA via Bubblewrap | | |
| Android final | Capacitor | 6+ | |
| iOS | Capacitor + Xcode | | Post-MVP |
| Cloud frontend | Vercel | | CDN global |
| Cloud backend | Railway | | FastAPI + PostgreSQL |
| Monitoratge | Sentry | 2+ | Sense PII |

### Repositori
- **GitHub:** https://github.com/NackerWD/my-lists-app
- **Visibilitat:** públic (la protecció de branques requereix pla de pagament en privats)
- **Branca principal:** `main`
- **Branca d'integració:** `develop`
- **Features:** `feature/nom-funcionalitat` — base sempre `develop`

### Estructura del monorepo

```
/
├── web/                          # Next.js frontend
│   ├── app/
│   │   ├── (auth)/               # login, register — SSG
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   ├── (app)/                # pàgines protegides — SSR
│   │   │   ├── home/page.tsx
│   │   │   └── lists/
│   │   │       ├── page.tsx
│   │   │       └── [id]/page.tsx
│   │   ├── onboarding/page.tsx
│   │   └── layout.tsx
│   ├── components/
│   │   ├── ui/
│   │   │   ├── NavBar.tsx
│   │   │   └── SideMenu.tsx
│   │   ├── lists/
│   │   ├── items/
│   │   ├── collaboration/
│   │   └── offline/
│   ├── lib/
│   │   ├── api/client.ts         # fetch wrapper + 401/offline handling
│   │   ├── stores/
│   │   │   ├── auth.store.ts     # Zustand: user, login, logout, refresh
│   │   │   └── offline.store.ts  # Zustand: isOnline, queue
│   │   ├── hooks/
│   │   ├── utils/
│   │   ├── ws/client.ts          # WebSocket amb backoff exponencial
│   │   ├── offline/queue.ts      # IndexedDB via idb
│   │   └── supabase.ts           # client Supabase (anon key)
│   ├── tests/
│   │   └── auth.test.tsx
│   ├── __mocks__/
│   │   └── fileMock.js
│   ├── public/
│   │   └── .well-known/
│   │       └── assetlinks.json   # TWA Android
│   ├── jest.config.js            # JS no TS — evita ts-node
│   ├── jest.setup.js
│   ├── middleware.ts              # getUser() server-side (mai getSession())
│   ├── next.config.ts
│   ├── capacitor.config.ts
│   └── package.json
├── mobile/
│   ├── android/
│   └── ios/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── auth.py       # register, login, logout, refresh, me
│   │   │   │   ├── lists.py
│   │   │   │   ├── list_items.py
│   │   │   │   ├── list_members.py
│   │   │   │   ├── list_invitations.py
│   │   │   │   └── users.py      # GET/PATCH /users/me
│   │   │   └── router.py
│   │   ├── core/
│   │   │   ├── config.py         # Pydantic BaseSettings
│   │   │   ├── database.py       # AsyncEngine, get_db dependency
│   │   │   ├── security.py       # verify_supabase_token, get_current_user
│   │   │   └── limiter.py        # SlowAPI
│   │   ├── models/               # SQLAlchemy async — 8 taules
│   │   ├── schemas/              # Pydantic v2 — Base/Create/Update/Response
│   │   ├── services/
│   │   └── ws/handler.py         # WebSocket /ws/lists/{id}
│   ├── alembic/
│   │   └── versions/
│   │       └── 0001_initial_schema.py
│   ├── tests/
│   │   ├── conftest.py           # PostgreSQL real, mocks Supabase
│   │   ├── unit/
│   │   │   ├── test_auth_schemas.py
│   │   │   └── test_schemas.py
│   │   └── integration/
│   │       └── test_auth_endpoints.py
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   └── alembic.ini
├── .github/
│   └── workflows/
│       ├── ci.yml                # PostgreSQL service integrat
│       └── deploy-staging.yml
├── .cursor/
│   └── rules                    # context complet per a Cursor Agent
└── ARCHITECTURE.md

```

---

## 2. Seguretat

### Autenticació — Supabase Auth (decisió tancada)

**Per què Supabase Auth:**
- Gratuït fins 50.000 usuaris actius/mes
- PostgreSQL integrat — els usuaris viuen a la mateixa BD
- SDK oficial per a Next.js, FastAPI i Capacitor
- Exportació de dades possible si cal migrar

**Flux de tokens:**
```
Login → Supabase retorna access_token (15min) + refresh_token (7 dies)
Cada petició API → Authorization: Bearer {access_token}
Si 401 → supabase.auth.refreshSession() → nou access_token
Si refresh caducat → logout i redirecció a /login
```

**Emmagatzematge:**
- Web: HttpOnly cookies via `@supabase/ssr` — **mai localStorage**
- Capacitor: Keychain (iOS) / Keystore (Android)

**Regla crítica de seguretat al servidor:**
```typescript
// MAI usar al servidor:
const { data: { session } } = await supabase.auth.getSession()

// SEMPRE usar al servidor:
const { data: { user } } = await supabase.auth.getUser()
```
`getSession()` llegeix de la cookie sense verificar amb Supabase — és insegur.
`getUser()` sempre valida el token amb el servidor de Supabase.

### Variables d'entorn

**Backend (`backend/.env` — mai al repositori):**
```
DATABASE_URL=postgresql+asyncpg://...
SECRET_KEY=                          # mínim 32 chars aleatoris
REFRESH_SECRET_KEY=                  # diferent del SECRET_KEY
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...             # clau pública
SUPABASE_SERVICE_KEY=eyJ...          # clau privada — DIFERENT de l'anon key
ALLOWED_ORIGINS=["http://localhost:3000","capacitor://localhost"]
ENVIRONMENT=development
SENTRY_DSN=
```

**⚠️ Error comú:** `SUPABASE_SERVICE_KEY` i `SUPABASE_ANON_KEY` han de ser
valors DIFERENTS. La `service_role` key és la llarga marcada com a "secret"
a Project Settings → API del dashboard de Supabase.

**Frontend (`web/.env.local` — mai al repositori):**
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...   # la mateixa anon key, és pública
```

### Headers HTTP de seguretat
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy:   default-src 'self'; ...
X-Frame-Options:           DENY
X-Content-Type-Options:    nosniff
Permissions-Policy:        camera=(), microphone=()
Referrer-Policy:           strict-origin-when-cross-origin
```

### CORS
```python
# backend/app/core/config.py
ALLOWED_ORIGINS: list[str]  # llegit des de .env

# backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # MAI ["*"]
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)
```

### Rate limiting (SlowAPI)
```
/api/v1/auth/*  → 5 peticions/minut per IP
Default         → 100 peticions/minut per IP
```

---

## 3. Backend

### API — convencions
- Tots els endpoints: `/api/v1/`
- IDs: sempre UUID, mai integers seqüencials
- Timestamps: UTC, format ISO 8601
- Error estàndard: `{"detail": "missatge", "code": "ERROR_CODE"}`
- Paginació: `{"items": [], "total": 0, "page": 1, "per_page": 20}`

### Endpoints implementats (Sprint 1)
```
POST  /api/v1/auth/register
POST  /api/v1/auth/login
POST  /api/v1/auth/logout
POST  /api/v1/auth/refresh
GET   /api/v1/auth/me
GET   /api/v1/users/me
PATCH /api/v1/users/me
```

### Endpoints implementats (Sprint 2)
```
GET    /api/v1/lists/
POST   /api/v1/lists/
GET    /api/v1/lists/{id}
PATCH  /api/v1/lists/{id}
DELETE /api/v1/lists/{id}
GET    /api/v1/lists/{id}/items
POST   /api/v1/lists/{id}/items
PATCH  /api/v1/lists/{id}/items/{item_id}
DELETE /api/v1/lists/{id}/items/{item_id}
```

### Endpoints pendents (stubs)
```
GET/DEL        /api/v1/lists/{id}/members
POST           /api/v1/lists/{id}/invite
GET/POST       /api/v1/invitations/{token}
WS             /ws/lists/{id}?token=JWT
```

### WebSockets — col·laboració en temps real
```
Canal: /ws/lists/{list_id}?token={jwt}
Auth: JWT validat al handshake — tanca amb 1008 si invàlid
Broadcast: a tots els membres connectats excepte l'emissor
Format: {"type": "item_updated", "payload": {...}, "user_id": "..."}
Reconnexió client: backoff 1s→2s→4s→8s→30s màxim
```

### Migracions Alembic
```bash
# Crear migració
alembic revision --autogenerate -m "descripcio_clara"

# Aplicar
alembic upgrade head

# Rollback
alembic downgrade -1

# Estat
alembic current
```

**Regles:**
- Cada PR que modifica models inclou la migració corresponent
- `downgrade()` sempre implementat
- Mai modificar una migració ja aplicada — crear-ne una de nova
- Validar al CI: `alembic upgrade head` abans dels tests

---

## 4. Frontend

### Estratègia de rendering per ruta

| Ruta | Mètode | Raó |
|---|---|---|
| `/login`, `/register` | SSG `force-static` | No necessiten dades de servidor |
| `/home`, `/lists`, `/lists/[id]` | SSR `force-dynamic` | Requereixen sessió verificada |
| `/onboarding` | SSG | Flux d'entrada sense dades |

### Middleware de protecció de rutes
```typescript
// Rutes públiques: /login, /register, /onboarding, /invitations/*
// Tota la resta: requereix sessió via getUser() de Supabase SSR
// Si no hi ha sessió → redirect('/login')
// Si hi ha sessió i intenta accedir a /login → redirect('/home')
```

### Gestió de l'estat offline
```
Usuari edita sense connexió
  → Canvi aplicat immediatament (optimistic UI)
  → Guardat a cua IndexedDB
  → Banner "Sense connexió — els canvis es guardaran"

Connexió restaurada (@capacitor/network)
  → Cua processada FIFO
  → Conflictes: last-write-wins (MVP)
  → Banner "Sincronitzat"
```

### Core Web Vitals objectius
| Mètrica | Objectiu |
|---|---|
| LCP | < 2.5s |
| CLS | < 0.1 |
| INP | < 200ms |
| TTFB | < 800ms |

### Estructura de fitxers (Sprint 2)

- `web/lib/types.ts` — tots els tipus TypeScript que reflecteixen els schemas del backend
- `web/lib/api/lists.ts` + `web/lib/api/list-items.ts` — helpers d'API tipats
- `web/app/providers.tsx` — QueryClientProvider (TanStack Query)
- `web/app/(app)/lists/page.tsx` — pàgina de llistes amb TanStack Query
- `web/app/(app)/lists/[id]/page.tsx` — detall de llista, `force-dynamic`
- `web/app/(app)/home/page.tsx` — vista intel·ligent (due_date + priority)
- `web/components/lists/ListCard.tsx` — card de llista
- `web/components/lists/NewListModal.tsx` — modal de creació
- `web/components/items/ItemRow.tsx` — fila d'ítem amb checkbox

---

## 5. Tests

### Estratègia general
- **No testar implementació interna** — testar comportament observable
- **Mocks:** Supabase sempre mockejar als tests; BD de test real (PostgreSQL)

### Patró de fixtures async (CRÍTIC — no canviar sense revisar)

El patró correcte per a tests async amb FastAPI + asyncpg + pytest-asyncio és:

- `test_engine` — `scope="session"`, NullPool, **sense** `drop_all`/`dispose()` al teardown
- `db_session` — `scope="function"`, creat manualment amb `session = async_session()` **sense** `async with`
- Els helpers de test que insereixen dades **HAN D'USAR `engine.begin()` directament**, MAI `db_session`
- `autobegin=False` **NO** s'ha d'usar — trenca els helpers i causa `InvalidRequestError`

```python
# conftest.py — patró correcte
@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with engine.begin() as conn:
        await conn.execute(text("INSERT INTO users ... ON CONFLICT DO NOTHING"))
    yield engine
    # NO drop_all ni dispose() al teardown — causa bloqueig al CI

@pytest_asyncio.fixture
async def db_session(test_engine):
    async_session = async_sessionmaker(
        test_engine, expire_on_commit=False, class_=AsyncSession
    )
    session = async_session()  # NO async with — causa 'different loop' errors
    yield session

# Helper de test — patró correcte
async def _setup_list(engine: AsyncEngine, ...) -> uuid.UUID:
    async with engine.begin() as conn:  # engine.begin(), NO db_session
        await conn.execute(text("INSERT INTO users ... ON CONFLICT DO NOTHING"))
        await conn.execute(text("INSERT INTO lists ..."), {...})
    return list_id
```

### Seed de dades de test

Els usuaris de test s'insereixen al fixture `test_engine` via `engine.begin()`:
- `MOCK_USER_ID = 550e8400-e29b-41d4-a716-446655440000`
- `OTHER_USER_ID = 650e8400-e29b-41d4-a716-446655440001`

`ON CONFLICT DO NOTHING` fa que sigui idempotent.

### BD de test

**BD de test:** PostgreSQL real via GitHub Actions service (no SQLite)
- Al CI: BD efímera arrencat per GitHub Actions
- En local: BD de test separada de la de desenvolupament

```
# BD de test local
DATABASE_URL=postgresql+asyncpg://test_user:test_password@localhost:5432/test_db

# Crear la BD de test local (una sola vegada)
psql -U postgres -c "CREATE USER test_user WITH PASSWORD 'test_password';"
psql -U postgres -c "CREATE DATABASE test_db OWNER test_user;"
```

**Per què PostgreSQL i no SQLite:**
- SQLite no suporta `UUID` natiu, `JSONB`, arrays de PostgreSQL
- Les incompatibilitats entre SQLite i PostgreSQL amaguen errors reals
- GitHub Actions ofereix serveis PostgreSQL gratuïts — zero cost addicional
- Paritat total entre tests i producció

### Cobertura

El llindar de cobertura es configura al `ci.yml` (no al `pytest.ini`):
```yaml
run: pytest tests/ -v --cov=app --cov-report=term-missing --cov-fail-under=82
```

Objectiu a llarg termini: 90%+. Llindar actual: 82% (pendent millorar al Sprint 3).

### Dependències de versió crítiques

| Paquet | Versió | Motiu |
|--------|--------|-------|
| fastapi | 0.116.* | 0.115 limita starlette <0.47 |
| starlette | 0.47.2 | màxim compatible amb fastapi 0.116 |
| pytest | 8.* | pytest-asyncio 0.24 no suporta pytest 9 |
| pytest-asyncio | 0.24.* | única versió compatible amb pytest 8 |
| python-jose | 3.4.0 | fix PYSEC-2024-232/233 |

CVEs ignorats al pip-audit (incompatibilitat de dependències):
- CVE-2025-71176 (pytest) — pytest-asyncio no suporta pytest 9 encara
- CVE-2025-54121, CVE-2025-62727 (starlette) — fastapi 0.116 limita starlette <0.48

### Frontend — configuració de tests

**jest.config.js** (ha de ser `.js`, no `.ts` — evita dependència de `ts-node`):
```javascript
module.exports = {
  testEnvironment: 'jsdom',
  transform: {
    '^.+\\.(ts|tsx|js|jsx)$': ['babel-jest', { presets: ['next/babel'] }],
  },
  moduleNameMapper: { '^@/(.*)$': '<rootDir>/$1' },
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],  // AfterEnv no AfterFramework
  testMatch: ['<rootDir>/tests/**/*.test.{ts,tsx}'],
}
```

---

## 6. CI/CD

### Pipeline complet (`ci.yml`)

```yaml
# Job backend: arrenca servei PostgreSQL 16, aplica migracions, executa tests
# Job frontend: instal·la deps, lint, tests, build, audit
# Tots dos en paral·lel — la PR no es pot fer merge fins que tots dos passen
```

**Variables d'entorn al CI (GitHub Actions Secrets):**
- `DATABASE_URL` — no cal, el CI usa el servei PostgreSQL local
- Els secrets de Supabase s'han de configurar a GitHub → Settings → Secrets

### Flux de branques
```
feature/nom  →  PR a develop  →  CI verd  →  merge
develop      →  PR a main     →  CI verd + 1 aprovació  →  merge  →  deploy staging
```

### pip-audit

El step de pip-audit ha d'usar `&&` en una sola línia, **NO** bloc `|` multiline:

```yaml
# CORRECTE
run: pip install pip-audit && pip-audit -r requirements.txt --ignore-vuln CVE-XXX --ignore-vuln PYSEC-XXX

# INCORRECTE — el bloc | interpreta les dues comandes per separat i pip-audit
# pot no trobar les dependències instal·lades al pas anterior
run: |
  pip install pip-audit
  pip-audit -r requirements.txt --ignore-vuln CVE-XXX
```

### Comandes útils Windows (PowerShell)
```powershell
# Recarregar PATH (necessari cada cop que gh CLI no es troba)
$env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")

# Crear PR
gh pr create --base develop --title "feat(x): ..." --body "..."

# Veure estat del CI
gh pr checks

# Obrir PR al navegador
gh pr view --web
```

---

## 7. Model de dades

### Taules i camps

```sql
users
  id            uuid PK DEFAULT gen_random_uuid()
  email         text UNIQUE NOT NULL
  display_name  text
  avatar_url    text
  created_at    timestamptz DEFAULT now()
  last_seen_at  timestamptz

list_types
  id            uuid PK
  slug          text UNIQUE          -- 'todo', 'shopping', 'books'...
  label         text
  icon          text
  is_active     boolean DEFAULT true

lists
  id            uuid PK
  owner_id      uuid FK → users
  list_type_id  uuid FK → list_types
  title         text NOT NULL
  description   text
  is_archived   boolean DEFAULT false
  created_at    timestamptz DEFAULT now()
  updated_at    timestamptz

list_members
  id            uuid PK
  list_id       uuid FK → lists
  user_id       uuid FK → users
  role          text CHECK (role IN ('owner','editor','viewer'))
  joined_at     timestamptz DEFAULT now()
  UNIQUE (list_id, user_id)

list_items
  id            uuid PK
  list_id       uuid FK → lists
  created_by    uuid FK → users
  content       text NOT NULL
  is_checked    boolean DEFAULT false
  position      integer
  due_date      date
  priority      text CHECK (priority IN ('high','medium','low'))
  remind_at     timestamptz
  metadata      jsonb
  created_at    timestamptz DEFAULT now()
  updated_at    timestamptz

list_invitations
  id            uuid PK
  list_id       uuid FK → lists
  invited_by    uuid FK → users
  email         text NOT NULL
  token         text UNIQUE
  status        text CHECK (status IN ('pending','accepted','expired'))
  expires_at    timestamptz

activity_log
  id            uuid PK
  list_id       uuid FK → lists
  user_id       uuid FK → users
  action        text        -- 'item_added', 'item_checked', 'member_joined'
  payload       jsonb
  created_at    timestamptz DEFAULT now()

device_tokens
  id            uuid PK
  user_id       uuid FK → users
  token         text NOT NULL
  platform      text CHECK (platform IN ('ios','android','web'))
  created_at    timestamptz DEFAULT now()
```

### Roadmap de tipus de llista

| Slug | Label | Camps `metadata` | Sprint |
|---|---|---|---|
| `todo` | Tasques | `due_date`, `priority` | MVP ✓ |
| `shopping` | Compra | `quantity`, `unit`, `category` | v1.1 |
| `wishlist` | Productes | `url`, `price`, `store` | v1.1 |
| `books` | Llibres | `author`, `isbn` | v1.2 |
| `movies` | Pel·lícules | `year`, `director`, `platform` | v1.2 |
| `places` | Viatges | `location`, `lat`, `lng` | v1.3 |

---

## 8. UX i navegació

### Estructura de pantalles
```
[/login] o [/register]
  ↓ (primer login)
[/onboarding] — 3 passos, saltable
  ↓
[/home] — vista intel·ligent agrupada per llista, ordenada per due_date + priority
  ↓ (toca una llista)
[/lists/{id}] — detall complet, col·laboració en temps real
```

### NavBar (top nav)
```
[Hamburger] [Títol pàgina] [Avatar + dropdown]
                                └── Perfil
                                └── Tancar sessió
```

### SideMenu (drawer)
```
Inici → /home
Llistes → /lists
Perfil → /profile
Configuració → /settings
─────────────
Tancar sessió
```

### Notificacions push
```
remind_at (timestamptz) a list_items
  → Backend scheduler (APScheduler) comprova cada minut
  → Envia push via Supabase Edge Functions o endpoint propi
  → Client registra token via @capacitor/push-notifications
  → Guardat a device_tokens

Nova taula: device_tokens (user_id, token, platform)
```

---

## 9. Lliçons apreses

Documentades per evitar repetir els mateixos errors en sprints futurs.

### Sprint 1 — Backend
1. **`dependency_overrides` de FastAPI no funcionen si la connexió a la BD es fa en import-time.** El motor `asyncpg` intenta connectar en el moment que es crea l'engine, no quan s'executa una query. La solució és usar una BD de test real (PostgreSQL via GitHub Actions) en lloc de SQLite o mocks.

2. **`ruff` F401 falla si `import pytest` apareix però `pytest` no s'usa directament.** Eliminar l'import o usar `pytest.mark.asyncio` explícitament al fitxer.

3. **`SUPABASE_SERVICE_KEY` i `SUPABASE_ANON_KEY` han de ser claus DIFERENTS.** Si el `logout` o el `get_user` falla misteriosament, verificar que no s'ha posat la mateixa clau als dos camps.

### Sprint 1 — Frontend
4. **`jest.config` ha de ser `.js`, no `.ts`.** El fitxer `.ts` requereix `ts-node` que no sempre és disponible al CI. Convertir a CommonJS resol el problema sense dependències addicionals.

5. **El camp és `setupFilesAfterEnv`, no `setupFilesAfterFramework`.** El typo fa que Jest ignori el fitxer de setup silenciosament — 0 tests executats sense cap error obvi.

6. **`next/babel` preset ja inclou TypeScript i JSX** — no cal instal·lar `@babel/preset-typescript` per separat.

### Sprint 1 — CI/CD i Git
7. **Protecció de branques a GitHub requereix pla de pagament per a repositoris privats.** Solució: fer el repositori públic (el codi no conté secrets) o pagar GitHub Pro.

8. **El PATH de `gh` CLI es perd entre sessions de PowerShell.** Sempre recarregar amb `$env:PATH = [System.Environment]::GetEnvironmentVariable(...)` abans d'usar `gh`.

9. **Les comandes multilínia amb el backtick de PowerShell fallen si hi ha text al mateix cursor.** Executar cada línia per separat o usar un fitxer `.ps1`.

### Sprint 2 — Tests async
10. **Els helpers de test que usen `db_session` per inserir dades causen errors de loop i d'estat de sessió.** `db_session` és function-scoped i els commits explícits deixen la sessió en un estat incompatible amb el teardown. Solució: usar sempre `engine.begin()` + SQL raw als helpers.

11. **`drop_all` i `dispose()` al teardown del fixture `test_engine` bloquegen el CI indefinidament** (30+ minuts observats). El teardown ha de ser buit — la BD efímera de GitHub Actions s'elimina sola en acabar el job.

12. **`autobegin=False` a `async_sessionmaker` causa `InvalidRequestError`** als helpers que fan `conn.execute()` directament. No usar mai aquesta opció.

13. **`async with async_session()` en lloc de `session = async_session()` causa errors de "different event loop"** als tests de llarga durada. El fixture `db_session` ha de crear la sessió sense context manager.

### Sprint 2 — CI/CD
14. **El step de pip-audit ha d'usar `&&` en una sola línia.** El bloc `|` multiline de YAML fa que pip-audit s'executi en un entorn on les dependències del pas anterior (`pip install pip-audit`) poden no estar disponibles correctament. Usar sempre la forma `pip install pip-audit && pip-audit ...` en una sola instrucció `run:`.

---

## 10. Estat actual del projecte

### ✅ Sprint 1 — Auth (completat)
- [x] Estructura base backend + frontend
- [x] Migracions Alembic (8 taules)
- [x] Endpoints d'auth (register, login, logout, refresh, me)
- [x] Middleware de protecció de rutes (Next.js)
- [x] Stores Zustand (auth, offline)
- [x] NavBar i SideMenu
- [x] Onboarding 3 passos
- [x] CI en verd (PostgreSQL service + Jest)
- [x] Merge a develop

### ✅ Sprint 2 — CRUD de llistes i ítems (completat)
- [x] Endpoints de llistes: GET, POST, GET/{id}, PATCH/{id}, DELETE/{id}
- [x] Endpoints d'ítems: GET, POST, PATCH/{item_id}, DELETE/{item_id}
- [x] `require_list_role("editor"|"owner")` — control d'accés per rol
- [x] Frontend: ListCard, NewListModal, ItemRow amb TanStack Query
- [x] Pàgines: `/lists`, `/lists/[id]`, `/home` (vista intel·ligent)
- [x] Tests d'integració amb `engine.begin()` (patró definitiu)
- [x] Cobertura de tests ≥ 82% (llindar CI)
- [x] Merge a develop

### Sprint 3 — Col·laboració WebSockets (pendent)
### Sprint 4 — Offline i push notifications (pendent)

---

*Última actualització: post Sprint 2*
*Repositori: https://github.com/NackerWD/my-lists-app*
