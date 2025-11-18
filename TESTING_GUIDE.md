# 🧪 Testing Guide - Aura RAG System

## Quick Start Testing

### 1. Access the Application
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### 2. Login with Test Account
Use one of these existing accounts:
```
Email: test2@example.com
Password: TestPass123!

OR

Email: newuser@example.com
Password: TestPass123!
```

### 3. Test Each Feature

#### ✅ Dashboard Home
- Navigate to: http://localhost:3000/dashboard
- Should see: Welcome message, stats cards, quick actions, getting started guide
- Click on any quick action card to navigate

#### ✅ Brains Management
- Click "Brains" in sidebar OR "Create Brain" button
- **Create a Brain:**
  1. Click "Create Brain" button
  2. Fill in:
     - Name: "Product Documentation" (or any name)
     - Description: "Knowledge base for product docs"
     - Visibility: Select "Private"
  3. Click "Create Brain"
  4. Should redirect to brains list with your new brain

#### ✅ Document Upload
- Click "Documents" in sidebar
- **Upload a Document:**
  1. Select your brain from dropdown
  2. Click "Choose File"
  3. Select a file (PDF, DOCX, TXT, etc.)
  4. File should upload automatically
  5. Wait for status to change to "processed" (may take a few seconds)

**Test Files You Can Use:**
- Any PDF file
- Any Word document (.docx)
- Any text file (.txt)
- Any markdown file (.md)

#### ✅ Chat with AI
- Click "Chat" in sidebar
- **Start Chatting:**
  1. Select your brain from dropdown
  2. Type a question related to your uploaded document
  3. Press "Send"
  4. Wait for AI response (you'll see "Thinking..." indicator)
  5. Continue conversation
  6. Click "New Chat" to start fresh

**Example Questions:**
- "What is this document about?"
- "Summarize the main points"
- "What does it say about [specific topic]?"

#### ✅ Team Management (Admin Only)
- Click "Team" in sidebar
- Should see three tabs: Users, Teams, Departments
- **Add a User:**
  1. Click "Add User" button
  2. Fill in name, email, password
  3. Click "Add"
  4. New user appears in table

- **Add a Team:**
  1. Click "Teams" tab
  2. Click "Add Team" button
  3. Fill in name and description
  4. Click "Add"

- **Add a Department:**
  1. Click "Departments" tab
  2. Click "Add Department" button
  3. Fill in name and description
  4. Click "Add"

#### ✅ Settings
- Click "Settings" in sidebar
- **Update Profile:**
  1. Change your name
  2. Optionally change password (fill both fields)
  3. Click "Save Changes"
  4. Should see success message

- **Update Organization (Admin only):**
  1. Click "Organization" tab
  2. Change organization name
  3. Click "Save Changes"

#### ✅ Logout
- Click your name/email at bottom of sidebar
- Click "Logout" button
- Should redirect to login page

## 🐛 Troubleshooting

### Problem: Chat not working / No AI response
**Solution:** Add your OpenAI API key:
```bash
# Edit backend/.env file
nano backend/.env

# Replace this line:
OPENAI_API_KEY=your-openai-api-key

# With your actual key:
OPENAI_API_KEY=sk-your-actual-openai-key

# Restart backend
docker compose restart backend
```

### Problem: Document shows "processing" forever
**Possible causes:**
1. OpenAI API key not configured (see above)
2. Document format not supported
3. Document too large (max 10MB)
4. Check backend logs:
```bash
docker compose logs backend -f
```

### Problem: "Failed to fetch" errors
**Solution:** Check if all containers are running:
```bash
docker compose ps
# All should show "Up" status

# If any are down, restart:
docker compose restart
```

### Problem: 404 errors on pages
**Solution:** Frontend needs rebuild:
```bash
docker compose restart frontend
# Wait 30 seconds for hot reload
```

### Problem: Can't create brain/upload document
**Check:**
1. You're logged in (check if redirected to /login)
2. Backend is running: `docker compose ps backend`
3. Database is connected: `docker compose logs backend | grep "database"`

## 🔍 Testing Checklist

- [ ] Register new account
- [ ] Login with account
- [ ] View dashboard
- [ ] Create a brain
- [ ] Upload a document to brain
- [ ] Wait for document to be processed
- [ ] Start a chat session
- [ ] Ask questions about the document
- [ ] Receive AI responses
- [ ] Create another brain
- [ ] Upload document to second brain
- [ ] Switch between brains in chat
- [ ] View all brains on brains page
- [ ] Delete a brain
- [ ] Add a team member (if admin)
- [ ] Update profile settings
- [ ] Change password
- [ ] Logout
- [ ] Login again with new password

## 📊 What to Expect

### Successful Document Processing Flow:
1. Upload document → Status: "processing"
2. Backend extracts text
3. Backend creates embeddings (using OpenAI)
4. Backend stores in Qdrant vector database
5. Status changes to "processed"
6. Document is ready for chat

### Successful Chat Flow:
1. User asks question
2. Backend searches relevant document chunks (vector search)
3. Backend sends chunks + question to OpenAI
4. OpenAI generates contextual answer
5. Answer displayed to user

## 🎯 Advanced Testing

### Test Multiple Brains
1. Create 3 different brains with different topics
2. Upload relevant documents to each
3. Verify chat gives different answers based on selected brain

### Test Visibility
1. Create brains with different visibility levels
2. Switch users (register another account)
3. Verify visibility restrictions work

### Test File Types
Upload different file types to test processing:
- PDF files
- Word documents (.docx)
- Text files (.txt)
- Markdown files (.md)
- CSV files
- Images with text (if OCR is configured)

### Performance Testing
1. Upload a large document (near 10MB limit)
2. Upload multiple documents simultaneously
3. Ask complex questions requiring multiple document chunks
4. Test chat with long conversation history

## 🔗 Quick Links

- Dashboard: http://localhost:3000/dashboard
- Brains: http://localhost:3000/dashboard/brains
- Documents: http://localhost:3000/dashboard/documents
- Chat: http://localhost:3000/dashboard/chat
- Team: http://localhost:3000/dashboard/team
- Settings: http://localhost:3000/dashboard/settings
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## 📝 Sample Test Data

### Test Brain 1: Company Policies
- Name: "HR Policies"
- Description: "Employee handbook and company policies"
- Visibility: Organization
- Documents: Upload your company handbook PDF

### Test Brain 2: Technical Documentation
- Name: "API Documentation"
- Description: "Technical specs and API reference"
- Visibility: Team
- Documents: Upload API docs or technical manuals

### Test Brain 3: Personal Notes
- Name: "My Notes"
- Description: "Personal knowledge base"
- Visibility: Private
- Documents: Upload your personal notes/documents

### Sample Questions for Each Brain:
**HR Policies:**
- "What is the vacation policy?"
- "How do I request time off?"
- "What are the working hours?"

**API Documentation:**
- "How do I authenticate?"
- "What endpoints are available?"
- "What's the rate limit?"

**Personal Notes:**
- "What did I write about [topic]?"
- "Summarize my notes from [date]"
- "Find information about [keyword]"

---

**Happy Testing! 🚀**

If you encounter any issues not covered here, check:
1. Docker container logs: `docker compose logs [service-name]`
2. Browser console (F12) for frontend errors
3. Backend API docs at http://localhost:8000/docs for direct API testing
