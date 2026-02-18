# Test Execution Checklist

**TASK-369 to TASK-388 - Testing & Quality Assurance**  
**Status:** Implementation Complete ✅

---

## Pre-Flight Checklist

### 1. Install Backend Test Dependencies

```bash
cd backend

# Option 1: Install with test extras
pip install -e ".[test]"

# Option 2: Install specific packages
pip install pytest pytest-cov pytest-asyncio pytest-mock httpx
```

**Expected packages:**
- pytest (7.4+)
- pytest-cov (coverage reporting)
- pytest-asyncio (async test support)
- pytest-mock (mocking utilities)
- httpx (for TestClient)

### 2. Install Frontend Test Dependencies

```bash
cd frontend

# Install all dependencies including devDependencies
npm install

# Or use yarn
yarn install
```

**Expected packages:**
- jest (29.7+)
- @testing-library/react (14.1+)
- @testing-library/jest-dom (6.1+)
- cypress (13.6+)
- jest-axe (8.0+)

### 3. Verify Configuration Files

**Backend:**
- ✅ `backend/pyproject.toml` - pytest config
- ✅ `backend/tests/conftest.py` - test fixtures
- ✅ `backend/tests/unit/` - unit tests directory
- ✅ `backend/tests/integration/` - integration tests directory
- ✅ `backend/tests/performance/` - performance tests directory

**Frontend:**
- ✅ `frontend/package.json` - test scripts
- ✅ `frontend/jest.setup.js` - Jest config
- ✅ `frontend/cypress.config.ts` - Cypress config
- ✅ `frontend/__tests__/` - component tests directory
- ✅ `frontend/cypress/e2e/` - E2E tests directory

---

## Test Execution Commands

### Backend Tests

#### Run All Backend Tests
```bash
cd backend
pytest -v
```

**Expected output:**
```
tests/unit/test_auth_service.py ............................ [ 30%]
tests/unit/test_encryption_service.py ...................... [ 60%]
tests/integration/test_auth_endpoints.py ................... [ 80%]
tests/integration/test_chat_endpoints.py ................... [ 90%]
tests/integration/test_app_integrations.py ................. [100%]

=================== 50 passed in 5.23s ===================
```

#### Run Unit Tests Only
```bash
pytest tests/unit/ -v
```

#### Run Integration Tests Only
```bash
pytest tests/integration/ -v
```

#### Run Performance Tests Only
```bash
pytest tests/performance/ -v -m slow
```

#### Run with Coverage Report
```bash
pytest --cov=app --cov-report=html --cov-report=term-missing

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

**Coverage threshold:** 70% minimum (enforced)

#### Run Specific Test File
```bash
pytest tests/unit/test_auth_service.py -v
pytest tests/integration/test_chat_endpoints.py -v
```

#### Run Specific Test Method
```bash
pytest tests/unit/test_auth_service.py::TestAuthService::test_create_user_success -v
```

---

### Frontend Tests

#### Run All Component Tests
```bash
cd frontend
npm test
```

**Expected output:**
```
 PASS  __tests__/auth.test.tsx
  ✓ Login page renders correctly (52ms)
  ✓ Shows validation errors (31ms)
  ✓ Registration form validates password (42ms)

Test Suites: 3 passed, 3 total
Tests:       12 passed, 12 total
```

#### Run in Watch Mode
```bash
npm run test:watch
```

#### Run with Coverage
```bash
npm run test:coverage

# View coverage report
open coverage/lcov-report/index.html
```

**Coverage threshold:** 70% across all metrics (enforced)

#### Run Specific Test File
```bash
npm test -- auth.test.tsx
npm test -- chat.test.tsx
```

#### Run E2E Tests (Headless)
```bash
npm run test:e2e
```

**Prerequisites:**
- Next.js dev server must be running on port 3001
- Or build and start production server

**Start dev server first:**
```bash
# Terminal 1: Start Next.js
npm run dev

# Terminal 2: Run E2E tests
npm run test:e2e
```

#### Run E2E Tests (Interactive)
```bash
npm run test:e2e:open
```

This opens Cypress Test Runner for interactive debugging.

#### Run Specific E2E Test
```bash
npx cypress run --spec "cypress/e2e/registration.cy.ts"
npx cypress run --spec "cypress/e2e/agent-creation.cy.ts"
npx cypress run --spec "cypress/e2e/app-connection.cy.ts"
```

---

## Troubleshooting

### Backend Issues

#### Issue: `ModuleNotFoundError: No module named 'app'`

**Solution:**
```bash
cd backend
pip install -e .
```

#### Issue: `Database connection error`

**Solution:**
Tests use SQLite in-memory database, no PostgreSQL needed.
Check `conftest.py` fixtures are loading correctly.

#### Issue: `pytest: command not found`

**Solution:**
```bash
pip install pytest
# Or activate virtual environment
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

#### Issue: Coverage below threshold

**Solution:**
Add more tests or adjust threshold in `pyproject.toml`:
```toml
[tool.pytest.ini_options]
addopts = "--cov-fail-under=70"  # Adjust this value
```

### Frontend Issues

#### Issue: `Cannot find module 'next/navigation'`

**Solution:**
Mock is defined in `jest.setup.js`. Ensure it's being loaded:
```javascript
// jest.setup.js should be referenced in package.json
"setupFilesAfterEnv": ["<rootDir>/jest.setup.js"]
```

#### Issue: `TypeError: matchMedia is not a function`

**Solution:**
Mock is in `jest.setup.js`. If still failing, add to individual test:
```javascript
Object.defineProperty(window, 'matchMedia', {
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    addListener: jest.fn(),
    removeListener: jest.fn(),
  })),
})
```

#### Issue: Cypress tests fail to find elements

**Solution:**
Ensure Next.js is running on correct port (3001):
```bash
npm run dev  # Should start on port 3001
```

Check `cypress.config.ts` baseUrl matches:
```typescript
baseUrl: 'http://localhost:3001'
```

#### Issue: E2E tests timeout

**Solution:**
Increase timeout in specific tests:
```typescript
it('completes registration', { defaultCommandTimeout: 10000 }, () => {
  // Test code
})
```

Or globally in `cypress.config.ts`:
```typescript
export default defineConfig({
  defaultCommandTimeout: 10000
})
```

---

## Validation Checklist

### Backend Tests ✅

- [ ] All unit tests pass (test_auth_service.py, test_encryption_service.py)
- [ ] All integration tests pass (auth, chat, app integrations)
- [ ] Performance tests pass (response times within thresholds)
- [ ] Coverage report generated successfully
- [ ] Coverage meets 70% threshold
- [ ] No warnings or deprecation messages

### Frontend Tests ✅

- [ ] All component tests pass (auth.test.tsx, chat.test.tsx)
- [ ] E2E tests pass (registration, agent creation, app connection)
- [ ] Accessibility tests pass (no axe violations)
- [ ] Coverage report generated successfully
- [ ] Coverage meets 70% threshold
- [ ] No console errors during test runs

### Performance ✅

- [ ] Chat endpoint response time < 5s
- [ ] Auth endpoints response time < 500ms
- [ ] Database queries < 200ms
- [ ] SSE connections < 1s
- [ ] Concurrent requests (10+) handled successfully

### Database Optimization ✅

- [ ] Migration file created (add_performance_indexes.py)
- [ ] 20+ indexes defined
- [ ] Composite indexes for common queries
- [ ] Before/after examples documented
- [ ] Redis caching configuration ready

---

## Quick Test Run (5 Minutes)

**Fastest validation path:**

```bash
# 1. Backend quick test (30 seconds)
cd backend
pytest tests/unit/test_auth_service.py -v

# 2. Frontend quick test (30 seconds)
cd frontend
npm test -- auth.test.tsx

# 3. E2E quick test (2 minutes)
# Start server first:
npm run dev &
# Run one E2E test:
npx cypress run --spec "cypress/e2e/registration.cy.ts"
```

---

## Full Test Suite Run (15 Minutes)

**Complete validation:**

```bash
# Terminal 1: Backend
cd backend
pytest --cov=app --cov-report=html -v

# Terminal 2: Frontend
cd frontend
npm run test:coverage

# Terminal 3: E2E (requires dev server)
npm run dev &
sleep 10  # Wait for server to start
npm run test:e2e
```

---

## Continuous Integration Setup (Future)

### GitHub Actions Workflow

Create `.github/workflows/tests.yml`:

```yaml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -e ".[test]"
      
      - name: Run tests
        run: |
          cd backend
          pytest --cov=app --cov-report=xml --cov-report=term-missing
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml
          flags: backend

  frontend-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Run component tests
        run: |
          cd frontend
          npm test -- --coverage
      
      - name: Run E2E tests
        run: |
          cd frontend
          npm run dev &
          sleep 10
          npm run test:e2e
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./frontend/coverage/lcov.info
          flags: frontend
```

---

## Success Criteria

**All tests must:**
- ✅ Pass without errors
- ✅ Meet coverage thresholds (70%+)
- ✅ Complete within reasonable time (<15 min total)
- ✅ Have no flaky tests (consistent results)
- ✅ Mock external services (no real API calls)

**Coverage breakdown:**
- Backend: 50+ test cases across unit, integration, performance
- Frontend: 30+ test cases across component, E2E, accessibility
- Database: 20+ indexes for optimization
- Performance: All benchmarks within thresholds

---

## Next Actions

### Immediate (After Tests Pass)

1. **Apply Database Migrations**
   ```bash
   cd backend
   alembic upgrade head  # Apply performance indexes
   ```

2. **Commit Test Suite**
   ```bash
   git add .
   git commit -m "feat: Add comprehensive test suite (TASK-369-388)
   
   - Backend: Unit, integration, performance tests
   - Frontend: Component, E2E, accessibility tests
   - Coverage: 70% minimum enforced
   - Database: 20+ indexes for optimization
   - Caching: Redis configuration
   "
   ```

3. **Update Project Status**
   - Phase 5.1 (Testing & QA): 100% complete ✅
   - Overall progress: 383/388 tasks (98.7%)

### Next Phase

4. **Begin Security Hardening (TASK-389-403)**
   - Security audit of authentication flows
   - JWT token security review
   - Input sanitization
   - Rate limiting
   - CORS configuration

---

**Testing Infrastructure Complete!** 🎉

All 20 tasks (TASK-369 to TASK-388) implemented with comprehensive coverage across backend, frontend, performance, and optimization.
