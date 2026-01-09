# Aura - Quick Reference

## 🚀 Start Commands

### Using Docker
```bash
docker-compose up -d          # Start all services
docker-compose logs -f        # View logs
docker-compose down           # Stop all services
docker-compose restart        # Restart services
```

### Manual Start
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2 - Frontend  
cd frontend
npm run dev
```

## 🔗 URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## 📋 Key Concepts

### User Flow
1. Register → 2. Create Org → 3. Add API Key → 4. Create Agent → 5. Chat

### Role Hierarchy
- **Owner**: Full control, can delete org
- **Admin**: Can manage members and settings
- **Member**: Can use agents and chat

### Data Isolation
Every query is scoped to `org_id` - users can only access data from their organizations.

## 🔑 Environment Variables

### Backend (.env)
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/aura
SECRET_KEY=<generate-with-secrets>
ENCRYPTION_KEY=<generate-with-secrets>
ALLOWED_ORIGINS=http://localhost:3000
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🗄️ Database Commands

```bash
# Create database
createdb aura

# Enable pgvector
psql aura -c "CREATE EXTENSION vector;"

# Initialize schema
psql aura -f database/init.sql

# Connect to database
psql aura

# Drop and recreate (DEV ONLY)
dropdb aura && createdb aura && psql aura -f database/init.sql
```

## 🧪 Testing API

### Register User
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

### Create Organization
```bash
curl -X POST http://localhost:8000/api/v1/organizations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "My Company",
    "slug": "my-company",
    "description": "Our organization"
  }'
```

## 🐛 Common Issues

### Port Already in Use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

### Database Connection Error
- Check if PostgreSQL is running: `pg_isready`
- Verify DATABASE_URL in .env
- Ensure database exists: `psql -l | grep aura`

### Module Not Found (Backend)
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Module Not Found (Frontend)
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### CORS Error
- Check ALLOWED_ORIGINS in backend/.env
- Verify NEXT_PUBLIC_API_URL in frontend/.env.local
- Ensure backend is running

### Token Expired
- Clear browser localStorage
- Login again
- Check ACCESS_TOKEN_EXPIRE_MINUTES in backend config

## 📊 Database Quick Queries

```sql
-- Check users
SELECT email, is_active, created_at FROM users;

-- Check organizations
SELECT o.name, o.slug, m.role, u.email 
FROM organizations o 
JOIN memberships m ON o.id = m.org_id 
JOIN users u ON m.user_id = u.id;

-- Check credentials
SELECT c.credential_type, c.label, o.name 
FROM credentials c 
JOIN organizations o ON c.org_id = o.id 
WHERE c.is_active = true;

-- Check agents
SELECT a.name, a.description, o.name as org_name 
FROM agents a 
JOIN organizations o ON a.org_id = o.id 
WHERE a.is_active = true;

-- Check activity logs
SELECT action_type, status, created_at 
FROM activity_logs 
ORDER BY created_at DESC 
LIMIT 10;
```

## 🔧 Development Tips

### Hot Reload
Both backend and frontend support hot reload:
- Backend: Change Python files, server reloads automatically
- Frontend: Change React files, browser updates automatically

### API Documentation
Visit `/api/docs` for interactive Swagger UI where you can test all endpoints.

### State Management
Frontend uses Zustand for state. Check `lib/store.ts` to see current state structure.

### Adding New Endpoint
1. Create function in `backend/app/api/v1/endpoints/`
2. Add route to `router.py`
3. Create corresponding schema in `app/schemas/`
4. Update frontend API calls in `lib/api.ts`

### Adding New Database Table
1. Create model in `app/db/models/`
2. Import in `app/db/base.py`
3. Add to `database/init.sql`
4. Restart backend to create table

## 📱 UI Pages

- `/` - Landing page
- `/auth/register` - Registration
- `/auth/login` - Login
- `/dashboard` - Main dashboard
- `/chat` - Chat interface
- `/agents/create` - Create agent (to be implemented)
- `/settings` - Settings (to be implemented)

## 🎯 Next Development Steps

1. **Implement OAuth flows** for Gmail, Slack integration
2. **Add vector embeddings** for semantic memory
3. **Create approval drawer** component
4. **Implement email verification**
5. **Add password reset flow**
6. **Create settings page** for credentials
7. **Build agent configuration UI**
8. **Add rate limiting**
9. **Implement proper error boundaries**
10. **Add loading skeletons**

## 📚 Documentation Links

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Next.js Docs](https://nextjs.org/docs)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [MCP Spec](https://modelcontextprotocol.io/)
- [pgvector Docs](https://github.com/pgvector/pgvector)

## 💡 Pro Tips

1. Use `httpx` for async HTTP in backend
2. Use Server-Sent Events (SSE) for streaming
3. Store vectors normalized for faster similarity search
4. Use connection pooling for database
5. Implement request ID tracking for debugging
6. Add structured logging early
7. Use TypeScript strict mode
8. Implement proper error boundaries in React
9. Use React Query for data fetching
10. Add E2E tests with Playwright

---

**Need help?** Check `MVP_SUMMARY.md` for full documentation.
