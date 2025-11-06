# Enterprise GuardCAP - Quick Start Guide

## TL;DR - Get Running in 5 Minutes

### Prerequisites
- Python 3.9+
- Node.js 14+
- MongoDB Atlas account

### Step 1: Clone & Setup Environment
```bash
cd /Users/6kiity/Documents/enterprise-guardcap

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
npm install --prefix frontend
```

### Step 2: Configure Environment
Create `.env` file in project root:
```env
# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
MONGODB_URI=mongodb+srv://maskit:basakbasak@cluster0.bpbrvcu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
DATABASE_NAME=maskit
SECRET_KEY=your-secret-key-here-minimum-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Frontend
REACT_APP_API_URL=http://127.0.0.1:8000
```

### Step 3: Start Backend
```bash
source venv/bin/activate
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 4: Start Frontend
**Option A - Browser**:
Open `frontend/index.html` in web browser

**Option B - Electron Desktop App**:
```bash
cd frontend
npm start
```

### Step 5: Login with Test Account
Click any test account button on login page:
- **admin@test.com** / admin123 → System Admin Dashboard
- **policy@test.com** / policy123 → Policy Admin Dashboard
- **approver@test.com** / approver123 → Approver Dashboard
- **auditor@test.com** / auditor123 → Auditor Dashboard
- **user@test.com** / user123 → User Dashboard

That's it! You're ready to develop.

---

## Common Commands

### Start Development Environment
```bash
# Terminal 1 - Backend
source venv/bin/activate && cd backend && python -m uvicorn app.main:app --reload

# Terminal 2 - Frontend (Web)
# Just open frontend/index.html in browser

# Terminal 2 - Frontend (Electron)
cd frontend && npm start
```

### View API Documentation
```
http://localhost:8000/docs
```

### Check Backend Health
```bash
curl http://127.0.0.1:8000/health
```

### Test Login API
```bash
curl -X POST http://127.0.0.1:8000/api/v1/smtp/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"admin123"}'
```

### Create New Test User
```bash
curl -X POST http://127.0.0.1:8000/api/v1/smtp/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email":"newtestuser@test.com",
    "password":"password123",
    "nickname":"Test User",
    "department":"Testing",
    "role":"user"
  }'
```

---

## User Roles & Dashboards

```
┌─────────────────┬─────────────┬─────────────────────────────────────┐
│ Role            │ Test Email  │ Dashboard File                      │
├─────────────────┼─────────────┼─────────────────────────────────────┤
│ System Admin     │ admin       │ smtp/dashboard-admin.html           │
│ Policy Admin     │ policy      │ smtp/dashboard-policy.html          │
│ Approver        │ approver    │ pages/approver-review.html          │
│ Auditor         │ auditor     │ smtp/dashboard-auditor.html         │
│ Regular User    │ user        │ smtp/dashboard-user.html            │
└─────────────────┴─────────────┴─────────────────────────────────────┘
```

---

## Authentication Flow

```
1. User lands on frontend/index.html
2. Check: localStorage.getItem('auth_token') exists?
   → NO: Redirect to smtp/login.html
   → YES: Proceed to step 3

3. Check: localStorage.getItem('user') has role?
   → NO: Redirect to smtp/login.html
   → YES: Proceed to step 4

4. Switch on user.role:
   root_admin → smtp/dashboard-admin.html
   policy_admin → smtp/dashboard-policy.html
   approver → pages/approver-review.html
   auditor → smtp/dashboard-auditor.html
   user → smtp/dashboard-user.html (default)

5. Dashboard page:
   - Displays user info
   - Shows logout button
   - Validates role matches expected role
   - Redirects unauthorized users back to index.html
```

---

## Key Files to Know

### Entry Points
- `frontend/index.html` - Auth check & role-based routing
- `frontend/smtp/login.html` - Login form with test accounts
- `backend/app/main.py` - FastAPI application

### Authentication
- `backend/app/smtp/routes/auth.py` - Login & register endpoints
- `backend/app/smtp/auth.py` - JWT & password utilities
- `backend/app/smtp/database.py` - MongoDB connection

### Models
- `backend/app/smtp/models.py` - UserRole, UserResponse, etc.

### Dashboards
- `frontend/smtp/dashboard-admin.html` - System admin
- `frontend/smtp/dashboard-policy.html` - Policy admin
- `frontend/pages/approver-review.html` - Approver
- `frontend/smtp/dashboard-auditor.html` - Auditor
- `frontend/smtp/dashboard-user.html` - Regular user

---

## Data Flow

### Login Process
```
Frontend (login form)
    ↓
POST /api/v1/smtp/auth/login
    ↓
Backend (password verification)
    ↓
Generate JWT token
    ↓
Return { access_token, user }
    ↓
Frontend stores in localStorage
    ↓
Redirect to appropriate dashboard
```

### localStorage Keys
```javascript
localStorage.auth_token       // JWT access token
localStorage.user             // JSON user object with role
```

### User Object Structure
```json
{
  "email": "admin@test.com",
  "nickname": "관리자",
  "department": "관리부",
  "team_name": null,
  "role": "root_admin",
  "created_at": "2025-11-06T17:58:16.440000",
  "updated_at": "2025-11-06T17:58:16.440000"
}
```

---

## Debugging Tips

### Check Browser Console
```javascript
// In browser DevTools console:
localStorage.getItem('auth_token')    // Should show JWT
JSON.parse(localStorage.getItem('user')) // Should show user object
```

### Check Backend Logs
```
Look for:
- "✅ MongoDB 연결 완료"
- "INFO: Uvicorn running on 0.0.0.0:8000"
- No error messages on startup
```

### API Testing
```bash
# See all users in database
curl http://127.0.0.1:8000/api/v1/smtp/users

# Test invalid login
curl -X POST http://127.0.0.1:8000/api/v1/smtp/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"wrong@email.com","password":"wrong"}'

# Expected error: {"detail":"이메일 또는 비밀번호가 올바르지 않습니다"}
```

---

## Common Issues

### "No auth token found, redirecting to login"
- **Cause**: localStorage is empty or browser in private mode
- **Fix**: Clear cache, reload, login again

### "Cannot POST /api/v1/smtp/auth/login"
- **Cause**: Backend not running or API_BASE_URL wrong
- **Fix**: Start backend with `python -m uvicorn app.main:app --reload`

### "Failed to load resource: the server responded with a status of 401"
- **Cause**: Token invalid or expired
- **Fix**: Logout and login again

### Dashboard shows "권한이 없습니다"
- **Cause**: User role doesn't match dashboard requirement
- **Fix**: Login with correct test account for that role

### MongoDB connection timeout
- **Cause**: No internet or IP not whitelisted
- **Fix**: Check MongoDB Atlas console > Network Access

---

## Next Steps

1. ✅ **Test all 5 roles** with provided test accounts
2. ✅ **Verify each dashboard** loads correctly
3. ✅ **Test logout** functionality
4. ✅ **Create new test user** via registration
5. ✅ **Check API docs** at http://localhost:8000/docs
6. → **Implement dashboard features** as needed
7. → **Add role-based backend restrictions**
8. → **Deploy to production** (update CORS, SECRET_KEY, etc.)

---

## Useful Resources

- **FastAPI Docs**: http://localhost:8000/docs (Swagger UI)
- **FastAPI Guide**: https://fastapi.tiangolo.com/
- **MongoDB Atlas**: https://www.mongodb.com/cloud/atlas
- **JWT Tokens**: https://jwt.io/

---

**Version**: 2.0.0
**Last Updated**: November 7, 2025
**Status**: ✅ Ready for Development
