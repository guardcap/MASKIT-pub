# Enterprise GuardCAP - Authentication & Role-Based Routing Setup

## Overview
This document describes the complete authentication system and role-based dashboard routing for Enterprise GuardCAP.

## System Architecture

### Authentication Flow
```
User → Login Page (smtp/login.html)
  ↓
  Login API (/api/v1/smtp/auth/login)
  ↓
  Redirect to index.html
  ↓
  Auth Check & Role-Based Routing
  ↓
  Role-Specific Dashboard
```

### Role Structure
The system supports 5 user roles with different permissions and dashboards:

| Role | Description | Dashboard | Database Value |
|------|-------------|-----------|-----------------|
| **System Admin** | System-wide settings and user management | System Settings Page | `root_admin` |
| **Policy Admin** | DLP policy and entity management | Policy Settings Page | `policy_admin` |
| **Approver** | Email approval/rejection workflow | Approval Dashboard | `approver` |
| **Auditor** | Read-only access to all logs and statistics | Audit Dashboard | `auditor` |
| **Regular User** | Send emails subject to DLP policies | Mail List | `user` |

## Test Accounts

All test accounts are pre-configured in MongoDB and ready to use:

```
┌──────────────────────┬─────────────┬──────────────┬─────────────────────────┐
│ Email                │ Password    │ Role         │ Dashboard               │
├──────────────────────┼─────────────┼──────────────┼─────────────────────────┤
│ admin@test.com       │ admin123    │ root_admin   │ smtp/dashboard-admin    │
│ policy@test.com      │ policy123   │ policy_admin │ smtp/dashboard-policy   │
│ approver@test.com    │ approver123 │ approver     │ pages/approver-review   │
│ auditor@test.com     │ auditor123  │ auditor      │ smtp/dashboard-auditor  │
│ user@test.com        │ user123     │ user         │ smtp/dashboard-user     │
└──────────────────────┴─────────────┴──────────────┴─────────────────────────┘
```

## Frontend Architecture

### Key Files

#### 1. **index.html** - Entry Point & Auth Router
- **Location**: `frontend/index.html`
- **Purpose**: Main entry point that checks authentication and routes to appropriate dashboard
- **Flow**:
  ```javascript
  if (!auth_token || !user) {
    redirect to smtp/login.html
  } else {
    switch(user.role) {
      case 'root_admin': → smtp/dashboard-admin.html
      case 'policy_admin': → smtp/dashboard-policy.html
      case 'approver': → pages/approver-review.html
      case 'auditor': → smtp/dashboard-auditor.html
      default: → smtp/dashboard-user.html
    }
  }
  ```

#### 2. **smtp/login.html** - Login & Test Account Selection
- **Location**: `frontend/smtp/login.html`
- **Features**:
  - Standard login form (email + password)
  - 5 quick-login buttons for test accounts
  - Responsive grid layout
  - Auto-fill and submit on test account button click
- **Function**: `quickLogin(email, password)` - Auto-fills credentials and submits form

#### 3. **Dashboard Pages** - Role-Specific Views
All dashboard pages include:
- **Auth Check**: Verifies `auth_token` and `user.role` on page load
- **User Info Display**: Shows user's nickname and email
- **Logout Button**: Clears localStorage and redirects to login
- **Role Validation**: Redirects unauthorized users back to index.html

**Dashboard Files**:
- `frontend/smtp/dashboard-admin.html` - System admin dashboard
- `frontend/smtp/dashboard-policy.html` - Policy admin dashboard
- `frontend/pages/approver-review.html` - Approver dashboard
- `frontend/smtp/dashboard-auditor.html` - Auditor dashboard
- `frontend/smtp/dashboard-user.html` - User mail list dashboard

### Authentication Flow Details

#### Step 1: User Lands on index.html
```javascript
const token = localStorage.getItem('auth_token');
const user = JSON.parse(localStorage.getItem('user') || 'null');

if (!token || !user) {
  // No credentials found
  window.location.href = 'smtp/login.html';
}
```

#### Step 2: User Logs In
**Manual Login**:
```javascript
POST /api/v1/smtp/auth/login
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Quick Login** (Test Accounts):
- User clicks a test account button
- `quickLogin(email, password)` called
- Email and password auto-filled
- Form auto-submitted

#### Step 3: Backend Validates & Returns Token
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "email": "admin@test.com",
    "nickname": "관리자",
    "role": "root_admin",
    "created_at": "2025-11-06T17:58:16.440000",
    "updated_at": "2025-11-06T17:58:16.440000"
  }
}
```

#### Step 4: Frontend Stores Credentials
```javascript
localStorage.setItem('auth_token', data.access_token);
localStorage.setItem('user', JSON.stringify(data.user));
```

#### Step 5: Redirect to Appropriate Dashboard
```javascript
switch(user.role) {
  case 'root_admin':
    window.location.href = 'smtp/dashboard-admin.html';
    break;
  // ... other roles ...
}
```

## Backend Architecture

### API Endpoints

#### Authentication Endpoints
```
POST /api/v1/smtp/auth/login
  Input: { email: EmailStr, password: str }
  Output: { access_token: str, token_type: str, user: UserResponse }

POST /api/v1/smtp/auth/register
  Input: { email: EmailStr, password: str, nickname: str, ... }
  Output: UserResponse

GET /api/v1/smtp/users
  Headers: { Authorization: "Bearer <token>" }
  Output: List[UserResponse]
```

### Database Models

#### UserRole Enum
```python
class UserRole(str, Enum):
    ROOT_ADMIN = "root_admin"      # System admin
    POLICY_ADMIN = "policy_admin"  # Policy manager
    AUDITOR = "auditor"            # Audit read-only
    APPROVER = "approver"          # Email approver
    USER = "user"                  # Regular user
```

#### User Model
```python
class UserResponse(BaseModel):
    email: EmailStr
    nickname: str
    department: Optional[str]
    team_name: Optional[str]
    role: UserRole
    created_at: datetime
    updated_at: datetime
```

### MongoDB Collections
- **Collection**: `users`
- **Indexes**: `email` (unique), `created_at`
- **Fields**: email, nickname, department, team_name, role, hashed_password, created_at, updated_at

## LocalStorage Keys

The frontend uses localStorage to persist authentication data:

```javascript
// Authentication Token (JWT)
localStorage.getItem('auth_token')

// User Object (JSON)
localStorage.getItem('user')
// Structure:
{
  "email": "user@test.com",
  "nickname": "일반사용자",
  "department": "마케팅팀",
  "team_name": null,
  "role": "user",
  "created_at": "2025-11-06T17:58:17.368000",
  "updated_at": "2025-11-06T17:58:17.368000"
}
```

## Environment Configuration

### Backend (.env)
```env
# API Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# MongoDB
MONGODB_URI=mongodb+srv://maskit:***@cluster0.bpbrvcu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
DATABASE_NAME=maskit

# JWT/Security
SECRET_KEY=your-secret-key-here-minimum-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### Frontend (.env)
```env
# API Base URL
REACT_APP_API_URL=http://127.0.0.1:8000
```

## Testing Guide

### Quick Start
1. **Start Backend**:
   ```bash
   cd /Users/6kiity/Documents/enterprise-guardcap
   source venv/bin/activate
   cd backend
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

2. **Open Frontend**:
   - Navigate to `frontend/index.html` in browser or
   - Run `npm start` in `frontend/` directory to launch Electron app

3. **Test Login** (Multiple Options):
   - **Option A**: Use test account quick-login buttons on login page
   - **Option B**: Manually enter test account credentials
   - **Option C**: Create new account via registration page

### Testing Each Role

#### 1. System Admin (root_admin)
```
Email: admin@test.com
Password: admin123
Dashboard: System Settings Page
```

#### 2. Policy Admin (policy_admin)
```
Email: policy@test.com
Password: policy123
Dashboard: Policy Settings Page
```

#### 3. Approver (approver)
```
Email: approver@test.com
Password: approver123
Dashboard: Email Approval Dashboard
```

#### 4. Auditor (auditor)
```
Email: auditor@test.com
Password: auditor123
Dashboard: Audit Dashboard (Read-Only)
```

#### 5. Regular User (user)
```
Email: user@test.com
Password: user123
Dashboard: Mail List
```

### API Testing with curl

**Test Login**:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/smtp/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"admin123"}'
```

**Register New User**:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/smtp/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email":"newuser@test.com",
    "password":"password123",
    "nickname":"New User",
    "department":"IT",
    "role":"user"
  }'
```

## Security Considerations

### Password Security
- Passwords hashed with bcrypt (12 rounds)
- Stored as `hashed_password` in MongoDB
- Never transmitted in plain text over HTTPS

### Token Security
- JWT tokens signed with HS256 algorithm
- Tokens stored in localStorage (accessible to JavaScript)
- For production, consider HttpOnly cookies for better security
- Token expiration: 1440 minutes (24 hours) by default

### CORS Configuration
- Currently allows all origins: `allow_origins=["*"]`
- For production, restrict to specific domains

### Role-Based Access Control
- Each dashboard page validates user role on load
- Unauthorized access redirects to index.html
- Backend API endpoints should also validate user roles

## Common Issues & Solutions

### Issue: "No auth token found" on every page reload
**Solution**: Check that `localStorage.setItem()` is called after successful login

### Issue: Dashboard loads but shows wrong user's data
**Solution**: Verify that `user` object is properly stored with `JSON.stringify()`

### Issue: Token expires mid-session
**Solution**: Implement token refresh endpoint at `/api/v1/smtp/auth/refresh`

### Issue: Login button doesn't work
**Solution**:
1. Check API_BASE_URL matches actual backend server
2. Verify CORS is enabled on backend
3. Check browser console for error messages

## Future Enhancements

- [ ] Token refresh endpoint implementation
- [ ] HttpOnly cookie-based token storage (security)
- [ ] Two-factor authentication
- [ ] Role-based API endpoint protection
- [ ] Session timeout with warning
- [ ] Activity logging and audit trail
- [ ] Password reset functionality
- [ ] Account lockout after failed login attempts

## References

- **Backend API Docs**: `http://localhost:8000/docs`
- **Models**: `backend/app/smtp/models.py`
- **Auth Routes**: `backend/app/smtp/routes/auth.py`
- **Database**: `backend/app/smtp/database.py`

---

**Last Updated**: November 7, 2025
**Status**: ✓ Complete and Tested
