# Aura AI Agent Platform - Security Architecture

## Executive Summary

Security is the foundation of the Aura AI Agent Platform. As a "trust-first" system handling sensitive user data, API keys, and OAuth tokens, we implement defense-in-depth security across all layers of the architecture.

**Security Principles:**
1. **Zero Trust**: Never trust, always verify
2. **Least Privilege**: Minimum necessary permissions
3. **Defense in Depth**: Multiple layers of security controls
4. **Transparency**: Full audit trail of all actions
5. **Privacy by Design**: PII protection built-in

## Threat Model

### Assets to Protect

1. **User Credentials**
   - Email/password combinations
   - OAuth access/refresh tokens
   - LLM API keys (OpenAI, Anthropic, Gemini)

2. **User Data**
   - Email content from Gmail
   - Slack messages and channels
   - Jira issues and comments
   - Calendar events
   - Conversation history with AI agents

3. **System Integrity**
   - Database integrity
   - Application availability
   - Audit trail completeness

### Threat Actors

1. **External Attackers**
   - Credential theft
   - Data exfiltration
   - Service disruption (DDoS)
   - Injection attacks (SQL, XSS, CSRF)

2. **Insider Threats**
   - Malicious admin access
   - Credential misuse
   - Data leakage

3. **Compromised Dependencies**
   - Supply chain attacks
   - Vulnerable third-party libraries

### Attack Vectors

- Authentication bypass
- Authorization bypass
- Token theft/replay
- Man-in-the-middle attacks
- Injection attacks
- Cross-site scripting (XSS)
- Cross-site request forgery (CSRF)
- Denial of service
- API key exposure
- Insecure direct object references (IDOR)

## Security Controls

### 1. Authentication

#### Password Security

**Storage:**
```python
# Bcrypt with cost factor 12
hashed_password = bcrypt.hashpw(
    password.encode('utf-8'),
    bcrypt.gensalt(rounds=12)
)
```

**Requirements:**
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number
- At least 1 special character
- Not in common password list (10k most common)

**Validation:**
```python
import re
from typing import Tuple

def validate_password(password: str) -> Tuple[bool, str]:
    """Validate password strength."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain number"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain special character"
    
    # Check against common passwords
    if password.lower() in COMMON_PASSWORDS:
        return False, "Password is too common"
    
    return True, "Password is valid"
```

#### JWT Token Management

**Access Token:**
- Algorithm: RS256 (RSA with SHA-256)
- Expiration: 15 minutes
- Claims: user_id, org_id, role, email
- Signed with private key

**Refresh Token:**
- Algorithm: RS256
- Expiration: 7 days
- Stored in HTTPOnly cookie
- Rotation on use (refresh token rotation)
- One-time use only

**Token Structure:**
```json
{
  "header": {
    "alg": "RS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user_id",
    "email": "user@example.com",
    "org_id": "org_id",
    "role": "member",
    "iat": 1708271700,
    "exp": 1708272600
  },
  "signature": "..."
}
```

**Implementation:**
```python
from datetime import datetime, timedelta
import jwt

def create_access_token(user_id: str, org_id: str, role: str) -> str:
    """Create JWT access token."""
    now = datetime.utcnow()
    payload = {
        'sub': user_id,
        'org_id': org_id,
        'role': role,
        'iat': now,
        'exp': now + timedelta(minutes=15),
        'type': 'access'
    }
    return jwt.encode(payload, PRIVATE_KEY, algorithm='RS256')

def create_refresh_token(user_id: str) -> str:
    """Create JWT refresh token."""
    now = datetime.utcnow()
    jti = str(uuid.uuid4())  # Unique token ID
    payload = {
        'sub': user_id,
        'iat': now,
        'exp': now + timedelta(days=7),
        'type': 'refresh',
        'jti': jti
    }
    
    # Store jti in Redis for revocation checking
    redis.setex(f'refresh_token:{jti}', timedelta(days=7), user_id)
    
    return jwt.encode(payload, PRIVATE_KEY, algorithm='RS256')
```

**Token Validation:**
```python
def verify_token(token: str, token_type: str = 'access') -> dict:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=['RS256'])
        
        # Verify token type
        if payload.get('type') != token_type:
            raise ValueError('Invalid token type')
        
        # For refresh tokens, check if revoked
        if token_type == 'refresh':
            jti = payload.get('jti')
            if not redis.exists(f'refresh_token:{jti}'):
                raise ValueError('Token revoked')
        
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError('Token expired')
    except jwt.InvalidTokenError:
        raise ValueError('Invalid token')
```

#### Multi-Factor Authentication (Future)

- TOTP (Time-based One-Time Password)
- SMS backup codes
- WebAuthn/FIDO2 hardware keys
- Recovery codes (10 single-use codes)

### 2. Authorization

#### Role-Based Access Control (RBAC)

**Roles:**

| Role | Permissions |
|------|------------|
| **owner** | All permissions, including delete org, manage billing |
| **admin** | Manage members, settings, credentials, agents |
| **member** | Create agents, use integrations, view audit logs (own) |
| **viewer** | Read-only access to agents and conversations |

**Permission Matrix:**

| Resource | Owner | Admin | Member | Viewer |
|----------|-------|-------|--------|--------|
| Organization settings | RWD | RW | R | R |
| Members | RWD | RWD | R | R |
| Credentials (own) | RWD | RWD | RWD | R |
| Credentials (others) | RWD | R | - | - |
| Agents (own) | RWD | RWD | RWD | R |
| Agents (others) | RWD | R | R | R |
| Audit logs (own) | R | R | R | R |
| Audit logs (org) | R | R | - | - |

**Implementation:**
```python
from enum import Enum
from typing import Optional

class Permission(Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"

class Role(Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"

def check_permission(
    user_role: Role,
    resource_type: str,
    permission: Permission,
    is_owner: bool = False
) -> bool:
    """Check if user has permission for resource."""
    
    # Owners have all permissions
    if user_role == Role.OWNER:
        return True
    
    # Resource-specific logic
    if resource_type == "credential":
        if is_owner:  # Own credential
            return permission in [Permission.READ, Permission.WRITE, Permission.DELETE]
        if user_role == Role.ADMIN:
            return permission == Permission.READ
        return False
    
    # Add more resource-specific logic...
    
    return False
```

**Middleware:**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)) -> dict:
    """Get current user from JWT token."""
    try:
        payload = verify_token(token.credentials, 'access')
        user = await get_user_by_id(payload['sub'])
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Invalid user")
        return user
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

async def require_role(
    required_role: Role,
    user: dict = Depends(get_current_user)
) -> dict:
    """Require specific role or higher."""
    role_hierarchy = {
        Role.VIEWER: 0,
        Role.MEMBER: 1,
        Role.ADMIN: 2,
        Role.OWNER: 3
    }
    
    user_role = Role(user['role'])
    if role_hierarchy[user_role] < role_hierarchy[required_role]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return user
```

### 3. Data Encryption

#### Encryption at Rest

**Credentials Encryption (AES-256-GCM):**

```python
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

class CredentialEncryption:
    """AES-256-GCM encryption for credentials."""
    
    def __init__(self, master_key: bytes):
        """Initialize with master key from environment."""
        self.master_key = master_key
    
    def encrypt(self, plaintext: str) -> dict:
        """Encrypt credential with AES-256-GCM."""
        # Generate random salt and nonce
        salt = os.urandom(16)
        nonce = os.urandom(12)
        
        # Derive key from master key + salt
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )
        key = kdf.derive(self.master_key)
        
        # Encrypt with AESGCM
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(
            nonce,
            plaintext.encode('utf-8'),
            None  # No associated data
        )
        
        # Return encrypted components
        return {
            'encrypted_value': ciphertext,
            'salt': salt,
            'nonce': nonce,
            # Auth tag is included in ciphertext
        }
    
    def decrypt(self, encrypted_data: dict) -> str:
        """Decrypt credential."""
        # Derive key from master key + salt
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=encrypted_data['salt'],
            iterations=100000
        )
        key = kdf.derive(self.master_key)
        
        # Decrypt with AESGCM
        aesgcm = AESGCM(key)
        try:
            plaintext = aesgcm.decrypt(
                encrypted_data['nonce'],
                encrypted_data['encrypted_value'],
                None
            )
            return plaintext.decode('utf-8')
        except Exception:
            raise ValueError('Decryption failed - data corrupted or wrong key')
```

**Master Key Management:**

```bash
# Production: Use AWS KMS, Google Cloud KMS, or Azure Key Vault
# Development: Environment variable

# Generate master key (one-time setup)
python -c "import os; print(os.urandom(32).hex())"

# Store in environment
export AURA_MASTER_KEY="64-char-hex-string"

# Key rotation strategy (annual)
# 1. Generate new master key
# 2. Re-encrypt all credentials with new key
# 3. Update environment variable
# 4. Verify all credentials decrypt correctly
```

**Database Encryption:**
- Enable PostgreSQL transparent data encryption (TDE)
- Encrypt database backups
- Encrypt vector database collections

#### Encryption in Transit

**TLS Configuration:**

```nginx
# Nginx TLS configuration
ssl_protocols TLSv1.3 TLSv1.2;
ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
ssl_prefer_server_ciphers on;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_stapling on;
ssl_stapling_verify on;

# HSTS
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
```

**Certificate Management:**
- Let's Encrypt for automatic certificate renewal
- 90-day certificate rotation
- Certificate pinning for mobile apps (future)

### 4. Input Validation

#### Request Validation (Pydantic)

```python
from pydantic import BaseModel, EmailStr, validator, constr
from typing import Optional

class UserCreate(BaseModel):
    """User creation schema with validation."""
    email: EmailStr
    password: constr(min_length=8, max_length=128)
    full_name: constr(min_length=2, max_length=255)
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password meets requirements."""
        valid, message = validate_password(v)
        if not valid:
            raise ValueError(message)
        return v
    
    @validator('full_name')
    def validate_name(cls, v):
        """Validate name doesn't contain suspicious characters."""
        if re.search(r'[<>{}()\[\]]', v):
            raise ValueError('Name contains invalid characters')
        return v

class SearchRequest(BaseModel):
    """Search request schema."""
    query: constr(min_length=1, max_length=500)
    sources: Optional[list[str]] = None
    limit: int = 50
    
    @validator('sources')
    def validate_sources(cls, v):
        """Validate source list."""
        if v:
            valid_sources = ['gmail', 'slack', 'jira', 'calendar']
            for source in v:
                if source not in valid_sources:
                    raise ValueError(f'Invalid source: {source}')
        return v
    
    @validator('limit')
    def validate_limit(cls, v):
        """Validate result limit."""
        if v < 1 or v > 100:
            raise ValueError('Limit must be between 1 and 100')
        return v
```

#### SQL Injection Prevention

**Always use parameterized queries:**

```python
# BAD - Vulnerable to SQL injection
query = f"SELECT * FROM users WHERE email = '{email}'"

# GOOD - Parameterized query
query = "SELECT * FROM users WHERE email = :email"
result = session.execute(query, {'email': email})

# BEST - ORM (SQLAlchemy)
user = session.query(User).filter(User.email == email).first()
```

#### XSS Prevention

**Content Security Policy:**

```http
Content-Security-Policy: 
  default-src 'self';
  script-src 'self' 'nonce-{random}';
  style-src 'self' 'nonce-{random}';
  img-src 'self' data: https:;
  font-src 'self';
  connect-src 'self' wss://api.aura.example.com;
  frame-ancestors 'none';
  base-uri 'self';
  form-action 'self';
```

**Output Escaping:**
```python
import html
import bleach

def sanitize_user_input(text: str) -> str:
    """Sanitize user input for display."""
    # Remove all HTML tags except safe ones
    allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'a']
    allowed_attrs = {'a': ['href', 'title']}
    
    clean = bleach.clean(
        text,
        tags=allowed_tags,
        attributes=allowed_attrs,
        strip=True
    )
    
    return clean
```

#### CSRF Prevention

**SameSite Cookies:**
```python
response.set_cookie(
    key='refresh_token',
    value=token,
    httponly=True,
    secure=True,
    samesite='strict',
    max_age=604800  # 7 days
)
```

**CSRF Tokens:**
```python
from fastapi import Header, HTTPException

async def verify_csrf_token(
    x_csrf_token: str = Header(None),
    csrf_cookie: str = Cookie(None)
):
    """Verify CSRF token matches cookie."""
    if not x_csrf_token or not csrf_cookie:
        raise HTTPException(status_code=403, detail="CSRF token missing")
    
    if not secrets.compare_digest(x_csrf_token, csrf_cookie):
        raise HTTPException(status_code=403, detail="CSRF token invalid")
```

### 5. PII Sanitization

**Before sending to external LLMs:**

```python
import re
from typing import Dict, List

class PIISanitizer:
    """Detect and remove PII before sending to external APIs."""
    
    # Regex patterns
    SSN_PATTERN = r'\b\d{3}-\d{2}-\d{4}\b'
    CREDIT_CARD_PATTERN = r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
    PHONE_PATTERN = r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    def __init__(self):
        self.replacements: Dict[str, str] = {}
    
    def sanitize(self, text: str) -> str:
        """Remove PII from text."""
        sanitized = text
        
        # Replace SSN
        sanitized = re.sub(
            self.SSN_PATTERN,
            '[SSN_REDACTED]',
            sanitized
        )
        
        # Replace credit cards
        sanitized = re.sub(
            self.CREDIT_CARD_PATTERN,
            '[CARD_REDACTED]',
            sanitized
        )
        
        # Replace phone numbers
        sanitized = re.sub(
            self.PHONE_PATTERN,
            '[PHONE_REDACTED]',
            sanitized
        )
        
        # Replace emails (preserve domain for context)
        def replace_email(match):
            email = match.group(0)
            domain = email.split('@')[1]
            return f'[EMAIL_REDACTED]@{domain}'
        
        sanitized = re.sub(
            self.EMAIL_PATTERN,
            replace_email,
            sanitized
        )
        
        return sanitized
    
    def desanitize(self, text: str) -> str:
        """Restore original values (if needed)."""
        for placeholder, original in self.replacements.items():
            text = text.replace(placeholder, original)
        return text

# Usage
sanitizer = PIISanitizer()
safe_text = sanitizer.sanitize(user_query)
llm_response = call_llm_api(safe_text)
```

### 6. Rate Limiting

**Implementation with Redis:**

```python
import redis
from datetime import datetime, timedelta
from fastapi import HTTPException

class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> bool:
        """Check if request is within rate limit."""
        now = datetime.utcnow().timestamp()
        window_start = now - window_seconds
        
        # Remove old requests
        self.redis.zremrangebyscore(key, 0, window_start)
        
        # Count requests in window
        request_count = self.redis.zcard(key)
        
        if request_count >= max_requests:
            # Get oldest request
            oldest = self.redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                reset_at = oldest[0][1] + window_seconds
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Reset at {reset_at}",
                    headers={
                        'X-RateLimit-Limit': str(max_requests),
                        'X-RateLimit-Remaining': '0',
                        'X-RateLimit-Reset': str(int(reset_at))
                    }
                )
        
        # Add current request
        self.redis.zadd(key, {str(now): now})
        self.redis.expire(key, window_seconds)
        
        return True

# Middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting to all requests."""
    user_id = getattr(request.state, 'user_id', None)
    
    if user_id:
        # Per-user rate limit
        key = f'rate_limit:user:{user_id}'
        await rate_limiter.check_rate_limit(key, 100, 60)
    else:
        # Per-IP rate limit for unauthenticated requests
        ip = request.client.host
        key = f'rate_limit:ip:{ip}'
        await rate_limiter.check_rate_limit(key, 20, 60)
    
    response = await call_next(request)
    return response
```

### 7. Audit Logging

**Comprehensive audit trail:**

```python
async def log_audit_event(
    action_type: str,
    user_id: str,
    organization_id: str,
    resource_type: str = None,
    resource_id: str = None,
    details: dict = None,
    status: str = 'success',
    error_message: str = None,
    request: Request = None
):
    """Log audit event."""
    log_entry = {
        'action_type': action_type,
        'user_id': user_id,
        'organization_id': organization_id,
        'resource_type': resource_type,
        'resource_id': resource_id,
        'details': details or {},
        'status': status,
        'error_message': error_message,
        'ip_address': request.client.host if request else None,
        'user_agent': request.headers.get('user-agent') if request else None,
        'request_id': request.state.request_id if request else None,
        'created_at': datetime.utcnow()
    }
    
    await audit_repository.create(log_entry)

# Usage
@app.post('/credentials')
async def create_credential(
    credential: CredentialCreate,
    user = Depends(get_current_user),
    request: Request
):
    """Create new credential."""
    try:
        new_credential = await credential_service.create(
            user_id=user.id,
            org_id=credential.organization_id,
            type=credential.type,
            provider=credential.provider,
            api_key=credential.api_key
        )
        
        await log_audit_event(
            action_type='credential.create',
            user_id=user.id,
            organization_id=credential.organization_id,
            resource_type='credential',
            resource_id=new_credential.id,
            details={'provider': credential.provider},
            request=request
        )
        
        return new_credential
    except Exception as e:
        await log_audit_event(
            action_type='credential.create',
            user_id=user.id,
            organization_id=credential.organization_id,
            status='failure',
            error_message=str(e),
            request=request
        )
        raise
```

### 8. OAuth Security

**OAuth 2.0 Best Practices:**

```python
import secrets
import hashlib
import base64
from urllib.parse import urlencode

class OAuthService:
    """Secure OAuth 2.0 implementation."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def generate_authorization_url(
        self,
        provider: str,
        redirect_uri: str,
        scope: List[str]
    ) -> dict:
        """Generate OAuth authorization URL with PKCE."""
        # Generate state token
        state = secrets.token_urlsafe(32)
        
        # Generate PKCE code verifier and challenge
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode().rstrip('=')
        
        # Store state and verifier in Redis (5 min expiry)
        self.redis.setex(
            f'oauth_state:{state}',
            300,
            json.dumps({
                'provider': provider,
                'code_verifier': code_verifier,
                'redirect_uri': redirect_uri
            })
        )
        
        # Build authorization URL
        params = {
            'client_id': OAUTH_CLIENTS[provider]['client_id'],
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(scope),
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
            'access_type': 'offline',  # For refresh token
            'prompt': 'consent'  # Force consent screen
        }
        
        auth_url = f"{OAUTH_CLIENTS[provider]['auth_url']}?{urlencode(params)}"
        
        return {
            'authorization_url': auth_url,
            'state': state
        }
    
    async def handle_callback(
        self,
        provider: str,
        code: str,
        state: str
    ) -> dict:
        """Handle OAuth callback and exchange code for tokens."""
        # Verify state
        stored_data = self.redis.get(f'oauth_state:{state}')
        if not stored_data:
            raise ValueError('Invalid or expired state token')
        
        data = json.loads(stored_data)
        if data['provider'] != provider:
            raise ValueError('Provider mismatch')
        
        # Delete state token (one-time use)
        self.redis.delete(f'oauth_state:{state}')
        
        # Exchange code for tokens
        token_params = {
            'client_id': OAUTH_CLIENTS[provider]['client_id'],
            'client_secret': OAUTH_CLIENTS[provider]['client_secret'],
            'code': code,
            'redirect_uri': data['redirect_uri'],
            'grant_type': 'authorization_code',
            'code_verifier': data['code_verifier']
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                OAUTH_CLIENTS[provider]['token_url'],
                data=token_params
            )
            
            if response.status_code != 200:
                raise ValueError('Token exchange failed')
            
            tokens = response.json()
            
            return {
                'access_token': tokens['access_token'],
                'refresh_token': tokens.get('refresh_token'),
                'expires_in': tokens.get('expires_in'),
                'scope': tokens.get('scope')
            }
```

**Minimal OAuth Scopes:**

```python
# Phase 1 - Read-only scopes
OAUTH_SCOPES = {
    'gmail': {
        'read': ['https://www.googleapis.com/auth/gmail.readonly'],
        'write': ['https://www.googleapis.com/auth/gmail.modify']  # Phase 2
    },
    'slack': {
        'read': ['search:read', 'channels:read', 'users:read'],
        'write': ['chat:write', 'channels:write']  # Phase 2
    },
    'jira': {
        'read': ['read:jira-work', 'read:jira-user'],
        'write': ['write:jira-work']  # Phase 2
    },
    'google_calendar': {
        'read': ['https://www.googleapis.com/auth/calendar.readonly'],
        'write': ['https://www.googleapis.com/auth/calendar.events']  # Phase 2
    }
}
```

### 9. Dependency Security

**Automated Scanning:**

```bash
# Python dependencies
pip install safety
safety check --json

# NPM dependencies
npm audit --json

# Docker image scanning
docker scan aura-backend:latest
```

**Dependency Update Policy:**
- Security patches: Within 24 hours
- Minor updates: Weekly
- Major updates: Monthly (with testing)

**Lock Files:**
```bash
# Python
pip freeze > requirements.txt
pip-compile requirements.in

# Node.js
npm ci  # Use package-lock.json
```

### 10. Incident Response

**Security Incident Playbook:**

1. **Detection**
   - Automated alerts from monitoring
   - User reports
   - Third-party security reports

2. **Containment**
   - Isolate affected systems
   - Revoke compromised credentials
   - Enable maintenance mode if needed

3. **Investigation**
   - Review audit logs
   - Analyze attack vectors
   - Identify affected users

4. **Remediation**
   - Patch vulnerabilities
   - Rotate credentials
   - Update security controls

5. **Communication**
   - Notify affected users within 24 hours
   - Report to authorities if required (GDPR, etc.)
   - Public disclosure if appropriate

6. **Post-Mortem**
   - Document incident timeline
   - Identify root cause
   - Implement preventive measures

**Breach Notification:**
```python
async def notify_security_breach(
    affected_users: List[str],
    breach_type: str,
    breach_details: str
):
    """Notify users of security breach."""
    for user_id in affected_users:
        # Send email notification
        await send_email(
            to=user.email,
            subject='Security Notification - Action Required',
            template='security_breach',
            context={
                'user_name': user.full_name,
                'breach_type': breach_type,
                'breach_details': breach_details,
                'action_required': 'Reset password immediately',
                'support_email': 'security@aura.example.com'
            }
        )
        
        # Log audit event
        await log_audit_event(
            action_type='security.breach_notification',
            user_id=user_id,
            details={'breach_type': breach_type}
        )
```

## Security Checklist

### Pre-Production

- [ ] All secrets in environment variables, not code
- [ ] Master encryption key stored in KMS
- [ ] TLS 1.3 configured and tested
- [ ] JWT signing keys generated (RS256)
- [ ] Rate limiting enabled and tested
- [ ] CORS configured for production domain
- [ ] CSP headers configured
- [ ] SQL injection tests passed
- [ ] XSS tests passed
- [ ] CSRF protection enabled
- [ ] Password policy enforced
- [ ] OAuth flows tested with PKCE
- [ ] Audit logging enabled for all sensitive operations
- [ ] PII sanitization tested
- [ ] Dependency vulnerabilities scanned
- [ ] Penetration testing completed
- [ ] Security headers verified
- [ ] Backup encryption verified
- [ ] Incident response plan documented

### Post-Production

- [ ] Security monitoring alerts configured
- [ ] Log aggregation and analysis setup
- [ ] Vulnerability scanning automated (weekly)
- [ ] Dependency updates automated
- [ ] Security audit scheduled (quarterly)
- [ ] Penetration testing scheduled (annually)
- [ ] Bug bounty program considered

## Compliance

### GDPR Compliance

- Right to access: `/users/me/data-export`
- Right to deletion: `/users/me/delete`
- Data portability: JSON export
- Consent management: OAuth consent screens
- Breach notification: Within 72 hours

### SOC 2 Compliance (Future)

- Audit logging
- Access controls
- Encryption at rest and in transit
- Incident response procedures
- Regular security assessments

## Security Contacts

- Security Team: security@aura.example.com
- Vulnerability Reports: security@aura.example.com
- PGP Key: Available at /security.txt

## Conclusion

This security architecture provides comprehensive protection through:

✅ **Strong Authentication**: Bcrypt passwords, JWT tokens, refresh token rotation
✅ **Fine-grained Authorization**: RBAC with role hierarchy
✅ **Data Protection**: AES-256-GCM encryption, TLS 1.3
✅ **Input Validation**: Pydantic schemas, SQL injection prevention
✅ **PII Protection**: Automated sanitization before external API calls
✅ **Rate Limiting**: Token bucket algorithm
✅ **Complete Audit Trail**: All actions logged
✅ **Secure OAuth**: PKCE, minimal scopes, state validation
✅ **Dependency Security**: Automated scanning and updates
✅ **Incident Response**: Documented procedures

Security is an ongoing process. This architecture will evolve as new threats emerge and best practices change.
