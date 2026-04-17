# Cursor rules — App de llistes universals
# Llegeix aquest fitxer sencer abans de generar qualsevol codi.

## Descripció del projecte
Aplicació B2C de llistes universals (tasques, compra, viatges, llibres, pel·lícules, etc.).
Llistes col·laboratives editables en temps real per múltiples usuaris simultàniament.
MVP: un sol tipus de llista (todo) per validar el flux complet de seguretat i escalabilitat.

## Stack tecnològic
- Frontend:    Next.js 14+ App Router, TypeScript strict, Tailwind CSS
- Backend:     FastAPI (Python 3.12+), SQLAlchemy async, Pydantic v2
- BD:          PostgreSQL 16+ amb Alembic per a migracions
- Auth:        Supabase Auth (JWT access 15min + refresh 7 dies amb rotació)
- Temps real:  WebSockets natius de FastAPI per col·laboració simultània
- Mòbil:       Capacitor 6+ (Android final, iOS post-MVP)
- Android proves: TWA via Bubblewrap
- Cloud:       Vercel (web) + Railway (backend + BD)
- Monitoratge: Sentry (sense PII en els events)

## Estructura del monorepo
```
/web        → Next.js (App Router)
/mobile     → Capacitor (Android + iOS)
/backend    → FastAPI
/.github    → CI/CD pipelines
/.cursor    → aquest fitxer
```

## Regles de seguretat — NO NEGOCIABLES
- Mai emmagatzemar tokens a localStorage. Sempre HttpOnly cookies (web) o Keychain/Keystore (Capacitor).
- Mai secrets, API keys o credencials al codi. Sempre process.env / os.environ.
- CORS: mai allow_origins=["*"]. Llista blanca explícita a core/config.py.
- Tots els endpoints de l'API requereixen autenticació excepte els marcats explícitament com a públics.
- Rate limiting a tots els endpoints d'autenticació (SlowAPI): 5 peticions/minut per IP.
- Headers HTTP de seguretat obligatoris: CSP, HSTS, X-Frame-Options, Permissions-Policy.
- Cap PII (emails, noms) als logs ni als payloads de Sentry.
- Contrasenyes: mínim 12 caràcters, validat tant al frontend com al backend.

## Regles de codi — TypeScript / Frontend
- TypeScript strict mode sempre. Cap `any` sense comentari justificatiu.
- Noms de variables, funcions i fitxers en anglès. Comentaris en català si cal.
- Cada component a la seva carpeta: ComponentName/index.tsx + ComponentName.test.tsx
- Estat del servidor: TanStack Query. Estat UI global: Zustand.
- Cada operació d'escriptura ha de passar pel gestor de cua offline (lib/offline/queue.ts) abans de cridar l'API.
- Optimistic UI per defecte: aplica el canvi localment, sincronitza en segon pla.
- No fer fetch directament des de components. Sempre a través de lib/api/client.ts.
- Mai usar getSession() al servidor — sempre getUser() per seguretat.

## Regles de codi — Python / Backend
- Type hints obligatoris a totes les funcions.
- Pydantic v2 per a tots els schemas d'entrada i sortida.
- SQLAlchemy async (AsyncSession) per a totes les consultes.
- Cada endpoint ha de tenir el seu test d'integració corresponent.
- Mai modificar una migració Alembic ja aplicada. Crear-ne una de nova.
- Estructura de resposta d'error estàndard: {"detail": "missatge", "code": "ERROR_CODE"}
- Estructura de paginació estàndard: {"items": [], "total": 0, "page": 1, "per_page": 20}

## API — convencions
- Tots els endpoints sota /api/v1/
- Mètodes HTTP semàntics: GET (lectura), POST (creació), PATCH (actualització parcial), DELETE
- IDs sempre com a UUID, mai com a integers seqüencials
- Timestamps sempre en UTC, format ISO 8601

## WebSockets — col·laboració en temps real
- Canal per llista: /ws/lists/{list_id}
- Autenticació: token JWT com a query param ?token= en la connexió inicial
- El client ha de gestionar reconnexió automàtica amb backoff exponencial (1s→2s→4s→8s→30s màx)
- Missatges en format JSON: {"type": "item_updated", "payload": {...}, "user_id": "..."}
- Tanca connexió amb codi 1008 si el JWT és invàlid

## Offline — cua de sincronització
- Tota operació d'escriptura s'ha d'encuar a IndexedDB si no hi ha connexió
- Detectar connexió via @capacitor/network
- Processar la cua en ordre FIFO quan es restaura la connexió
- Estratègia de conflictes al MVP: last-write-wins
- Mostrar banner discret "Sense connexió — els canvis es guardaran" quan offline

## Mòbil — Capacitor
- El codi web ha de funcionar dins WKWebView (iOS) i WebView (Android)
- Evitar APIs de navegador no suportades per Capacitor
- Plugins necessaris al MVP: @capacitor/network, @capacitor/push-notifications, @capacitor/preferences
- Digital Asset Links: /public/.well-known/assetlinks.json (obligatori per TWA Android)
- Bundle ID actual: com.placeholder.app (actualitzar quan es defineixi el nom)

## Tests — cobertura 90%+
- Tests unitaris per a tota la lògica de negoci (stores, utils, hooks, schemas)
- Tests d'integració per a tots els endpoints de l'API (mockejar Supabase, no cridar el servei real)
- Tests e2e (Playwright) per als fluxos principals: registre, crear llista, afegir ítem, convidar membre
- Cap merge a main sense CI verd i cobertura >= 90%

## Model de dades — taules principals
- users: id (UUID PK), email (UNIQUE), display_name, avatar_url, created_at, last_seen_at
- list_types: id, slug (UNIQUE), label, icon, is_active
- lists: id, owner_id FK, list_type_id FK, title, description, is_archived, created_at, updated_at
- list_members: id, list_id FK, user_id FK, role (owner|editor|viewer), joined_at — UNIQUE(list_id, user_id)
- list_items: id, list_id FK, created_by FK, content, is_checked, position, due_date, priority (high|medium|low), remind_at, metadata jsonb, created_at, updated_at
- list_invitations: id, list_id FK, invited_by FK, email, token (UNIQUE), status (pending|accepted|expired), expires_at
- activity_log: id, list_id FK, user_id FK, action, payload jsonb, created_at
- device_tokens: id, user_id FK, token, platform (ios|android|web), created_at

## Navegació UX
- Top nav + menú lateral (hamburger)
- Pantalla Home: vista intel·ligent agrupada per llista, ítems ordenats per due_date i priority
- Pantalla Llistes: totes les llistes de l'usuari (pròpies i compartides)
- Pantalla Detall: ítems de la llista amb col·laboració en temps real via WebSocket
- Onboarding: 2-3 passos per a usuari nou (saltable)
- Invitació: per correu electrònic (token) + per link compartible
- Offline: optimistic UI + cua local + banner d'estat de connexió

## Flux de branques Git
- main: producció — requereix PR + 1 aprovació + CI verd
- develop: integració — requereix PR + CI verd
- feature/*: una branca per funcionalitat, base sempre develop
- Mai push directe a main ni develop
