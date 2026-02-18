# Security Quick Reference Guide

**Aura Platform Security - TASK-389 to TASK-403**

---

## Quick Start

### 1. Apply Security Middleware (1 minute)

```python
# app/main.py
from app.middleware.security import (
    SecurityHeadersMiddleware,
    InputSanitizationMiddleware,
    RateLimitMiddleware,
    IPBlockingMiddleware
)
from app.core.cors import add_cors_middleware
import redis

# Initialize Redis (optional, falls back to in-memory)
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
except:
    redis_client = None

# Create app
app = FastAPI(title="Aura Platform")

# Add CORS (first!)
add_cors_middleware(app)

# Add security middleware (in order)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(InputSanitizationMiddleware)
app.add_middleware(RateLimitMiddleware, redis_client=redis_client)
app.add_middleware(IPBlockingMiddleware, redis_client=redis_client)
```

### 2. Enable Security Logging (2 minutes)

```python
# In your auth endpoint
from app.services.security_audit import audit_logger

@router.post("/login")
async def login(form: OAuth2PasswordRequestForm, request: Request):
    user = authenticate_user(form.username, form.password)
    
    if not user:
        audit_logger.log_authentication_failure(
            email=form.username,
            ip_address=request.client.host,
            reason="Invalid credentials"
        )
        raise HTTPException(401, "Invalid credentials")
    
    audit_logger.log_authentication_success(
        user_email=user.email,
        user_id=user.id,
        ip_address=request.client.host
    )
    
    return create_tokens(user)
```

### 3. Configure Environment Variables (1 minute)

```bash
# .env
SECRET_KEY=your-super-secret-key-at-least-32-characters-long
ENCRYPTION_KEY=your-fernet-encryption-key-32-bytes
ENVIRONMENT=production
ALLOWED_ORIGINS=["https://app.aura.com"]
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 4. Run Security Tests (2 minutes)

```bash
cd backend
pytest tests/security/ -v
```

**Done! Your application now has:**
✅ Security headers  
✅ Input sanitization  
✅ Rate limiting  
✅ IP blocking  
✅ CORS protection  
✅ Security audit logs  

---

## Security Headers Applied

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Frame-Options` | DENY | Prevent clickjacking |
| `X-Content-Type-Options` | nosniff | Prevent MIME sniffing |
| `X-XSS-Protection` | 1; mode=block | Enable XSS filter |
| `Strict-Transport-Security` | max-age=31536000 | Enforce HTTPS |
| `Content-Security-Policy` | [restrictive] | Prevent XSS/injection |
| `Referrer-Policy` | strict-origin-when-cross-origin | Control referrer |
| `Permissions-Policy` | geolocation=() | Disable unused features |

---

## Rate Limits

| Endpoint Type | Limit | Window |
|--------------|-------|--------|
| Auth endpoints (`/auth/*`) | 5 requests | per minute |
| API endpoints (`/api/*`) | 100 requests | per minute |
| Global per IP | 1000 requests | per hour |

**Response on limit exceeded:**
```json
{
  "detail": "Rate limit exceeded. Please try again later.",
  "retry_after": 60
}
```
**Status Code:** 429 Too Many Requests  
**Header:** `Retry-After: 60`

---

## Input Sanitization

### Patterns Blocked

**XSS Patterns:**
- `<script>...</script>`
- `javascript:...`
- `onerror=...`, `onclick=...`
- `<iframe>`, `<object>`, `<embed>`

**SQL Patterns (detected):**
- `SELECT`, `INSERT`, `DROP`, `UNION`
- `--`, `#`, `/* */`
- `OR 1=1`, `' OR '1'='1`

**Path Traversal:**
- `../`, `..`, `%2e%2e`

### Usage

Middleware automatically sanitizes:
- Query parameters
- Request body (JSON)
- Headers

Manual sanitization:
```python
from app.middleware.security import InputSanitizationMiddleware

sanitizer = InputSanitizationMiddleware(app)
clean_text = sanitizer.sanitize_string(user_input)
```

---

## Security Audit Logging

### Event Types

**Authentication:**
- `login_success`, `login_failed`, `logout`
- `password_change`, `password_reset`

**Authorization:**
- `unauthorized_access`, `forbidden_access`

**Security Incidents:**
- `brute_force_attempt`
- `sql_injection_attempt`
- `xss_attempt`
- `rate_limit_exceeded`
- `ip_blocked`

### Log Functions

```python
from app.services.security_audit import audit_logger

# Authentication
audit_logger.log_authentication_success(email, user_id, ip)
audit_logger.log_authentication_failure(email, ip, reason)

# Security incidents
audit_logger.log_brute_force_attempt(ip, attempts)
audit_logger.log_sql_injection_attempt(ip, payload, endpoint)
audit_logger.log_xss_attempt(ip, payload, endpoint)

# Access control
audit_logger.log_unauthorized_access(email, user_id, resource, ip)

# API keys
audit_logger.log_api_key_rotation(user_id, credential_type)
```

### View Logs

```bash
# File logs
tail -f logs/security_audit.log

# Database logs (SQL)
SELECT * FROM security_audit_logs 
WHERE severity = 'CRITICAL' 
ORDER BY timestamp DESC 
LIMIT 100;
```

---

## API Key Rotation

### Automatic Rotation Policies

| Credential Type | Rotation Period |
|----------------|-----------------|
| OpenAI API Key | 90 days |
| Anthropic API Key | 90 days |
| Gmail OAuth | 30 days |
| Slack API Key | 60 days |
| Jira OAuth | 30 days |

### Manual Rotation

```python
from app.services.api_key_rotation import get_rotation_service

rotation_service = get_rotation_service(db)

# Rotate a credential
rotation_service.rotate_credential(
    credential_id="cred-123",
    new_api_key="new-secret-key",
    user_id="user-456"
)

# Check rotation status
status = rotation_service.get_rotation_status(org_id="org-789")
print(f"Credentials needing rotation: {status['needs_rotation']}")

# Get list of credentials to rotate
to_rotate = rotation_service.get_credentials_needing_rotation(org_id)
```

### Revoke Credential

```python
rotation_service.revoke_credential(
    credential_id="cred-123",
    user_id="user-456",
    reason="Compromised key detected"
)
```

---

## IP Blocking

### Automatic Blocking

**Trigger:** 10 failed authentication attempts  
**Action:** IP automatically blocked  
**Duration:** Permanent (until manually unblocked)

### Manual IP Management

```python
from app.middleware.security import IPBlockingMiddleware

ip_blocker = IPBlockingMiddleware(app)

# Block an IP
ip_blocker.block_ip("192.168.1.100", duration=3600)  # 1 hour

# Unblock an IP
ip_blocker.unblock_ip("192.168.1.100")

# Check if blocked
is_blocked = ip_blocker.is_blocked("192.168.1.100")
```

### Whitelist IPs

```python
# In middleware initialization
ip_blocker.whitelist.add("10.0.0.1")  # Office IP
ip_blocker.whitelist.add("192.168.1.50")  # Admin IP
```

---

## CORS Configuration

### Allowed Origins

**Development:**
- `http://localhost:3000`
- `http://localhost:3001`
- `http://127.0.0.1:3000`

**Production:**
- Configure via `ALLOWED_ORIGINS` environment variable
- Example: `ALLOWED_ORIGINS=["https://app.aura.com"]`

### Validate Origin

```python
from app.core.cors import CORSConfig

# Check if origin is allowed
is_allowed = CORSConfig.validate_origin("https://app.aura.com")

# Check if origin is secure (HTTPS)
is_secure = CORSConfig.is_secure_origin("https://app.aura.com")
```

### CORS Headers

**Allowed Methods:** GET, POST, PUT, PATCH, DELETE, OPTIONS  
**Allowed Headers:** Authorization, Content-Type, Accept, etc.  
**Credentials:** Enabled (cookies/auth headers allowed)  
**Max Age:** 600 seconds (10 minutes)

---

## Testing

### Run All Security Tests

```bash
cd backend

# All security tests
pytest tests/security/ -v

# Specific test file
pytest tests/security/test_auth_security.py -v
pytest tests/security/test_jwt_security.py -v
pytest tests/security/test_injection_security.py -v
pytest tests/security/test_rate_limiting.py -v

# With coverage
pytest tests/security/ --cov=app.middleware --cov=app.services
```

### Test Categories

| Test File | Tests | Focus |
|-----------|-------|-------|
| `test_auth_security.py` | 15+ | Password, auth flows, brute force |
| `test_jwt_security.py` | 17+ | Token validation, expiration, algorithms |
| `test_injection_security.py` | 17+ | SQL injection, XSS, CSRF |
| `test_rate_limiting.py` | 20+ | CORS, rate limits, headers |

---

## Common Tasks

### 1. Check Failed Login Attempts

```python
from sqlalchemy import func
from app.models import SecurityAuditLog

# Failed logins in last hour
failed_logins = db.query(SecurityAuditLog).filter(
    SecurityAuditLog.event_type == "login_failed",
    SecurityAuditLog.timestamp > datetime.utcnow() - timedelta(hours=1)
).all()

for log in failed_logins:
    print(f"{log.ip_address}: {log.user_email} - {log.message}")
```

### 2. Block Suspicious IP

```python
from app.middleware.security import IPBlockingMiddleware
from app.services.security_audit import audit_logger

# Block IP
ip_blocker.block_ip("203.0.113.45")

# Log the blocking
audit_logger.log_ip_blocked(
    ip_address="203.0.113.45",
    reason="Multiple SQL injection attempts"
)
```

### 3. Monitor Rate Limit Violations

```bash
# Query database
SELECT ip_address, COUNT(*) as violations
FROM security_audit_logs
WHERE event_type = 'rate_limit_exceeded'
  AND timestamp > NOW() - INTERVAL '1 hour'
GROUP BY ip_address
ORDER BY violations DESC;
```

### 4. Rotate All Expired Credentials

```python
from app.services.api_key_rotation import get_rotation_service

rotation_service = get_rotation_service(db)

# Get credentials needing rotation
credentials = rotation_service.get_credentials_needing_rotation(org_id)

print(f"Found {len(credentials)} credentials needing rotation")

# Notify users to rotate
for cred in credentials:
    send_rotation_reminder(cred.user_id, cred.credential_type)
```

### 5. Generate Security Report

```python
from datetime import datetime, timedelta

# Last 24 hours
start = datetime.utcnow() - timedelta(days=1)

report = {
    "failed_logins": db.query(SecurityAuditLog).filter(
        SecurityAuditLog.event_type == "login_failed",
        SecurityAuditLog.timestamp > start
    ).count(),
    
    "sql_injection_attempts": db.query(SecurityAuditLog).filter(
        SecurityAuditLog.event_type == "sql_injection_attempt",
        SecurityAuditLog.timestamp > start
    ).count(),
    
    "rate_limit_violations": db.query(SecurityAuditLog).filter(
        SecurityAuditLog.event_type == "rate_limit_exceeded",
        SecurityAuditLog.timestamp > start
    ).count(),
    
    "blocked_ips": len(ip_blocker.blacklist)
}

print(f"Security Report (Last 24h):")
print(f"  Failed Logins: {report['failed_logins']}")
print(f"  SQL Injection Attempts: {report['sql_injection_attempts']}")
print(f"  Rate Limit Violations: {report['rate_limit_violations']}")
print(f"  Blocked IPs: {report['blocked_ips']}")
```

---

## Troubleshooting

### Issue: "Rate limit exceeded" for legitimate users

**Solution 1:** Whitelist their IP
```python
ip_blocker.whitelist.add("user-ip-address")
```

**Solution 2:** Increase rate limit for endpoint
```python
# In RateLimitMiddleware.get_limit_for_path()
if "/api/premium/" in path:
    return 500  # Higher limit for premium users
```

### Issue: CORS errors in browser console

**Check:**
1. Origin is in `ALLOWED_ORIGINS`
2. Credentials are enabled if sending cookies
3. Preflight request is succeeding (OPTIONS)

**Fix:**
```python
# Add origin to allowed list
ALLOWED_ORIGINS=["https://your-frontend-domain.com"]
```

### Issue: Security logs filling up disk

**Solution:** Implement log rotation
```bash
# /etc/logrotate.d/aura-security
/path/to/logs/security_audit.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
}
```

### Issue: Redis connection failed

**Fallback:** Middleware automatically falls back to in-memory storage

**Fix:**
```bash
# Start Redis
sudo systemctl start redis

# Or with Docker
docker run -d -p 6379:6379 redis:latest
```

---

## Security Best Practices

✅ **DO:**
- Use HTTPS in production
- Rotate API keys regularly
- Monitor security logs daily
- Keep dependencies updated
- Use strong passwords
- Enable MFA when available
- Limit rate aggressively on auth endpoints
- Log all security events
- Test security regularly

❌ **DON'T:**
- Use wildcard (*) CORS in production
- Store passwords in plaintext
- Expose sensitive data in errors
- Allow unlimited requests
- Trust user input without validation
- Disable security middleware
- Ignore security logs
- Use weak encryption

---

## Emergency Procedures

### Security Incident Response

1. **Identify the threat**
   - Check security logs
   - Identify attack pattern
   - List affected resources

2. **Contain the damage**
   ```python
   # Block attacking IPs
   ip_blocker.block_ip("attacker-ip")
   
   # Revoke compromised credentials
   rotation_service.revoke_credential(credential_id, user_id, "Compromised")
   
   # Force password reset for affected users
   user.force_password_reset = True
   ```

3. **Investigate**
   ```sql
   -- Find all actions by attacker
   SELECT * FROM security_audit_logs
   WHERE ip_address = 'attacker-ip'
   ORDER BY timestamp DESC;
   ```

4. **Recover**
   - Restore from backup if needed
   - Rotate all potentially compromised keys
   - Update security rules

5. **Document**
   - Record incident details
   - Update procedures
   - Notify stakeholders if required

---

## Monitoring & Alerts

### Key Metrics to Monitor

1. **Failed login rate** - Spike indicates brute force
2. **Rate limit violations** - High count indicates abuse
3. **SQL injection attempts** - Any count is critical
4. **XSS attempts** - Any count is critical
5. **Blocked IPs** - Growing list needs review

### Set Up Alerts

```python
# Example: Alert on critical events
from app.services.security_audit import audit_logger

def send_alert(event):
    if event.severity == "CRITICAL":
        # Send email/Slack/PagerDuty notification
        notify_security_team(event)

# Hook into logging
audit_logger.add_handler(send_alert)
```

---

## Additional Resources

- **Full Documentation:** `/docs/SECURITY_IMPLEMENTATION.md`
- **Test Files:** `/backend/tests/security/`
- **Middleware:** `/backend/app/middleware/security.py`
- **Audit Logging:** `/backend/app/services/security_audit.py`
- **API Key Rotation:** `/backend/app/services/api_key_rotation.py`
- **CORS Config:** `/backend/app/core/cors.py`

---

**Security Status:** ✅ **HARDENED**  
**Last Updated:** February 19, 2026  
**Review Date:** May 19, 2026 (90 days)
