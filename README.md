# Aura — Open-Source Agentic Data & Knowledge Platform

> **Connect your organization's data once → define access policies → let users ask questions or request work in natural language → agents securely use permitted data/tools → return verified answers, reports, and citations.**

---

## 1. Product Architecture

Aura is built on the fundamental principle that **the LLM should never receive unrestricted credentials to your organization's systems**. The LLM asks the platform to perform an operation; the platform evaluates whether that operation is allowed before executing it.

```text
                         ┌───────────────────────────┐
                         │       Next.js UI          │
                         │                           │
                         │  Chat │ Admin │ Sources   │
                         │  Users │ Roles │ Reports  │
                         └─────────────┬─────────────┘
                                       │
                                  REST / SSE
                                       │
                         ┌─────────────▼─────────────┐
                         │       FastAPI API         │
                         │                           │
                         │ Auth / Org / RBAC         │
                         │ Chat / Conversations      │
                         │ Sources / Documents       │
                         │ Agent API / Reports       │
                         └─────────────┬─────────────┘
                                       │
                   ┌───────────────────┼───────────────────┐
                   │                   │                   │
          ┌────────▼────────┐ ┌────────▼────────┐ ┌───────▼────────┐
          │ Policy Engine   │ │ Agent Runtime   │ │ Knowledge      │
          │                 │ │                 │ │ Engine         │
          │ RBAC            │ │ Planner         │ │ RAG            │
          │ Permissions     │ │ Tool Selection  │ │ Embeddings     │
          │ Data Policies   │ │ Execution       │ │ Retrieval      │
          │ Row / Column    │ │ Verification    │ │ Documents      │
          └────────┬────────┘ └────────┬────────┘ └───────┬────────┘
                   │                   │                  │
                   └───────────────────┼──────────────────┘
                                       │
                         ┌─────────────▼─────────────┐
                         │      Tool Gateway         │
                         │                           │
                         │ SQL │ RAG │ MCP │ Web     │
                         │ Search │ APIs │ Actions   │
                         └─────────────┬─────────────┘
                                       │
        ┌──────────────────────────────┼─────────────────────────────┐
        │              │               │             │               │
   ┌────▼────┐    ┌────▼────┐    ┌─────▼────┐  ┌────▼────┐    ┌─────▼─────┐
   │ SQLite  │    │Postgres │    │  MySQL   │  │ Files   │    │ MCP       │
   │ Embedded│    │pgvector │    │ Relational│ │ PDF/CSV │    │ Servers   │
   └─────────┘    └─────────┘    └──────────┘  └─────────┘    └───────────┘
```

---

## 2. Core Capabilities

1. **Ask**: "How much revenue did we generate last quarter?"
2. **Analyze**: "Compare this quarter with the previous quarter and show category trends."
3. **Retrieve**: "What does our company leave handbook say about annual leave?"
4. **Act**: "Analyze sales trends across categories and generate an executive report."

---

## 3. Technology Stack

- **Backend**: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 Async, Greenlet, SQLite / PostgreSQL (pgvector), SQLGlot AST parser, Cryptography (Fernet symmetric encryption), PyPDF, Python-Docx, OpenPyXL.
- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS, Lucide Icons, Zustand.
- **Protocol**: REST + SSE (Server-Sent Events) for real-time agent execution streaming.
- **Infrastructure**: Docker Compose (API, Frontend, Worker, PostgreSQL + pgvector, Redis, MinIO).

---

## 4. Security & Policy Engine

- **Strict AST Read-Only SQL**: SQL queries are parsed into AST via SQLGlot. `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, and transaction commands are strictly rejected.
- **Table & Column Permissions**: Explicit ALLOW/DENY lists for tables and columns per role.
- **Row-Level Filters**: Injects tenancy or organizational WHERE clauses into SQL queries automatically.
- **Data Masking**: Automatic masking for PII (e.g. `MASK_EMAIL` -> `jo***@domain.com`, `REDACT` -> `[REDACTED]`, `MASK_NUMERIC` -> `***`).
- **MCP Gatekeeper**: Discovered Model Context Protocol tools are blocked by default until approved by an administrator.
- **Immutable Audit Logging**: Every query, tool execution, login, and policy denial is recorded.

---

## 5. Quickstart

### Option A: Using Docker Compose

```bash
# Clone the repository
git clone https://github.com/leopathu/aura.git
cd aura

# Start all services
docker compose up -d
```

- **Frontend Chat & Console**: [http://localhost:3000](http://localhost:3000)
- **FastAPI Backend & Swagger**: [http://localhost:8000/docs](http://localhost:8000/docs)

### Option B: Local Standalone Development

#### 1. Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run the FastAPI server (auto-creates tables and seeds demo data)
uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000).

---

## 6. Pre-Seeded Demo Credentials

The platform automatically initializes a demonstration organization (`Acme Corporation`) with sample data:

| Role | Email | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Organization Admin** | `admin@acme.com` | `admin123` | Full access across all tools, sources, models, policies |
| **Analyst** | `analyst@acme.com` | `analyst123` | Query database, RAG search, generate reports |

### Seeded Demo Data Sources:
1. **Sales & Transactions DB (SQLite)**: Tables `customers`, `orders`, `employees` with sample revenue data.
2. **Employee Leave & Operations Handbook (Markdown)**: Sample document parsed, chunked, and embedded for instant RAG.
3. **Financial Security Policy**: Email masking rule on `email` and salary redaction rule on `salary`.

---

## 7. Running Tests

Run the full pytest test suite:

```bash
cd backend
PYTHONPATH=. pytest tests -v
```

All integration tests verify:
- Auth & JWT verification
- SQL AST safety validation (rejection of malicious/DML statements)
- Policy engine rules and data masking
- Schema discovery on connected databases
- End-to-end Agent Runtime execution graph & SSE streaming.

---

## 8. License

Apache 2.0 Open Source.
