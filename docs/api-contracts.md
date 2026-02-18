# Aura AI Agent Platform - API Contracts

## Overview

This document defines all REST API endpoints, WebSocket protocols, request/response schemas, and authentication requirements for the Aura platform.

**Base URL**: `https://api.aura.example.com/api/v1`

**Authentication**: JWT Bearer tokens (except auth endpoints)

**Content-Type**: `application/json`

## Table of Contents

1. [Authentication](#authentication)
2. [Users](#users)
3. [Organizations](#organizations)
4. [Credentials](#credentials)
5. [Integrations](#integrations)
6. [Agents](#agents)
7. [Search](#search)
8. [Actions](#actions-phase-2)
9. [Audit](#audit)
10. [WebSocket](#websocket)
11. [Error Responses](#error-responses)

---

## Authentication

### POST `/auth/register`

Register a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "full_name": "John Doe",
  "organization_name": "Acme Corp"
}
```

**Response:** `201 Created`
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "is_verified": false,
    "created_at": "2024-01-15T10:30:00Z"
  },
  "organization": {
    "id": "uuid",
    "name": "Acme Corp",
    "slug": "acme-corp",
    "role": "owner"
  },
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

**Validation:**
- Email: Valid email format, unique
- Password: Min 8 chars, 1 uppercase, 1 lowercase, 1 number, 1 special char
- Full name: 2-255 characters
- Organization name: 2-255 characters

---

### POST `/auth/login`

Authenticate user and receive tokens.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "organizations": [
      {
        "id": "uuid",
        "name": "Acme Corp",
        "slug": "acme-corp",
        "role": "owner"
      }
    ]
  }
}
```

**Errors:**
- `401 Unauthorized`: Invalid credentials
- `403 Forbidden`: Account inactive or not verified

---

### POST `/auth/refresh`

Refresh access token using refresh token.

**Request:**
```json
{
  "refresh_token": "eyJhbGc..."
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 900
}
```

---

### POST `/auth/logout`

Invalidate current tokens.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `204 No Content`

---

### POST `/auth/verify-email`

Verify user email address.

**Request:**
```json
{
  "token": "verification-token-from-email"
}
```

**Response:** `200 OK`
```json
{
  "message": "Email verified successfully",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "is_verified": true
  }
}
```

---

## Users

### GET `/users/me`

Get current user profile.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "avatar_url": "https://...",
  "is_active": true,
  "is_verified": true,
  "preferences": {
    "theme": "dark",
    "notifications": {
      "email": true,
      "push": false
    }
  },
  "created_at": "2024-01-15T10:30:00Z",
  "last_login_at": "2024-02-18T14:22:00Z"
}
```

---

### PATCH `/users/me`

Update current user profile.

**Request:**
```json
{
  "full_name": "John Doe Jr.",
  "avatar_url": "https://...",
  "preferences": {
    "theme": "light"
  }
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe Jr.",
  "avatar_url": "https://...",
  "preferences": {
    "theme": "light",
    "notifications": {
      "email": true,
      "push": false
    }
  },
  "updated_at": "2024-02-18T14:25:00Z"
}
```

---

### POST `/users/me/change-password`

Change user password.

**Request:**
```json
{
  "current_password": "OldPassword123!",
  "new_password": "NewPassword456!"
}
```

**Response:** `200 OK`
```json
{
  "message": "Password changed successfully"
}
```

**Errors:**
- `401 Unauthorized`: Incorrect current password
- `400 Bad Request`: New password doesn't meet requirements

---

## Organizations

### GET `/organizations`

List organizations user is member of.

**Response:** `200 OK`
```json
{
  "organizations": [
    {
      "id": "uuid",
      "name": "Acme Corp",
      "slug": "acme-corp",
      "plan_tier": "pro",
      "role": "owner",
      "member_count": 5,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

### GET `/organizations/{org_id}`

Get organization details.

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "name": "Acme Corp",
  "slug": "acme-corp",
  "plan_tier": "pro",
  "max_users": 50,
  "settings": {
    "default_llm_provider": "openai",
    "require_2fa": false
  },
  "member_count": 5,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-02-10T09:15:00Z"
}
```

---

### PATCH `/organizations/{org_id}`

Update organization settings (requires admin role).

**Request:**
```json
{
  "name": "Acme Corporation",
  "settings": {
    "default_llm_provider": "anthropic",
    "require_2fa": true
  }
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "name": "Acme Corporation",
  "settings": {
    "default_llm_provider": "anthropic",
    "require_2fa": true
  },
  "updated_at": "2024-02-18T14:30:00Z"
}
```

---

### GET `/organizations/{org_id}/members`

List organization members (requires member role).

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Results per page (default: 20, max: 100)
- `role`: Filter by role (owner, admin, member, viewer)

**Response:** `200 OK`
```json
{
  "members": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "email": "user@example.com",
      "full_name": "John Doe",
      "role": "owner",
      "joined_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 5,
    "total_pages": 1
  }
}
```

---

### POST `/organizations/{org_id}/members`

Invite user to organization (requires admin role).

**Request:**
```json
{
  "email": "newuser@example.com",
  "role": "member"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "email": "newuser@example.com",
  "role": "member",
  "invited_at": "2024-02-18T14:35:00Z",
  "invite_status": "pending"
}
```

---

### DELETE `/organizations/{org_id}/members/{member_id}`

Remove member from organization (requires admin role).

**Response:** `204 No Content`

---

## Credentials

### GET `/credentials`

List user's credentials.

**Query Parameters:**
- `type`: Filter by type (llm_api_key, oauth_token)
- `provider`: Filter by provider (openai, gmail, slack, etc.)
- `organization_id`: Filter by organization

**Response:** `200 OK`
```json
{
  "credentials": [
    {
      "id": "uuid",
      "type": "llm_api_key",
      "provider": "openai",
      "name": "My OpenAI Key",
      "is_active": true,
      "last_used_at": "2024-02-18T14:00:00Z",
      "created_at": "2024-01-20T10:00:00Z"
    },
    {
      "id": "uuid",
      "type": "oauth_token",
      "provider": "gmail",
      "name": "john@example.com",
      "scope": ["https://www.googleapis.com/auth/gmail.readonly"],
      "expires_at": "2024-03-20T10:00:00Z",
      "is_active": true,
      "connection_status": "active"
    }
  ]
}
```

**Note:** Encrypted values are never returned via API

---

### POST `/credentials`

Create new credential (BYOK API key).

**Request:**
```json
{
  "type": "llm_api_key",
  "provider": "openai",
  "api_key": "sk-proj-...",
  "name": "My OpenAI Key",
  "organization_id": "uuid"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "type": "llm_api_key",
  "provider": "openai",
  "name": "My OpenAI Key",
  "is_active": true,
  "created_at": "2024-02-18T14:40:00Z"
}
```

**Validation:**
- API key format validated per provider
- Optional test call to verify key works

---

### DELETE `/credentials/{credential_id}`

Delete credential.

**Response:** `204 No Content`

**Note:** Triggers audit log entry

---

### POST `/credentials/{credential_id}/test`

Test credential validity.

**Response:** `200 OK`
```json
{
  "valid": true,
  "provider_response": {
    "model": "gpt-4",
    "rate_limit": 10000
  }
}
```

**Errors:**
- `400 Bad Request`: Invalid credential
- `401 Unauthorized`: Credential expired/revoked

---

## Integrations

### GET `/integrations`

List available integrations.

**Response:** `200 OK`
```json
{
  "integrations": [
    {
      "type": "gmail",
      "name": "Gmail",
      "description": "Search and manage your Gmail inbox",
      "scopes": {
        "read": ["https://www.googleapis.com/auth/gmail.readonly"],
        "write": ["https://www.googleapis.com/auth/gmail.modify"]
      },
      "phase": 1,
      "supported_actions": ["search"],
      "logo_url": "https://..."
    },
    {
      "type": "slack",
      "name": "Slack",
      "description": "Search and send messages in Slack",
      "scopes": {
        "read": ["search:read", "channels:read"],
        "write": ["chat:write"]
      },
      "phase": 1,
      "supported_actions": ["search"],
      "logo_url": "https://..."
    }
  ]
}
```

---

### GET `/integrations/{integration_type}/authorize`

Initiate OAuth flow for integration.

**Query Parameters:**
- `organization_id`: Organization to connect (required)
- `redirect_uri`: Custom redirect URI (optional)

**Response:** `200 OK`
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "state": "random-state-token"
}
```

**Flow:**
1. Frontend redirects user to `authorization_url`
2. User grants permissions
3. Provider redirects to callback URL with auth code
4. Backend exchanges code for tokens
5. Tokens encrypted and stored

---

### POST `/integrations/{integration_type}/callback`

Handle OAuth callback (typically called by provider).

**Request:**
```json
{
  "code": "auth-code-from-provider",
  "state": "random-state-token"
}
```

**Response:** `200 OK`
```json
{
  "credential_id": "uuid",
  "connection_id": "uuid",
  "integration_type": "gmail",
  "status": "active",
  "external_user_email": "john@example.com"
}
```

---

### GET `/integrations/{integration_type}/connections`

List active connections for integration type.

**Response:** `200 OK`
```json
{
  "connections": [
    {
      "id": "uuid",
      "credential_id": "uuid",
      "integration_type": "gmail",
      "status": "active",
      "external_user_email": "john@example.com",
      "workspace_name": null,
      "last_sync_at": "2024-02-18T14:45:00Z",
      "created_at": "2024-01-20T10:00:00Z"
    }
  ]
}
```

---

### DELETE `/integrations/{integration_type}/connections/{connection_id}`

Disconnect integration.

**Response:** `204 No Content`

**Side Effects:**
- Revokes OAuth tokens with provider
- Marks credential as inactive
- Triggers audit log

---

### POST `/integrations/{integration_type}/sync`

Manually trigger sync for integration (if applicable).

**Response:** `202 Accepted`
```json
{
  "job_id": "uuid",
  "status": "queued",
  "message": "Sync job queued"
}
```

---

## Agents

### GET `/agents`

List user's agents.

**Query Parameters:**
- `organization_id`: Filter by organization
- `is_active`: Filter by active status
- `page`: Page number
- `per_page`: Results per page

**Response:** `200 OK`
```json
{
  "agents": [
    {
      "id": "uuid",
      "name": "My Assistant",
      "description": "General purpose assistant",
      "is_active": true,
      "llm_provider": "openai",
      "config": {
        "temperature": 0.7,
        "max_tokens": 2000,
        "tools_enabled": ["search", "memory"]
      },
      "conversation_count": 5,
      "created_at": "2024-01-25T10:00:00Z",
      "updated_at": "2024-02-18T14:50:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 1,
    "total_pages": 1
  }
}
```

---

### POST `/agents`

Create new agent.

**Request:**
```json
{
  "name": "Email Assistant",
  "description": "Helps manage my inbox",
  "organization_id": "uuid",
  "llm_credential_id": "uuid",
  "system_prompt": "You are a helpful email assistant...",
  "config": {
    "temperature": 0.7,
    "max_tokens": 2000,
    "tools_enabled": ["search", "gmail"]
  }
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "name": "Email Assistant",
  "description": "Helps manage my inbox",
  "system_prompt": "You are a helpful email assistant...",
  "llm_provider": "openai",
  "config": {
    "temperature": 0.7,
    "max_tokens": 2000,
    "tools_enabled": ["search", "gmail"]
  },
  "is_active": true,
  "created_at": "2024-02-18T15:00:00Z"
}
```

---

### GET `/agents/{agent_id}`

Get agent details.

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "name": "Email Assistant",
  "description": "Helps manage my inbox",
  "system_prompt": "You are a helpful email assistant...",
  "llm_provider": "openai",
  "config": {
    "temperature": 0.7,
    "max_tokens": 2000,
    "tools_enabled": ["search", "gmail"]
  },
  "is_active": true,
  "conversation_count": 3,
  "total_messages": 42,
  "created_at": "2024-02-18T15:00:00Z",
  "updated_at": "2024-02-18T15:00:00Z"
}
```

---

### PATCH `/agents/{agent_id}`

Update agent configuration.

**Request:**
```json
{
  "name": "Email & Calendar Assistant",
  "config": {
    "temperature": 0.5,
    "tools_enabled": ["search", "gmail", "calendar"]
  }
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "name": "Email & Calendar Assistant",
  "config": {
    "temperature": 0.5,
    "max_tokens": 2000,
    "tools_enabled": ["search", "gmail", "calendar"]
  },
  "updated_at": "2024-02-18T15:05:00Z"
}
```

---

### DELETE `/agents/{agent_id}`

Delete agent (soft delete).

**Response:** `204 No Content`

---

### GET `/agents/{agent_id}/conversations`

List agent conversations.

**Query Parameters:**
- `page`: Page number
- `per_page`: Results per page

**Response:** `200 OK`
```json
{
  "conversations": [
    {
      "id": "uuid",
      "title": "Email summary from last week",
      "message_count": 8,
      "created_at": "2024-02-15T10:00:00Z",
      "updated_at": "2024-02-15T10:15:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 3,
    "total_pages": 1
  }
}
```

---

### POST `/agents/{agent_id}/conversations`

Create new conversation.

**Request:**
```json
{
  "title": "New conversation"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "agent_id": "uuid",
  "title": "New conversation",
  "message_count": 0,
  "created_at": "2024-02-18T15:10:00Z"
}
```

---

### GET `/agents/{agent_id}/conversations/{conversation_id}`

Get conversation with messages.

**Query Parameters:**
- `limit`: Max messages to return (default: 50)
- `before`: Message ID for pagination (older messages)

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "agent_id": "uuid",
  "title": "Email summary from last week",
  "messages": [
    {
      "id": "uuid",
      "role": "user",
      "content": "Show me unread emails from this week",
      "created_at": "2024-02-18T15:10:00Z"
    },
    {
      "id": "uuid",
      "role": "assistant",
      "content": "I found 12 unread emails from this week...",
      "tool_calls": [
        {
          "tool": "gmail_search",
          "input": {"query": "is:unread newer_than:7d"},
          "output": {"count": 12, "emails": [...]}
        }
      ],
      "created_at": "2024-02-18T15:10:05Z"
    }
  ],
  "has_more": false,
  "created_at": "2024-02-18T15:10:00Z",
  "updated_at": "2024-02-18T15:10:05Z"
}
```

---

### POST `/agents/{agent_id}/conversations/{conversation_id}/messages`

Send message to agent (synchronous response).

**Request:**
```json
{
  "content": "Summarize my unread emails"
}
```

**Response:** `200 OK`
```json
{
  "message": {
    "id": "uuid",
    "role": "assistant",
    "content": "You have 12 unread emails. Here's a summary...",
    "tool_calls": [
      {
        "tool": "gmail_search",
        "input": {"query": "is:unread"},
        "output": {"count": 12}
      }
    ],
    "metadata": {
      "tokens_used": 450,
      "latency_ms": 2300
    },
    "created_at": "2024-02-18T15:15:00Z"
  }
}
```

**Note:** For streaming responses, use WebSocket (see [WebSocket](#websocket) section)

---

## Search

### POST `/search`

Execute global search across all connected integrations.

**Request:**
```json
{
  "query": "budget Q4 2024",
  "sources": ["gmail", "slack", "jira"],
  "filters": {
    "date_from": "2024-01-01",
    "date_to": "2024-12-31"
  },
  "limit": 50
}
```

**Response:** `200 OK`
```json
{
  "query": "budget Q4 2024",
  "results": [
    {
      "source": "gmail",
      "type": "email",
      "id": "external-id",
      "title": "Q4 Budget Review",
      "snippet": "Attached is the Q4 budget breakdown...",
      "url": "https://mail.google.com/...",
      "metadata": {
        "from": "cfo@company.com",
        "date": "2024-10-15T14:00:00Z",
        "has_attachments": true
      },
      "relevance_score": 0.95
    },
    {
      "source": "slack",
      "type": "message",
      "id": "external-id",
      "title": "#finance channel",
      "snippet": "Final Q4 budget numbers are in...",
      "url": "https://workspace.slack.com/...",
      "metadata": {
        "channel": "finance",
        "author": "Jane Doe",
        "timestamp": "2024-10-20T09:30:00Z"
      },
      "relevance_score": 0.88
    }
  ],
  "metadata": {
    "total_results": 23,
    "sources_queried": ["gmail", "slack", "jira"],
    "sources_failed": [],
    "execution_time_ms": 1850
  }
}
```

**Performance:**
- Target latency: <3 seconds
- Parallel execution across sources
- Circuit breaker for slow sources
- Results cached for 5 minutes

---

## Actions (Phase 2)

### GET `/actions`

List actions (pending, completed, or all).

**Query Parameters:**
- `status`: Filter by status (pending, approved, executing, completed, failed, rejected)
- `type`: Filter by action type
- `page`: Page number
- `per_page`: Results per page

**Response:** `200 OK`
```json
{
  "actions": [
    {
      "id": "uuid",
      "type": "gmail.send_email",
      "status": "pending",
      "title": "Send budget summary to team",
      "description": "Draft email with Q4 budget summary",
      "preview": {
        "to": ["team@company.com"],
        "subject": "Q4 Budget Summary",
        "body": "Hi team, here's the Q4 budget summary..."
      },
      "ai_reasoning": "User requested a summary email based on recent budget discussions",
      "created_at": "2024-02-18T15:20:00Z",
      "expires_at": "2024-02-18T16:20:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 1,
    "total_pages": 1
  }
}
```

---

### GET `/actions/{action_id}`

Get action details.

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "type": "gmail.send_email",
  "status": "pending",
  "title": "Send budget summary to team",
  "description": "Draft email with Q4 budget summary",
  "parameters": {
    "to": ["team@company.com"],
    "subject": "Q4 Budget Summary",
    "body": "Hi team, here's the Q4 budget summary...",
    "attachments": []
  },
  "preview": {
    "to": ["team@company.com"],
    "subject": "Q4 Budget Summary",
    "body_preview": "Hi team, here's the Q4..."
  },
  "ai_reasoning": "User requested a summary email based on recent budget discussions",
  "agent_id": "uuid",
  "conversation_id": "uuid",
  "created_at": "2024-02-18T15:20:00Z",
  "expires_at": "2024-02-18T16:20:00Z"
}
```

---

### POST `/actions/{action_id}/approve`

Approve pending action.

**Request (optional):**
```json
{
  "modifications": {
    "subject": "Updated Q4 Budget Summary"
  }
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "status": "approved",
  "approved_by": "uuid",
  "approved_at": "2024-02-18T15:25:00Z",
  "message": "Action approved and queued for execution"
}
```

---

### POST `/actions/{action_id}/reject`

Reject pending action.

**Request:**
```json
{
  "reason": "Email should go to leadership, not entire team"
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "status": "rejected",
  "rejected_by": "uuid",
  "rejected_at": "2024-02-18T15:25:00Z",
  "rejection_reason": "Email should go to leadership, not entire team"
}
```

---

## Audit

### GET `/audit`

Query audit logs.

**Query Parameters:**
- `action_type`: Filter by action type
- `resource_type`: Filter by resource type
- `resource_id`: Filter by resource ID
- `status`: Filter by status (success, failure)
- `date_from`: Start date (ISO 8601)
- `date_to`: End date (ISO 8601)
- `page`: Page number
- `per_page`: Results per page

**Response:** `200 OK`
```json
{
  "logs": [
    {
      "id": "uuid",
      "action_type": "agent.query",
      "resource_type": "agent",
      "resource_id": "uuid",
      "details": {
        "query": "Show unread emails",
        "tools_used": ["gmail_search"],
        "tokens_used": 450
      },
      "status": "success",
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0...",
      "created_at": "2024-02-18T15:15:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 123,
    "total_pages": 3
  }
}
```

---

### GET `/audit/export`

Export audit logs (CSV/JSON).

**Query Parameters:**
- Same filters as `/audit`
- `format`: Export format (csv, json)

**Response:** `200 OK`
```
Content-Type: text/csv
Content-Disposition: attachment; filename="audit-logs-2024-02-18.csv"

id,action_type,resource_type,status,created_at
uuid,agent.query,agent,success,2024-02-18T15:15:00Z
...
```

---

## WebSocket

### Connection

**URL:** `wss://api.aura.example.com/ws`

**Authentication:**
```
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Protocol: bearer, <access_token>
```

### Message Format

All messages are JSON with a `type` field.

#### Client → Server

**1. Subscribe to agent conversation**
```json
{
  "type": "subscribe",
  "channel": "agent.conversation",
  "conversation_id": "uuid"
}
```

**2. Send message (streaming response)**
```json
{
  "type": "message",
  "conversation_id": "uuid",
  "content": "Summarize my emails"
}
```

**3. Unsubscribe**
```json
{
  "type": "unsubscribe",
  "channel": "agent.conversation",
  "conversation_id": "uuid"
}
```

#### Server → Client

**1. Connection acknowledgment**
```json
{
  "type": "connected",
  "client_id": "uuid"
}
```

**2. Subscription confirmation**
```json
{
  "type": "subscribed",
  "channel": "agent.conversation",
  "conversation_id": "uuid"
}
```

**3. Streaming message chunk**
```json
{
  "type": "message.chunk",
  "conversation_id": "uuid",
  "message_id": "uuid",
  "content": "You have ",
  "is_final": false
}
```

**4. Message complete**
```json
{
  "type": "message.complete",
  "conversation_id": "uuid",
  "message": {
    "id": "uuid",
    "role": "assistant",
    "content": "You have 12 unread emails...",
    "tool_calls": [...],
    "metadata": {
      "tokens_used": 450,
      "latency_ms": 2300
    },
    "created_at": "2024-02-18T15:30:00Z"
  }
}
```

**5. Action notification (Phase 2)**
```json
{
  "type": "action.proposed",
  "action": {
    "id": "uuid",
    "type": "gmail.send_email",
    "title": "Send email to team",
    "preview": {...}
  }
}
```

**6. Error**
```json
{
  "type": "error",
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Too many requests"
  }
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "error": {
    "code": "error_code",
    "message": "Human-readable error message",
    "details": {
      "field": "Additional context"
    },
    "request_id": "uuid"
  }
}
```

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 400 | Bad Request | Invalid input, validation error |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource already exists |
| 422 | Unprocessable Entity | Semantic validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Temporary outage |

### Common Error Codes

```json
{
  "auth_required": "Authentication required",
  "invalid_token": "Token expired or invalid",
  "insufficient_permissions": "User lacks required permissions",
  "resource_not_found": "Requested resource not found",
  "validation_error": "Request validation failed",
  "rate_limit_exceeded": "Rate limit exceeded",
  "external_api_error": "External API error (Gmail, Slack, etc.)",
  "encryption_error": "Credential encryption/decryption failed",
  "llm_error": "LLM API error",
  "database_error": "Database operation failed"
}
```

### Example Error Responses

**Validation Error (400):**
```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed",
    "details": {
      "email": "Invalid email format",
      "password": "Password must be at least 8 characters"
    },
    "request_id": "req_abc123"
  }
}
```

**Unauthorized (401):**
```json
{
  "error": {
    "code": "invalid_token",
    "message": "Access token expired",
    "request_id": "req_abc123"
  }
}
```

**Rate Limit (429):**
```json
{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Rate limit exceeded. Try again in 60 seconds.",
    "details": {
      "limit": 100,
      "remaining": 0,
      "reset_at": "2024-02-18T15:35:00Z"
    },
    "request_id": "req_abc123"
  }
}
```

---

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/auth/login` | 5 requests | 5 minutes |
| `/auth/register` | 3 requests | 1 hour |
| `/search` | 30 requests | 1 minute |
| `/agents/.../messages` | 20 requests | 1 minute |
| `/credentials` (write) | 10 requests | 1 minute |
| Global (per user) | 100 requests | 1 minute |

**Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1708271700
```

---

## Pagination

All list endpoints support cursor-based pagination:

**Request:**
```
GET /agents?page=1&per_page=20
```

**Response:**
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 45,
    "total_pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## Webhooks (Future)

For third-party integrations to notify Aura of events:

```
POST /webhooks/{integration_type}
X-Webhook-Signature: sha256=...

{
  "event": "message.received",
  "data": {...}
}
```

---

## API Versioning

- Current version: `v1`
- Version in URL: `/api/v1/...`
- Deprecated endpoints receive 12-month notice
- Breaking changes require new version

---

## OpenAPI Specification

Full OpenAPI 3.0 spec available at:
```
GET /api/v1/openapi.json
```

Interactive documentation:
```
GET /api/v1/docs
```

---

## Security Headers

All API responses include:

```
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
```

---

## CORS

Allowed origins configured per environment:

**Development:**
```
Access-Control-Allow-Origin: http://localhost:3000
```

**Production:**
```
Access-Control-Allow-Origin: https://app.aura.example.com
```

**Methods:**
```
Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
```

**Headers:**
```
Access-Control-Allow-Headers: Authorization, Content-Type
Access-Control-Max-Age: 86400
```

---

## Summary

This API provides:
- ✅ RESTful endpoints for all resources
- ✅ WebSocket for real-time agent interactions
- ✅ Comprehensive error handling
- ✅ Rate limiting and pagination
- ✅ Strong authentication and authorization
- ✅ Complete audit trail
- ✅ OpenAPI documentation

All endpoints follow consistent patterns and return predictable responses.
