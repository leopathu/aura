"""
Database Optimization Script

TASK-386: Optimize slow queries
TASK-387: Add database indexes
TASK-388: Add caching layer
"""

from sqlalchemy import Index, text
from alembic import op
import sqlalchemy as sa


def upgrade():
    """
    Add database indexes for performance optimization
    TASK-387: Add database indexes
    """
    
    # User table indexes
    op.create_index(
        'idx_users_email',
        'users',
        ['email'],
        unique=True
    )
    
    op.create_index(
        'idx_users_is_active',
        'users',
        ['is_active']
    )
    
    # Organization table indexes
    op.create_index(
        'idx_organizations_name',
        'organizations',
        ['name']
    )
    
    # Membership table indexes
    op.create_index(
        'idx_memberships_user_org',
        'memberships',
        ['user_id', 'org_id']
    )
    
    # Agent table indexes
    op.create_index(
        'idx_agents_org_id',
        'agents',
        ['org_id']
    )
    
    op.create_index(
        'idx_agents_is_active',
        'agents',
        ['is_active']
    )
    
    op.create_index(
        'idx_agents_created_at',
        'agents',
        ['created_at']
    )
    
    # Credential table indexes
    op.create_index(
        'idx_credentials_org_type',
        'credentials',
        ['org_id', 'credential_type']
    )
    
    # Chat message indexes
    op.create_index(
        'idx_messages_agent_id',
        'messages',
        ['agent_id']
    )
    
    op.create_index(
        'idx_messages_created_at',
        'messages',
        ['created_at']
    )
    
    # Automation indexes
    op.create_index(
        'idx_automations_org_id',
        'automations',
        ['org_id']
    )
    
    op.create_index(
        'idx_automations_status',
        'automations',
        ['status']
    )
    
    op.create_index(
        'idx_automations_trigger_type',
        'automations',
        ['trigger_type']
    )
    
    op.create_index(
        'idx_automations_next_run',
        'automations',
        ['next_run_at']
    )
    
    # Automation run indexes
    op.create_index(
        'idx_automation_runs_automation_id',
        'automation_runs',
        ['automation_id']
    )
    
    op.create_index(
        'idx_automation_runs_status',
        'automation_runs',
        ['status']
    )
    
    op.create_index(
        'idx_automation_runs_started_at',
        'automation_runs',
        ['started_at']
    )
    
    # Composite indexes for common queries
    op.create_index(
        'idx_automations_org_status',
        'automations',
        ['org_id', 'status']
    )
    
    op.create_index(
        'idx_runs_automation_status',
        'automation_runs',
        ['automation_id', 'status']
    )


def downgrade():
    """Remove indexes"""
    op.drop_index('idx_users_email')
    op.drop_index('idx_users_is_active')
    op.drop_index('idx_organizations_name')
    op.drop_index('idx_memberships_user_org')
    op.drop_index('idx_agents_org_id')
    op.drop_index('idx_agents_is_active')
    op.drop_index('idx_agents_created_at')
    op.drop_index('idx_credentials_org_type')
    op.drop_index('idx_messages_agent_id')
    op.drop_index('idx_messages_created_at')
    op.drop_index('idx_automations_org_id')
    op.drop_index('idx_automations_status')
    op.drop_index('idx_automations_trigger_type')
    op.drop_index('idx_automations_next_run')
    op.drop_index('idx_automation_runs_automation_id')
    op.drop_index('idx_automation_runs_status')
    op.drop_index('idx_automation_runs_started_at')
    op.drop_index('idx_automations_org_status')
    op.drop_index('idx_runs_automation_status')


# Query optimization examples
OPTIMIZED_QUERIES = """
-- TASK-386: Optimize slow queries

-- Before: Slow query without index
SELECT * FROM automations WHERE org_id = 'xxx' AND status = 'ACTIVE';

-- After: Fast query with composite index
-- Uses idx_automations_org_status

-- Before: Full table scan
SELECT * FROM automation_runs WHERE automation_id = 'yyy' ORDER BY started_at DESC LIMIT 10;

-- After: Index scan + sort
-- Uses idx_automation_runs_automation_id and idx_automation_runs_started_at

-- Before: Slow join
SELECT a.*, COUNT(r.id) as run_count
FROM automations a
LEFT JOIN automation_runs r ON a.id = r.automation_id
WHERE a.org_id = 'xxx'
GROUP BY a.id;

-- After: Optimized with indexes
-- Uses idx_automations_org_id and idx_automation_runs_automation_id
"""


# Caching layer configuration
CACHE_CONFIG = """
# TASK-388: Add caching layer

# Redis cache configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
CACHE_TTL=300  # 5 minutes

# Cache keys
CACHE_USER_KEY = "user:{user_id}"
CACHE_AGENT_LIST_KEY = "agents:org:{org_id}"
CACHE_AUTOMATION_KEY = "automation:{automation_id}"

# Cache implementation example:
from redis import Redis
from functools import wraps
import json

cache = Redis(host='localhost', port=6379, db=0)

def cache_result(ttl=300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            
            # Try to get from cache
            cached = cache.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.setex(cache_key, ttl, json.dumps(result))
            
            return result
        return wrapper
    return decorator

# Usage:
@cache_result(ttl=600)
def get_user_agents(user_id: str):
    # Database query here
    pass
"""
