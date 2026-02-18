# Aura AI Agent Platform - Implementation Guide

## Overview

This guide provides step-by-step instructions for implementing the Aura AI Agent Platform based on the architecture defined in [architecture.md](./architecture.md).

## Phase 1: Foundation (Weeks 1-2)

### Week 1: Backend Foundation

#### 1. Project Setup

```bash
# Create backend directory structure
cd /home/runner/work/aura/aura/backend

mkdir -p app/{core,api/{v1/endpoints},domain/{models,schemas,enums},services,integrations,db/repositories,utils,workers/tasks}

# Install dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary alembic \
    pydantic pydantic-settings python-jose passlib bcrypt \
    redis celery httpx python-multipart
```

#### 2. Core Configuration

**`app/core/config.py`:**
```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Aura AI Agent Platform"
    APP_VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Security
    SECRET_KEY: str  # JWT signing key
    ALGORITHM: str = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    MASTER_ENCRYPTION_KEY: str  # For credential encryption
    
    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Vector Database
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # External APIs
    # (Added per integration)
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

#### 3. Database Models

**`app/domain/models/user.py`:**
```python
from sqlalchemy import Column, String, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    avatar_url = Column(String)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime(timezone=True))
    last_login_at = Column(DateTime(timezone=True))
    preferences = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

Continue with other models: Organization, OrganizationMember, Credential, etc.

#### 4. Authentication Service

**`app/services/auth_service.py`:**
```python
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)
    
    def verify_password(self, plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)
    
    def create_access_token(self, user_id: str, org_id: str, role: str) -> str:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": user_id,
            "org_id": org_id,
            "role": role,
            "exp": expire,
            "type": "access"
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

auth_service = AuthService()
```

#### 5. API Endpoints

**`app/api/v1/endpoints/auth.py`:**
```python
from fastapi import APIRouter, Depends, HTTPException, status
from app.domain.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    # Implement login logic
    pass

@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(request: RegisterRequest):
    # Implement registration logic
    pass
```

### Week 2: Frontend Foundation

#### 1. Project Setup

```bash
# Navigate to frontend directory
cd /home/runner/work/aura/aura/frontend

# Install dependencies
npm install next@15 react@18 react-dom@18
npm install @tanstack/react-query axios
npm install tailwindcss postcss autoprefixer
npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu
npm install lucide-react class-variance-authority clsx tailwind-merge
```

#### 2. Directory Structure

```
app/
├── (auth)/
│   ├── layout.tsx
│   ├── login/
│   │   └── page.tsx
│   └── signup/
│       └── page.tsx
├── (dashboard)/
│   ├── layout.tsx
│   ├── page.tsx  # Dashboard home
│   └── settings/
│       └── page.tsx
├── api/
│   └── auth/
│       └── [...nextauth]/
│           └── route.ts
├── layout.tsx
└── page.tsx  # Landing page
```

#### 3. API Client

**`lib/api-client.ts`:**
```typescript
import axios, { AxiosInstance } from 'axios';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Handle token refresh
          const refreshToken = localStorage.getItem('refresh_token');
          if (refreshToken) {
            try {
              const response = await this.refreshToken(refreshToken);
              localStorage.setItem('access_token', response.access_token);
              // Retry original request
              return this.client(error.config);
            } catch (refreshError) {
              // Refresh failed, redirect to login
              window.location.href = '/login';
            }
          }
        }
        return Promise.reject(error);
      }
    );
  }

  async refreshToken(refreshToken: string) {
    const response = await this.client.post('/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  }

  // Auth endpoints
  async login(email: string, password: string) {
    const response = await this.client.post('/auth/login', { email, password });
    return response.data;
  }

  async register(data: RegisterData) {
    const response = await this.client.post('/auth/register', data);
    return response.data;
  }

  // Add more endpoint methods...
}

export const apiClient = new ApiClient();
```

#### 4. Authentication UI

**`app/(auth)/login/page.tsx`:**
```typescript
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api-client';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await apiClient.login(email, password);
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('refresh_token', response.refresh_token);
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Login failed');
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center">
      <form onSubmit={handleSubmit} className="w-full max-w-md space-y-4">
        <h1 className="text-2xl font-bold">Log in to Aura</h1>
        {error && <div className="text-red-500">{error}</div>}
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full rounded border px-4 py-2"
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded border px-4 py-2"
        />
        <button
          type="submit"
          className="w-full rounded bg-blue-600 px-4 py-2 text-white"
        >
          Log in
        </button>
      </form>
    </div>
  );
}
```

## Phase 2: BYOK & Credentials (Week 3)

### Backend Implementation

#### 1. Encryption Service

**`app/core/encryption.py`:**
```python
# Implement AES-256-GCM encryption as shown in security-architecture.md
```

#### 2. Credential Endpoints

**`app/api/v1/endpoints/credentials.py`:**
```python
from fastapi import APIRouter, Depends, HTTPException
from app.services.encryption_service import encryption_service

router = APIRouter(prefix="/credentials", tags=["credentials"])

@router.post("/", status_code=201)
async def create_credential(
    request: CredentialCreate,
    user = Depends(get_current_user)
):
    # Encrypt API key
    encrypted = encryption_service.encrypt(request.api_key)
    
    # Store in database
    credential = await credential_repository.create({
        "user_id": user.id,
        "organization_id": request.organization_id,
        "type": "llm_api_key",
        "provider": request.provider,
        "encrypted_value": encrypted['encrypted_value'],
        "encryption_salt": encrypted['salt'],
        "encryption_nonce": encrypted['nonce'],
    })
    
    return credential
```

### Frontend Implementation

**`app/(dashboard)/settings/byok/page.tsx`:**
```typescript
'use client';

import { useState } from 'react';
import { apiClient } from '@/lib/api-client';

export default function BYOKPage() {
  const [provider, setProvider] = useState('openai');
  const [apiKey, setApiKey] = useState('');
  const [name, setName] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiClient.createCredential({
        type: 'llm_api_key',
        provider,
        api_key: apiKey,
        name,
      });
      // Show success message
      setApiKey('');
      setName('');
    } catch (err) {
      // Handle error
    }
  };

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold mb-4">Bring Your Own Key (BYOK)</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">Provider</label>
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
            className="w-full rounded border px-4 py-2"
          >
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="gemini">Google Gemini</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Key Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., My OpenAI Key"
            className="w-full rounded border px-4 py-2"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">API Key</label>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="sk-..."
            className="w-full rounded border px-4 py-2"
          />
        </div>
        <button
          type="submit"
          className="rounded bg-blue-600 px-4 py-2 text-white"
        >
          Add API Key
        </button>
      </form>
    </div>
  );
}
```

## Phase 3: OAuth Integration (Week 4)

### Backend Implementation

#### 1. OAuth Service

**`app/services/oauth_service.py`:**
```python
# Implement OAuth flow as shown in security-architecture.md
```

#### 2. Integration Endpoints

**`app/api/v1/endpoints/integrations.py`:**
```python
from fastapi import APIRouter, Depends, Query
from app.services.oauth_service import oauth_service

router = APIRouter(prefix="/integrations", tags=["integrations"])

@router.get("/{integration_type}/authorize")
async def authorize_integration(
    integration_type: str,
    organization_id: str = Query(...),
    user = Depends(get_current_user)
):
    # Generate OAuth URL
    result = oauth_service.generate_authorization_url(
        provider=integration_type,
        redirect_uri=f"{settings.FRONTEND_URL}/oauth/callback",
        scope=OAUTH_SCOPES[integration_type]['read']
    )
    return result

@router.post("/{integration_type}/callback")
async def oauth_callback(
    integration_type: str,
    code: str,
    state: str,
    user = Depends(get_current_user)
):
    # Exchange code for tokens
    tokens = await oauth_service.handle_callback(
        provider=integration_type,
        code=code,
        state=state
    )
    
    # Encrypt and store tokens
    encrypted_access = encryption_service.encrypt(tokens['access_token'])
    encrypted_refresh = encryption_service.encrypt(tokens['refresh_token'])
    
    credential = await credential_repository.create({
        "user_id": user.id,
        "type": "oauth_token",
        "integration_provider": integration_type,
        "encrypted_value": encrypted_access['encrypted_value'],
        "encryption_salt": encrypted_access['salt'],
        "encryption_nonce": encrypted_access['nonce'],
        "encrypted_refresh_token": encrypted_refresh['encrypted_value'],
        "refresh_token_salt": encrypted_refresh['salt'],
        "refresh_token_nonce": encrypted_refresh['nonce'],
        "scope": tokens['scope'],
        "expires_at": datetime.utcnow() + timedelta(seconds=tokens['expires_in'])
    })
    
    return {"status": "connected", "credential_id": credential.id}
```

### Frontend Implementation

**`app/(dashboard)/settings/integrations/page.tsx`:**
```typescript
'use client';

import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';

export default function IntegrationsPage() {
  const [integrations, setIntegrations] = useState([]);

  const handleConnect = async (integrationType: string) => {
    try {
      const response = await apiClient.getAuthorizationUrl(integrationType);
      // Redirect to OAuth provider
      window.location.href = response.authorization_url;
    } catch (err) {
      console.error('Failed to connect:', err);
    }
  };

  return (
    <div className="max-w-4xl">
      <h1 className="text-2xl font-bold mb-6">Integrations</h1>
      <div className="grid grid-cols-2 gap-4">
        {[
          { type: 'gmail', name: 'Gmail', icon: '📧' },
          { type: 'slack', name: 'Slack', icon: '💬' },
          { type: 'jira', name: 'Jira', icon: '📋' },
          { type: 'google_calendar', name: 'Calendar', icon: '📅' },
        ].map((integration) => (
          <div key={integration.type} className="border rounded p-4">
            <div className="text-4xl mb-2">{integration.icon}</div>
            <h3 className="text-lg font-semibold">{integration.name}</h3>
            <button
              onClick={() => handleConnect(integration.type)}
              className="mt-4 rounded bg-blue-600 px-4 py-2 text-white"
            >
              Connect
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
```

## Phase 4: Global Search (Week 5)

### Backend Implementation

#### 1. Integration Adapters

**`app/integrations/gmail/search.py`:**
```python
from googleapiclient.discovery import build
from app.services.encryption_service import encryption_service

class GmailSearch:
    def __init__(self, credential):
        # Decrypt access token
        access_token = encryption_service.decrypt({
            'encrypted_value': credential.encrypted_value,
            'salt': credential.encryption_salt,
            'nonce': credential.encryption_nonce
        })
        
        # Build Gmail API client
        self.service = build('gmail', 'v1', credentials=access_token)
    
    async def search(self, query: str, limit: int = 50):
        results = self.service.users().messages().list(
            userId='me',
            q=query,
            maxResults=limit
        ).execute()
        
        messages = []
        for msg in results.get('messages', []):
            message_data = self.service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata'
            ).execute()
            
            messages.append({
                'id': msg['id'],
                'subject': self._get_header(message_data, 'Subject'),
                'from': self._get_header(message_data, 'From'),
                'date': self._get_header(message_data, 'Date'),
                'snippet': message_data.get('snippet'),
            })
        
        return messages
    
    def _get_header(self, message, name):
        for header in message['payload']['headers']:
            if header['name'] == name:
                return header['value']
        return None
```

#### 2. Search Service

**`app/services/search_service.py`:**
```python
import asyncio
from app.integrations.gmail.search import GmailSearch
from app.integrations.slack.search import SlackSearch
# Import other integrations...

class SearchService:
    async def search(
        self,
        query: str,
        user_id: str,
        sources: list[str] = None,
        limit: int = 50
    ):
        # Get user's connected integrations
        credentials = await credential_repository.get_active_by_user(user_id)
        
        # Filter by requested sources
        if sources:
            credentials = [c for c in credentials if c.integration_provider in sources]
        
        # Execute searches in parallel
        tasks = []
        for credential in credentials:
            if credential.integration_provider == 'gmail':
                searcher = GmailSearch(credential)
            elif credential.integration_provider == 'slack':
                searcher = SlackSearch(credential)
            # Add more integrations...
            
            tasks.append(self._search_with_timeout(
                searcher.search(query, limit),
                timeout=2.0  # 2 second timeout per source
            ))
        
        # Gather results
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate and rank results
        aggregated = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Log error, continue
                continue
            
            source = credentials[i].integration_provider
            for item in result:
                aggregated.append({
                    'source': source,
                    **item
                })
        
        # Rank by relevance (simple TF-IDF or vector similarity)
        ranked = self._rank_results(aggregated, query)
        
        return ranked[:limit]
    
    async def _search_with_timeout(self, coro, timeout):
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            return []  # Return empty on timeout
    
    def _rank_results(self, results, query):
        # Implement ranking algorithm
        # For now, just return as-is
        return results

search_service = SearchService()
```

#### 3. Search Endpoint

**`app/api/v1/endpoints/search.py`:**
```python
from fastapi import APIRouter, Depends
from app.services.search_service import search_service

router = APIRouter(prefix="/search", tags=["search"])

@router.post("/")
async def search(
    request: SearchRequest,
    user = Depends(get_current_user)
):
    results = await search_service.search(
        query=request.query,
        user_id=user.id,
        sources=request.sources,
        limit=request.limit
    )
    
    return {
        "query": request.query,
        "results": results,
        "metadata": {
            "total_results": len(results),
            "sources_queried": request.sources or ["all"]
        }
    }
```

### Frontend Implementation

**`app/(dashboard)/search/page.tsx`:**
```typescript
'use client';

import { useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { SearchBar } from '@/components/search/SearchBar';
import { SearchResults } from '@/components/search/SearchResults';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    setLoading(true);
    try {
      const response = await apiClient.search({
        query,
        sources: null,  // All sources
        limit: 50,
      });
      setResults(response.results);
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      <SearchBar
        value={query}
        onChange={setQuery}
        onSearch={handleSearch}
        loading={loading}
      />
      <SearchResults results={results} />
    </div>
  );
}
```

## Phase 5: Agent Orchestration (Week 6)

### Backend Implementation

#### 1. LLM Service

**`app/services/llm_service.py`:**
```python
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

class LLMService:
    async def chat(
        self,
        provider: str,
        api_key: str,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        if provider == 'openai':
            client = AsyncOpenAI(api_key=api_key)
            response = await client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        
        elif provider == 'anthropic':
            client = AsyncAnthropic(api_key=api_key)
            response = await client.messages.create(
                model="claude-3-opus-20240229",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.content[0].text

llm_service = LLMService()
```

#### 2. Agent Orchestrator

**`app/services/agent_orchestrator.py`:**
```python
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool
from app.services.llm_service import llm_service

class AgentOrchestrator:
    def __init__(self):
        self.tools = self._create_tools()
    
    def _create_tools(self):
        return [
            Tool(
                name="search",
                func=self._search_tool,
                description="Search across connected integrations"
            ),
            # Add more tools...
        ]
    
    async def _search_tool(self, query: str):
        results = await search_service.search(query, user_id=self.user_id)
        return str(results)
    
    async def chat(
        self,
        agent_id: str,
        conversation_id: str,
        message: str,
        user_id: str
    ):
        # Get agent configuration
        agent = await agent_repository.get(agent_id)
        
        # Get conversation history
        messages = await message_repository.get_by_conversation(conversation_id)
        
        # Build LangChain agent
        # ... (implementation details)
        
        # Execute agent
        response = await llm_service.chat(
            provider=agent.llm_provider,
            api_key=decrypted_api_key,
            messages=formatted_messages
        )
        
        # Save response
        await message_repository.create({
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": response
        })
        
        return response

agent_orchestrator = AgentOrchestrator()
```

## Testing Strategy

### Unit Tests

```python
# tests/test_auth_service.py
import pytest
from app.services.auth_service import auth_service

def test_hash_password():
    password = "SecurePassword123!"
    hashed = auth_service.hash_password(password)
    assert hashed != password
    assert auth_service.verify_password(password, hashed)
```

### Integration Tests

```python
# tests/test_api_auth.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register():
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "SecurePassword123!",
        "full_name": "Test User",
        "organization_name": "Test Org"
    })
    assert response.status_code == 201
    assert "access_token" in response.json()
```

### E2E Tests (Playwright)

```typescript
// tests/e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test('user can log in', async ({ page }) => {
  await page.goto('http://localhost:3000/login');
  await page.fill('input[type="email"]', 'test@example.com');
  await page.fill('input[type="password"]', 'SecurePassword123!');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL('/dashboard');
});
```

## Deployment

### Docker Setup

**`backend/Dockerfile`:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**`frontend/Dockerfile`:**
```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

CMD ["npm", "start"]
```

**`docker-compose.yml`:**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: aura
      POSTGRES_USER: aura
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  milvus:
    image: milvusdb/milvus:latest
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    ports:
      - "19530:19530"

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://aura:${POSTGRES_PASSWORD}@postgres:5432/aura
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: ${SECRET_KEY}
      MASTER_ENCRYPTION_KEY: ${MASTER_ENCRYPTION_KEY}
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis

  frontend:
    build: ./frontend
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000/api/v1
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
```

## Monitoring

### Logging

```python
import logging
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

# Usage
logger.info("user_login", user_id=user.id, ip=request.client.host)
```

### Metrics

```python
from prometheus_client import Counter, Histogram

request_count = Counter('http_requests_total', 'Total HTTP requests')
request_latency = Histogram('http_request_duration_seconds', 'Request latency')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    request_count.inc()
    with request_latency.time():
        response = await call_next(request)
    return response
```

## Conclusion

This implementation guide provides:
- ✅ Step-by-step instructions for each phase
- ✅ Code samples for critical components
- ✅ Testing strategies
- ✅ Deployment configuration
- ✅ Monitoring setup

Follow this guide sequentially to build a production-ready Aura AI Agent Platform.
