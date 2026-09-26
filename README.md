# Aura — Open-Source Agentic Data & Knowledge Platform

<p align="center">
  <strong>Connect your organization's data once &rarr; define access policies &rarr; create role-scoped Brains &rarr; let users ask questions and request work in natural language &rarr; agents securely query permitted data and return verified answers with citations and executive reports.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Next.js-14-black.svg?logo=next.js&logoColor=white" alt="Next.js" />
  <img src="https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue.svg?logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/TypeScript-5.4-blue.svg?logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/TailwindCSS-3.4-38B2AC.svg?logo=tailwind-css&logoColor=white" alt="Tailwind CSS" />
  <img src="https://img.shields.io/badge/License-Apache%202.0-green.svg" alt="License" />
</p>

---

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Key Features](#key-features)
  - [1. Knowledge & Data Brains](#1-knowledge--data-brains)
  - [2. Multi-Source Database Intelligence](#2-multi-source-database-intelligence)
  - [3. Multi-Format Document Ingestion & RAG](#3-multi-format-document-ingestion--rag)
  - [4. Autonomous Agent Runtime](#4-autonomous-agent-runtime)
  - [5. Policy Engine & SQL Safety Layer](#5-policy-engine--sql-safety-layer)
  - [6. Multi-Provider AI Model Gateway](#6-multi-provider-ai-model-gateway)
  - [7. MCP (Model Context Protocol) Extensibility](#7-mcp-model-context-protocol-extensibility)
  - [8. Role-Based Access Control (RBAC) & Multi-Tenancy](#8-role-based-access-control-rbac--multi-tenancy)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation & Quickstart](#installation--quickstart)
  - [Option A: Standalone Local Setup (Recommended for Development)](#option-a-standalone-local-setup-recommended-for-development)
  - [Option B: Docker Compose (Full Stack with Postgres & Redis)](#option-b-docker-compose-full-stack-with-postgres--redis)
- [Configuration & Environment Variables](#configuration--environment-variables)
- [Pre-Seeded Demo Accounts](#pre-seeded-demo-accounts)
- [Usage Walkthrough](#usage-walkthrough)
- [API Reference](#api-reference)
- [Running Tests](#running-tests)
- [Project Directory Structure](#project-directory-structure)
- [Security Considerations](#security-considerations)
- [License](#license)

---

## Overview

Aura is a secure, enterprise-ready, open-source platform that enables organizations to deploy autonomous AI agents against internal databases and documents without exposing raw database credentials, violating data governance rules, or risking accidental write/delete operations.

### The Security-First Principle

> **The LLM never directly receives database credentials or unrestricted execution access.**

Instead, the agent operates in an isolated environment where every tool invocation passes through:
1. **Brain Scoping**: The agent can only see and query resources assigned to the user's role.
2. **Policy Evaluation**: Queries are validated against SQL AST rules (strict read-only SELECT enforcement).
3. **Data Masking**: Sensitive fields (emails, phone numbers, salaries) are dynamically redacted or masked before reaching the model or user interface.
4. **Approval Gatekeeper**: MCP tools require explicit administrative approval before execution.

---

## System Architecture

```text
                           ┌─────────────────────────────────────────┐
                           │         Next.js 14 Web Console          │
                           │                                         │
                           │  • Chat & Agent Streaming (SSE)         │
                           │  • Brains Workspace (Data & Docs Tabs)  │
                           │  • Schema Inspector & Query Explorer    │
                           │  • Policy Engine & Masking Rules        │
                           │  • Roles, RBAC & Audit Traces           │
                           └────────────────────┬────────────────────┘
                                                │
                                      REST API / SSE Streams
                                                │
                           ┌────────────────────▼────────────────────┐
                           │          FastAPI Control Plane          │
                           │                                         │
                           │  • Multi-Tenant Auth (Bcrypt, JWT)      │
                           │  • Role-Based Access Control (23 Perms) │
                           │  • Brain Scoping & Access Calculation   │
                           │  • Background Document & Schema Workers │
                           └────────────────────┬────────────────────┘
                                                │
                  ┌─────────────────────────────┼─────────────────────────────┐
                  │                             │                             │
        ┌─────────▼─────────┐         ┌─────────▼─────────┐         ┌─────────▼─────────┐
        │   Policy Engine   │         │   Agent Runtime   │         │ Knowledge Engine  │
        │                   │         │                   │         │                   │
        │ • SQLGlot AST     │         │ • State Graph     │         │ • Multi-Format    │
        │ • Read-Only Check │◄───────►│ • Dynamic Planner │◄───────►│   Parsers (PDF,   │
        │ • Table/Col Allow │         │ • Tool Selection  │         │   DOCX, XLSX, CSV)│
        │ • Row Filters     │         │ • Execution Graph │         │ • Chunk Overlap   │
        │ • Data Masking    │         │ • Citation Engine │         │ • Vector Similarity│
        └─────────┬─────────┘         └─────────┬─────────┘         └─────────┬─────────┘
                  │                             │                             │
                  └─────────────────────────────┼─────────────────────────────┘
                                                │
                           ┌────────────────────▼────────────────────┐
                           │              Tool Gateway               │
                           │                                         │
                           │  • Database Query & Schema Inspector    │
                           │  • Document Semantic Search & RAG       │
                           │  • Executive Report Generator           │
                           │  • Web Search & External APIs           │
                           │  • MCP Gateway (Admin Approved Tools)   │
                           └────────────────────┬────────────────────┘
                                                │
       ┌───────────────────────┬────────────────┴───────────────┬───────────────────────┐
       │                       │                                │                       │
┌──────▼──────┐         ┌──────▼──────┐                  ┌──────▼──────┐         ┌──────▼──────┐
│ PostgreSQL  │         │    MySQL    │                  │   SQLite    │         │ Model Context│
│ (with vector│         │ (Relational │                  │ (Embedded / │         │ Protocol    │
│  retrieval) │         │  Databases) │                  │  In-Memory) │         │ (MCP Servers│
└─────────────┘         └─────────────┘                  └─────────────┘         └─────────────┘
```

---

## Key Features

### 1. Knowledge & Data Brains
Brains are isolated, domain-specific logical boundaries for enterprise data:
- **Centralized Management**: Each Brain groups relational databases and unstructured documents into a cohesive domain (e.g. *Finance & Revenue Brain*, *HR & Operations Brain*).
- **Dedicated Tabbed Workspace**: Direct access to connected databases, schema inspectors, file uploads, chunk previews, and role governance.
- **Strict Role Scoping**: Assign one or more organizational roles to a Brain. Users only see and query Brains permitted for their role.
- **Chat Scoping**: Chat sessions can target a specific Brain or query across all accessible Brains with automatic isolation.

### 2. Multi-Source Database Intelligence
- **Supported Connectors**: PostgreSQL (`asyncpg`), MySQL (`pymysql`), and SQLite (`aiosqlite`).
- **Zero Plaintext Credentials**: All database connection strings and credentials are symmetrically encrypted using Fernet cryptography (`cryptography`).
- **Automatic Schema Discovery**: Discovers tables, column names, data types, primary keys, and nullability flags in real-time.
- **Live Connection Testing**: Test database reachability directly from the Brain workspace.

### 3. Multi-Format Document Ingestion & RAG
- **Format Support**: PDF (`pypdf`), Microsoft Word DOCX (`python-docx`), Excel XLSX (`openpyxl`), CSV, Markdown (`.md`), and Plain Text (`.txt`).
- **Smart Chunking**: Text chunking with configurable window size (1000 characters) and overlap (200 characters) to preserve contextual boundaries.
- **Vector Retrieval**: Embeddings and cosine similarity search for pinpoint semantic document retrieval.
- **Verifiable Citations**: Every document-derived answer includes document title, chunk index, and preview snippets.

### 4. Autonomous Agent Runtime
- **Multi-Step Execution Graph**: The agent analyzes user intent, determines whether database queries, document searches, or calculations are required, and executes tools sequentially.
- **Real-Time SSE Streaming**: Stream step-by-step reasoning, tool execution status, SQL queries, and final markdown responses in real-time.
- **First-Class Reports**: Autonomous generation of structured executive summaries, findings tables, and recommendations exportable as Markdown artifacts.

### 5. Policy Engine & SQL Safety Layer
- **AST Parsing with SQLGlot**: Incoming SQL queries are parsed into Abstract Syntax Trees. Any statement other than a read-only `SELECT` (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `GRANT`, etc.) is immediately blocked with an audit alert.
- **Table & Column Permissions**: Explicit ALLOW/DENY lists on a per-role and per-source basis.
- **Row-Level Tenancy Filters**: Automatic injection of `WHERE` clauses (e.g., `WHERE tenant_id = '...'`) into queries.
- **Dynamic Data Masking**:
  - `MASK_EMAIL` &rarr; `j***@acme.com`
  - `REDACT` &rarr; `[REDACTED]`
  - `MASK_NUMERIC` &rarr; `***`

### 6. Multi-Provider AI Model Gateway
- **Supported Providers**:
  - **OpenAI Compatible**: OpenAI (GPT-4o, GPT-3.5-turbo), Azure OpenAI, Groq, Together AI, vLLM.
  - **Anthropic**: Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku.
  - **Ollama**: Local open-weights models (Llama 3, Mistral, Qwen, DeepSeek).
  - **Mock AI Provider**: Built-in intelligent fallback for testing and development with zero external API keys required.
- **Dynamic Configuration**: Configure and test API keys dynamically in the console without server restarts.

### 7. MCP (Model Context Protocol) Extensibility
- Connect standard Model Context Protocol servers over SSE or stdio.
- Automatic tool discovery and administrative approval workflows (tools are quarantined until explicitly enabled).

### 8. Role-Based Access Control (RBAC) & Multi-Tenancy
- 23 granular system permissions covering Brains, Data Sources, Documents, Policies, Models, MCP, Reports, and Users.
- Default roles: **Organization Admin**, **Data Admin**, **Analyst**, **User**, and **Viewer**, with support for custom role creation.
- Immutable audit logging tracking logins, queries, tool executions, and security violations.

---

## Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Lucide Icons, Zustand |
| **Backend API** | FastAPI, Pydantic v2, Python 3.11+, Uvicorn, Greenlet |
| **ORM & Database** | SQLAlchemy 2.0 Async, aiosqlite (default), asyncpg (PostgreSQL), pymysql (MySQL) |
| **Vector & RAG** | NumPy vector similarity, pgvector (production), pypdf, python-docx, openpyxl |
| **Security & AST** | SQLGlot (AST parsing), Cryptography (Fernet), Passlib (Bcrypt), Python-JOSE (JWT) |
| **Containerization**| Docker, Docker Compose |

---

## Prerequisites

- **Node.js**: `v18.17.0` or higher (`v20+` recommended) & `npm`
- **Python**: `3.11` or `3.12`
- **Git**
- *(Optional)* **Docker & Docker Compose** (for multi-container deployment)

---

## Installation & Quickstart

### Option A: Standalone Local Setup (Recommended for Development)

This setup uses the default embedded SQLite database and requires **zero external database setup**.

#### 1. Clone the Repository
```bash
git clone https://github.com/leopathu/aura.git
cd aura
```

#### 2. Configure Backend Environment
```bash
cp .env.example backend/.env
```

#### 3. Setup Python Virtual Environment & Install Dependencies
```bash
# If using the existing project backend_venv:
source backend_venv/bin/activate

# OR create a new virtual environment:
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

#### 4. Start the Backend API Server
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*The backend automatically runs migrations and seeds default roles, permissions, demo users, sample Brains, and sample datasets on first startup.*

- **API Documentation (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

#### 5. Setup & Start Frontend Console (in a separate terminal)
```bash
cd frontend
npm install

# For development with hot reloading:
npm run dev

# OR for production build:
npm run build
npm run start
```

- **Aura Web Console**: [http://localhost:3000](http://localhost:3000)

---

### Option B: Docker Compose (Full Stack with Postgres & Redis)

This option deploys the complete production stack, including PostgreSQL 16 with the `pgvector` extension, Redis, MinIO object storage, the FastAPI backend, background worker, and Next.js frontend.

```bash
# Start all containers in the background
docker compose up -d --build

# View container logs
docker compose logs -f api
```

- **Frontend Console**: [http://localhost:3000](http://localhost:3000)
- **FastAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **MinIO Console**: [http://localhost:9001](http://localhost:9001) (`minioadmin` / `minioadmin`)

---

## Configuration & Environment Variables

Key configuration variables located in `.env` or `backend/.env`:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `ENVIRONMENT` | `development` | Deployment environment (`development`, `production`) |
| `DEBUG` | `true` | Enables detailed logging and debug endpoints |
| `SECRET_KEY` | *(Set strong key in prod)* | JWT secret key for token signing (min 32 chars) |
| `ENCRYPTION_KEY` | *(Fernet symmetric key)* | Encryption key for securing database credentials at rest |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | JWT access token lifespan (24 hours) |
| `DATABASE_URL` | `sqlite+aiosqlite:///./aura.db` | Main application database connection string |
| `STORAGE_DIR` | `./storage` | Directory for uploaded documents and temporary files |
| `UPLOAD_MAX_SIZE_MB` | `50` | Maximum file upload limit in megabytes |
| `SQL_MAX_ROWS` | `10000` | Upper cap on rows returned by database queries |
| `SQL_DEFAULT_LIMIT` | `1000` | Automatic LIMIT clause appended to user SELECT queries |
| `SQL_QUERY_TIMEOUT_SECONDS`| `30` | Execution timeout for database queries |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed CORS origins for browser access |

---

## Pre-Seeded Demo Accounts

The application initializes a demonstration organization (**Acme Corporation**) with pre-configured users, roles, and sample data:

| User | Email | Password | Assigned Role | Capabilities |
| :--- | :--- | :--- | :--- | :--- |
| **Alex Rivera** | `admin@acme.com` | `admin123` | **Organization Admin** | Full access to all Brains, Policies, AI Models, Roles, Users, and Audit Logs |
| **Sam Analyst** | `analyst@acme.com` | `analyst123` | **Analyst** | Query permitted Brains, execute safe queries, search documents, generate reports |

### Seeded Demonstration Assets:
1. **Finance & Revenue Brain**:
   - **Data Source**: Embedded SQLite database (`sales_transactions.db`) containing `customers`, `orders`, and `employees` tables with sample revenue data.
   - **Role Assignment**: Accessible to **Organization Admin** and **Analyst**.
2. **Operations & HR Brain**:
   - **Document**: *Employee Leave & Operations Handbook* (`leave_handbook.md`) with leave policies and operational guidelines indexed for RAG.
   - **Role Assignment**: Accessible to **Organization Admin** and **Analyst**.
3. **Data Security Policy**:
   - Policy masking the `email` column (`MASK_EMAIL`) and redacting the `salary` column (`REDACT`).

---

## Usage Walkthrough

### 1. Log In to the Console
1. Navigate to [http://localhost:3000/login](http://localhost:3000/login).
2. Sign in with `admin@acme.com` and `admin123`.

### 2. Manage Brains & Ingest Data
1. Navigate to **Brains** in the sidebar ([http://localhost:3000/console/brains](http://localhost:3000/console/brains)).
2. Click **+ Create Brain** to define a new domain (e.g., *Customer Success Brain*). Select the roles permitted to access it.
3. Click **Open Brain & Manage Data** on any Brain card to enter its workspace:
   - **Data Sources Tab**:
     - Click **+ Connect Database** to add a PostgreSQL, MySQL, or SQLite connection string.
     - Click **Inspect Schema** to review discovered tables and columns.
     - Click **Test Connection** or **Sync Schema**.
   - **Documents Tab**:
     - Click **+ Upload File** to drag-and-drop PDF, DOCX, XLSX, CSV, or Markdown files. The platform immediately parses, chunks, and indexes them.
     - Click **Inspect** on any document to preview parsed chunks and vector states.
   - **Role Governance Tab**:
     - Toggle role permissions to grant or revoke team access to this Brain.

### 3. Ask Questions in Natural Language
1. Click **Chat** in the navigation header ([http://localhost:3000/chat](http://localhost:3000/chat)).
2. Select a target Brain (or select *All Accessible Brains*).
3. Try asking:
   - *"How much total revenue did we generate from orders?"* &rarr; The agent queries the database, applies policies, and provides verified figures.
   - *"What is our company policy on annual vacation and sick leave?"* &rarr; The agent retrieves handbook chunks with citations.
   - *"Analyze our top customer spenders and generate an executive report."* &rarr; The agent plans, executes queries, formats tables, and exports an executive report.

### 4. Configure Data Policies & Privacy
1. Navigate to **Policy Engine** ([http://localhost:3000/console/policies](http://localhost:3000/console/policies)).
2. Define masking rules on sensitive columns (e.g. `salary`, `ssn`, `email`).
3. Set Table & Column ALLOW/DENY lists to prevent access to restricted schemas.

---

## API Reference

The FastAPI backend exposes an interactive OpenAPI Swagger UI at `http://localhost:8000/docs`.

### Core API Endpoints:

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/api/v1/auth/login` | `POST` | Authenticate with email/password and obtain JWT |
| `/api/v1/auth/me` | `GET` | Get current authenticated user profile and permissions |
| `/api/v1/brains` | `GET`, `POST` | List and create knowledge & data Brains |
| `/api/v1/brains/{id}` | `GET`, `PUT`, `DELETE` | Retrieve Brain details, connected sources, documents, and roles |
| `/api/v1/brains/{id}/assign-roles` | `POST` | Update role access assignments for a Brain |
| `/api/v1/brains/{id}/sources/{s_id}/detach` | `POST` | Detach a data source from a Brain |
| `/api/v1/brains/{id}/documents/{d_id}/detach` | `POST` | Detach a document from a Brain |
| `/api/v1/chat/conversations` | `GET`, `POST` | List and create chat conversation threads |
| `/api/v1/chat/conversations/{id}/messages` | `POST` | Send message and receive agent SSE streaming response |
| `/api/v1/sources` | `GET`, `POST` | Register and manage relational databases |
| `/api/v1/sources/{id}/test` | `POST` | Verify database connectivity |
| `/api/v1/sources/{id}/sync-schema` | `POST` | Trigger automated schema discovery |
| `/api/v1/documents` | `GET`, `POST` | Upload and list indexed documents |
| `/api/v1/policies` | `GET`, `POST` | Configure SQL safety, row filters, and masking policies |
| `/api/v1/models/providers` | `GET`, `POST` | Configure AI model providers (OpenAI, Ollama, Anthropic) |
| `/api/v1/rbac/roles` | `GET`, `POST` | Manage enterprise roles and permission matrices |
| `/api/v1/reports` | `GET` | Retrieve agent-generated reports and exports |
| `/api/v1/audit/logs` | `GET` | Query immutable audit logs and security traces |

---

## Running Tests

Run the backend integration test suite using `pytest`:

```bash
cd backend

# Run with virtual environment activated:
PYTHONPATH=. pytest tests -v
```

The test suite validates:
- Authentication & JWT token validation
- Brain creation, role assignment, and access isolation
- AST-level SQL safety (rejection of DML/DDL statements)
- Policy engine masking and row-level filtering
- Live schema discovery across relational connectors
- End-to-end Agent execution graph and tool dispatch

To test the frontend build:
```bash
cd frontend
npm run build
```

---

## Project Directory Structure

```text
aura/
├── backend/
│   ├── app/
│   │   ├── agent/             # State graph, planner, executor & runtime
│   │   ├── api/v1/            # FastAPI route handlers (auth, brains, chat, etc.)
│   │   ├── brains/            # Brain service, role scoping & resource binding
│   │   ├── connectors/        # Database drivers (Postgres, MySQL, SQLite)
│   │   ├── core/              # Config, crypto (Fernet), security (Bcrypt/JWT)
│   │   ├── documents/         # Multi-format parsers (PDF, DOCX, XLSX, CSV, MD)
│   │   ├── mcp/               # Model Context Protocol registry & approval gate
│   │   ├── models/            # SQLAlchemy database entities
│   │   ├── models_ai/         # AI Provider abstractions (OpenAI, Anthropic, Ollama)
│   │   ├── policies/          # SQLGlot AST engine & data masking
│   │   ├── rag/               # Vector similarity search & citations
│   │   ├── rbac/              # System permissions & role hierarchy
│   │   ├── schemas/           # Pydantic v2 domain schemas
│   │   ├── tools/             # Unified Tool Gateway
│   │   ├── worker/            # Background indexing & discovery tasks
│   │   ├── main.py            # FastAPI application entrypoint & lifespan
│   │   └── seed.py            # Default demo organization & data seeder
│   ├── tests/                 # Integration and unit test suite
│   ├── Dockerfile             # Backend container definition
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── chat/          # Real-time agent chat interface (SSE)
│   │   │   ├── console/       # Web console (Brains, Models, Policies, Roles)
│   │   │   │   └── brains/    # Brains list and tabbed [id] workspace
│   │   │   ├── login/         # Authentication views
│   │   │   └── layout.tsx     # Global layout and styling
│   │   ├── components/        # Reusable UI components
│   │   ├── lib/               # API client and streaming helpers
│   │   ├── store/             # Zustand state management
│   │   └── types/             # TypeScript domain interfaces
│   ├── Dockerfile             # Frontend container definition
│   └── package.json           # Next.js & React dependencies
├── docker-compose.yml         # Multi-container orchestration definition
├── .env.example               # Template environment configuration
├── implementation-plan.md     # Architectural specification & requirements
├── IMPLEMENTATION_STATUS.md   # Tracking document of completed features
└── README.md                  # Project documentation (this file)
```

---

## Security Considerations

- **Encryption at Rest**: Database passwords and API keys stored in the database are encrypted using Fernet symmetric encryption.
- **SQL Injection Prevention**: All queries pass through SQLGlot AST verification; string concatenation is disallowed; only parameterized and validated AST queries are executed.
- **Data Exfiltration Defense**: Agents cannot export or leak schema details or data beyond the user's role and Brain assignments.
- **Audit Trails**: Every interaction, SQL query executed, policy violation, and document search is permanently recorded in the `audit_logs` table.

---

## License

This project is licensed under the **Apache 2.0 License**. See the `LICENSE` file for details.
