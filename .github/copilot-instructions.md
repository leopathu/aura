# GitHub Copilot Instructions — Aura RAG System

## Project Overview

Aura is a Retrieval-Augmented Generation (RAG) system consisting of:

- **Backend**: FastAPI (Python)
- **Frontend**: Next.js (TypeScript)
- **Database**: PostgreSQL with pgvector extension for vector storage

---

## Repository Structure

```
aura/
├── backend/                  # FastAPI application
│   ├── app/
│   │   ├── api/              # Route handlers (versioned: /api/v1/...)
│   │   ├── core/             # Config, settings, security
│   │   ├── db/               # Database session, base models
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # Business logic (RAG pipeline, embeddings, etc.)
│   │   ├── repositories/     # DB query layer (repository pattern)
│   │   └── main.py           # FastAPI app entry point
│   ├── tests/
│   ├── alembic/              # Database migrations
│   ├── pyproject.toml
│   └── .env
├── frontend/                 # Next.js application
│   ├── src/
│   │   ├── app/              # App Router pages and layouts
│   │   ├── components/       # Reusable UI components
│   │   ├── hooks/            # Custom React hooks
│   │   ├── lib/              # Utilities, API clients, helpers
│   │   ├── services/         # API service layer (calls to FastAPI)
│   │   ├── store/            # Global state (Zustand / React Context)
│   │   └── types/            # TypeScript type definitions
│   ├── public/
│   ├── package.json
│   └── .env.local
└── docker-compose.yml
```

---

## Backend — FastAPI Standards

### General

- Use **Python 3.11+** with full type annotations on all functions and classes.
- Use **`async`/`await`** for all I/O-bound operations (DB queries, HTTP calls, file reads).
- Never use synchronous blocking calls inside async route handlers.
- Group routes using `APIRouter`; never define routes directly on the `app` instance except for health checks.
- Version all API routes under `/api/v1/`.

### Project Layout Rules

- `api/` — only route definitions and dependency injection; no business logic.
- `services/` — all business logic, RAG pipeline steps, LLM calls, embedding generation.
- `repositories/` — all raw database queries using SQLAlchemy; no logic beyond querying.
- `schemas/` — Pydantic v2 models for request validation and response serialization.
- `models/` — SQLAlchemy ORM models; keep them free of business logic.

### Pydantic & Schemas

- Use **Pydantic v2** (`model_config = ConfigDict(...)`).
- Always define separate `CreateSchema`, `UpdateSchema`, and `ResponseSchema` per resource.
- Use `model_validator` and `field_validator` over `@validator` (Pydantic v1 style).
- Never expose ORM model instances directly in responses; always serialize via a schema.

### SQLAlchemy & Database

- Use **SQLAlchemy 2.0** async style (`async_sessionmaker`, `AsyncSession`).
- Define a `Base` declarative base in `db/base.py`; all models inherit from it.
- Every model must have: `id` (UUID primary key), `created_at`, `updated_at` (auto-managed).
- Use **Alembic** for all schema migrations; never mutate the database schema manually.
- Always use dependency injection for DB sessions (`Depends(get_db)`).

### pgvector

- Store embeddings in a dedicated `embeddings` table using the `Vector` column type from `pgvector.sqlalchemy`.
- Always specify the vector dimension explicitly (e.g., `Vector(1536)`).
- Use `HNSW` or `IVFFlat` indexes for similarity search; add index creation in Alembic migrations.
- Similarity search queries must be performed in the repository layer.
- Never store raw embedding arrays in application memory longer than necessary.

### RAG Pipeline

- Implement the RAG pipeline as a service in `services/rag_service.py`.
- Separate concerns clearly:
  1. **Ingestion**: chunking → embedding → storing in pgvector.
  2. **Retrieval**: embed query → vector similarity search → fetch top-k chunks.
  3. **Generation**: build prompt with context → call LLM → return response.
- Use a consistent chunking strategy (chunk size + overlap) defined in `core/config.py`.
- All LLM and embedding API calls must be wrapped in try/except with proper error handling.

### Configuration

- Use `pydantic-settings` with a `Settings` class in `core/config.py`.
- Load all secrets from environment variables; never hardcode credentials.
- Provide a `.env.example` at the project root.

### Error Handling

- Use custom exception classes in `core/exceptions.py`.
- Register global exception handlers in `main.py`.
- Always return structured JSON errors: `{ "detail": "...", "code": "..." }`.
- Use appropriate HTTP status codes (422 for validation, 404 for not found, 500 for server errors).

### Testing

- Use **pytest** with `pytest-asyncio` for async tests.
- Mock all external API calls (LLM, embeddings) in unit tests.
- Aim for ≥80% coverage on `services/` and `repositories/`.
- Use a separate test database; never run tests against the production database.

### Code Style

- Follow **PEP 8**; enforce with `ruff` and `black`.
- Max line length: **100 characters**.
- All public functions and classes must have docstrings.
- Use meaningful variable names; avoid single-letter names outside of list comprehensions.

---

## Frontend — Next.js Standards

### General

- Use **Next.js 14+** with the **App Router** exclusively; do not use `pages/` directory.
- Use **TypeScript** with `strict` mode enabled in `tsconfig.json`.
- Never use `any` type; prefer `unknown` and narrow types properly.
- All components must be typed; avoid implicit prop types.

### Component Standards

- **Default to Server Components**; add `"use client"` only when browser APIs or React hooks are required.
- Use **named exports** for all components; avoid default exports except for page files (Next.js convention).
- Component filenames must use **PascalCase** (e.g., `ChatMessage.tsx`).
- Keep components focused and small; extract logic into custom hooks.
- Co-locate component-specific styles, types, and sub-components in the same directory.

### File & Folder Conventions

- `app/` — pages, layouts, and loading/error boundaries only; no business logic.
- `components/` — purely presentational or shared UI components.
- `hooks/` — custom hooks prefixed with `use` (e.g., `useChat.ts`).
- `services/` — all FastAPI HTTP calls using `fetch` or Axios with typed responses.
- `types/` — shared TypeScript interfaces and type aliases.
- `lib/` — pure utility functions; no React dependencies.

### Data Fetching

- Fetch data in **Server Components** using `async/await` wherever possible.
- Use **React Query (`@tanstack/react-query`)** for client-side data fetching, caching, and mutation.
- Always handle loading, error, and empty states explicitly.
- Type all API responses using interfaces defined in `types/`.

### API Service Layer

- All calls to the FastAPI backend must go through `services/api.ts` (or per-feature service files).
- Use a typed API client; never use raw `fetch` in components directly.
- Always handle HTTP errors and surface them as typed error objects.
- Use `NEXT_PUBLIC_API_URL` env variable for the backend base URL.

### State Management

- Use **React Context** for lightweight global state (e.g., auth, theme).
- Use **Zustand** for complex client-side state (e.g., chat history, document list).
- Avoid prop drilling beyond two levels; lift state or use a store.

### Styling

- Use **Tailwind CSS** for styling; avoid inline styles except for dynamic values.
- Use `cn()` utility (from `clsx` + `tailwind-merge`) for conditional class merging.
- Follow a consistent color palette and spacing scale defined in `tailwind.config.ts`.

### TypeScript Strictness

- Enable `strict`, `noUncheckedIndexedAccess`, and `exactOptionalPropertyTypes` in `tsconfig.json`.
- Never use type assertions (`as`) without a comment explaining why it is safe.
- Prefer `interface` for object shapes; use `type` for unions, intersections, and aliases.

### Testing

- Use **Vitest** + **React Testing Library** for unit and component tests.
- Test user interactions, not implementation details.
- Mock all API service calls in component tests.

### Code Style

- Enforce with **ESLint** (`eslint-config-next`) and **Prettier**.
- Max line length: **100 characters**.
- Use `const` by default; use `let` only when reassignment is necessary.
- Prefer arrow functions for components and callbacks.
- Avoid `console.log` in production code; use a proper logger or remove before committing.

---

## Database — PostgreSQL & pgvector

- Use **PostgreSQL 16+**.
- Enable the `pgvector` extension via migration: `CREATE EXTENSION IF NOT EXISTS vector;`.
- All tables must use **UUID** primary keys (`gen_random_uuid()`).
- Use **snake_case** for all table and column names.
- Define foreign key constraints explicitly; never rely on application-level integrity alone.
- Add appropriate indexes for frequently queried columns.
- Vector columns must declare their dimension; mismatched dimensions must raise a migration error.
- Store document metadata (title, source, chunk index, etc.) alongside embedding references.

---

## Cross-Cutting Concerns

### Environment Variables

| Variable | Used By | Description |
|---|---|---|
| `DATABASE_URL` | Backend | PostgreSQL connection string |
| `OPENAI_API_KEY` | Backend | LLM / Embedding API key |
| `EMBEDDING_MODEL` | Backend | Model name for embeddings |
| `LLM_MODEL` | Backend | Model name for generation |
| `VECTOR_DIMENSIONS` | Backend | Embedding vector size |
| `NEXT_PUBLIC_API_URL` | Frontend | FastAPI base URL |

### Security

- Never commit `.env` files; always commit `.env.example`.
- Sanitize and validate all user inputs on the backend (Pydantic handles this).
- Use parameterized queries only; never concatenate raw SQL strings.
- Implement rate limiting on the `/api/v1/query` endpoint.
- Use CORS middleware in FastAPI restricted to known frontend origins.

### Git Conventions

- Branch naming: `feature/`, `fix/`, `chore/`, `docs/` prefixes.
- Commit messages: follow **Conventional Commits** (`feat:`, `fix:`, `chore:`, etc.).
- Never commit directly to `main`; use pull requests.
- Each PR should be focused on a single concern.

### Docker

- Provide a `docker-compose.yml` with services: `backend`, `frontend`, `db`.
- The `db` service must include the `pgvector/pgvector` image (not plain `postgres`).
- Use named volumes for PostgreSQL data persistence.
- Backend must wait for DB to be healthy before starting (`depends_on` with `healthcheck`).
