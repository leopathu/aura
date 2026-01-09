# 🚀 Aura - Quick Start Guide

## You're All Set! The MVP is Ready to Run 🎉

Everything has been configured and verified. Here's how to get started immediately.

## ⚡ Fastest Way to Start (3 Commands)

### Option 1: Using Docker (Recommended)
```bash
cd /home/leopathu/Public/aura
docker-compose up -d
```

That's it! Visit http://localhost:3000

### Option 2: Manual Start (2 Terminals)

**Terminal 1 - Backend:**
```bash
cd /home/leopathu/Public/aura/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd /home/leopathu/Public/aura/frontend
npm install
npm run dev
```

Visit http://localhost:3000

## 📋 Before First Run

### 1. Setup Database (One Time Only)
```bash
# Create database
createdb aura

# Initialize schema
psql aura -f /home/leopathu/Public/aura/database/init.sql
```

### 2. Verify Setup
```bash
cd /home/leopathu/Public/aura
./verify.sh
```

## 🎯 Your First 5 Minutes with Aura

1. **Register** (http://localhost:3000/auth/register)
   - Enter your email and password
   - Click "Create Account"

2. **Create Organization**
   - You'll be prompted to create your first org
   - Enter: Name: "My Company", Slug: "my-company"

3. **Add API Key** (Dashboard → Add API Keys)
   - Choose your LLM provider (OpenAI, Anthropic, or Gemini)
   - Enter your API key
   - Label it (e.g., "My OpenAI Key")

4. **Create Agent** (Dashboard → Create Agent)
   - Name: "My First Agent"
   - Description: "Helps me with tasks"
   - Click Create

5. **Start Chatting** (Dashboard → Chat with Agent)
   - Type: "Hello, what can you help me with?"
   - Watch the thought trace in the sidebar
   - See the agent respond

## 🌐 URLs After Starting

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs
- **Alternative API Docs**: http://localhost:8000/api/redoc

## 🔑 Test Account (For Quick Testing)

After setup, you can create a test account:
- Email: test@aura.ai
- Password: test123456
- Organization: test-org

## 🐛 Troubleshooting

### "Port already in use"
```bash
# Backend (port 8000)
lsof -ti:8000 | xargs kill -9

# Frontend (port 3000)
lsof -ti:3000 | xargs kill -9
```

### "Database connection error"
```bash
# Check if PostgreSQL is running
pg_isready

# Check if database exists
psql -l | grep aura

# If not, create it
createdb aura
psql aura -f /home/leopathu/Public/aura/database/init.sql
```

### "Module not found" (Backend)
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### "Module not found" (Frontend)
```bash
cd frontend
rm -rf node_modules
npm install
```

## 📊 Check if Everything is Running

```bash
# Check backend
curl http://localhost:8000/health

# Expected response: {"status":"healthy"}

# Check frontend
curl http://localhost:3000

# Should return HTML
```

## 🎓 What to Try Next

### Test the API Directly
Visit http://localhost:8000/api/docs and try:
1. Register a user (POST /api/v1/auth/register)
2. Login (POST /api/v1/auth/login)
3. Create an organization (POST /api/v1/organizations)
4. Add credentials (POST /api/v1/organizations/{org_id}/credentials)

### Explore the Database
```bash
psql aura

# See all tables
\dt

# Check users
SELECT email, created_at FROM users;

# Check organizations
SELECT name, slug FROM organizations;

# Exit
\q
```

### Watch Logs
```bash
# Docker logs
docker-compose logs -f

# Or specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

## 🔄 Restart Services

### Docker
```bash
docker-compose restart
```

### Manual
Just Ctrl+C in the terminal windows and run the commands again.

## 🛑 Stop Services

### Docker
```bash
docker-compose down
```

### Manual
Ctrl+C in both terminal windows.

## 📚 Need More Help?

- **Setup Issues**: See `SETUP.md`
- **API Reference**: See `QUICK_REFERENCE.md`
- **Features**: See `MVP_SUMMARY.md`
- **Architecture**: See `COMPLETE.md`

## 🎯 What You Built

This is a **production-quality MVP** with:
- ✅ Full authentication system
- ✅ Multi-tenant organization management
- ✅ Encrypted API key storage
- ✅ AI agent orchestration with LangGraph
- ✅ MCP integration framework
- ✅ Perplexity-style chat UI
- ✅ Complete audit logging
- ✅ Vector memory support

## 🚀 Next Development Steps

Once you've tested the MVP:
1. Connect real MCP servers (Gmail, Slack, etc.)
2. Implement OAuth flows
3. Add semantic search with embeddings
4. Build approval drawer UI
5. Add scheduled background tasks

## 💡 Pro Tips

1. Use the API docs at `/api/docs` - it's interactive!
2. Check the thought trace sidebar in chat to see what the agent is doing
3. Activity logs show every action for debugging
4. Organizations allow team collaboration
5. Each org can have its own API keys

## ✨ You're Ready!

Everything is configured with secure keys, proper database schema, and all features working.

**Start building the future of AI agents!** 🚀

---

Questions? Check the documentation files or the API docs at http://localhost:8000/api/docs
