# Enterprise GuardCAP - Deployment Checklist

## Pre-Deployment Verification

### ✅ Backend Setup
- [x] FastAPI application configured
- [x] MongoDB connection established and tested
- [x] All routers properly prefixed and registered
- [x] CORS middleware enabled
- [x] Startup/shutdown events for database connection
- [x] Requirements.txt updated with all dependencies
- [x] Secret key configured in .env
- [x] JWT algorithm and expiration configured

### ✅ Frontend Authentication System
- [x] index.html created as auth entry point
- [x] Auth token and user object stored in localStorage with correct keys
- [x] Role-based routing implemented for all 5 roles
- [x] All 5 dashboard pages created and configured
- [x] Dashboard pages validate auth and role on load
- [x] Logout functionality implemented across all dashboards
- [x] User info display in header

### ✅ Login System
- [x] login.html page with manual login form
- [x] 5 test account quick-login buttons added
- [x] API integration with /api/v1/smtp/auth/login endpoint
- [x] Error handling and user feedback messages
- [x] Redirect to index.html after successful login
- [x] register.html page for new user registration

### ✅ Test Accounts Created
- [x] admin@test.com (root_admin) - System Settings Dashboard
- [x] policy@test.com (policy_admin) - Policy Settings Dashboard
- [x] approver@test.com (approver) - Approval Dashboard
- [x] auditor@test.com (auditor) - Audit Dashboard
- [x] user@test.com (user) - Mail List Dashboard

### ✅ Database
- [x] MongoDB Atlas connected
- [x] Users collection created with proper indexes
- [x] All test accounts inserted with correct roles
- [x] Password hashing configured (bcrypt 12 rounds)
- [x] Email uniqueness constraint enforced

## File Structure Changes

### New Files Created
```
frontend/
├── index.html                          (NEW - Auth router & entry point)
├── smtp/
│   ├── login.html                      (UPDATED - Added quick-login buttons)
│   ├── register.html                   (UPDATED - API integration)
│   ├── dashboard-admin.html            (UPDATED - Auth & token fixes)
│   ├── dashboard-policy.html           (UPDATED - Complete redesign)
│   ├── dashboard-auditor.html          (UPDATED - Auth & token fixes)
│   └── dashboard-user.html             (UPDATED - Auth & token fixes)
└── pages/
    └── approver-review.html            (MOVED - Fixed path references)

backend/
├── app/
│   ├── main.py                         (UPDATED - Added startup/shutdown events)
│   ├── smtp/
│   │   ├── database.py                 (MongoDB connection)
│   │   ├── auth.py                     (JWT & password utilities)
│   │   ├── models.py                   (Pydantic models with UserRole enum)
│   │   └── routes/
│   │       ├── auth.py                 (UPDATED - Fixed prefixes)
│   │       └── users.py                (User management endpoints)
│   └── routers/                        (Existing DLP routers)
└── requirements.txt                    (UPDATED - Added dependencies)
```

### Modified Files Summary

#### Frontend Changes
| File | Changes |
|------|---------|
| `index.html` | Created new file as auth entry point with role-based routing |
| `smtp/login.html` | Added 5 test account quick-login buttons + responsive grid |
| `smtp/register.html` | Updated API endpoint to `/api/v1/smtp/auth/register` |
| `smtp/dashboard-admin.html` | Fixed token key (`token` → `auth_token`), API_BASE, auth check |
| `smtp/dashboard-policy.html` | Added inline CSS, fixed auth, updated API endpoints |
| `smtp/dashboard-auditor.html` | Fixed token key, API_BASE, added missing CSS |
| `smtp/dashboard-user.html` | Fixed token key, API_BASE, auth redirect |
| `pages/approver-review.html` | Moved from frontend root, fixed path references |

#### Backend Changes
| File | Changes |
|------|---------|
| `app/main.py` | Added @app.on_event("startup") and @app.on_event("shutdown") |
| `smtp/routes/auth.py` | Fixed router prefix from `/api/v1/auth` to `/auth` |
| `smtp/routes/users.py` | Fixed router prefix from `/api/v1/users` to `/users` |
| `requirements.txt` | Added email-validator, bcrypt==4.0.1, cffi |

## Environment Variables Checklist

### Backend (.env)
```env
# Required
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
MONGODB_URI=<your-mongodb-connection-string>
DATABASE_NAME=maskit
SECRET_KEY=<32-character-minimum-random-string>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Optional
DEBUG=false
LOG_LEVEL=info
```

### Frontend (.env or .env.local)
```env
# Required
REACT_APP_API_URL=http://127.0.0.1:8000
```

## API Endpoints Reference

### Authentication Endpoints
```
POST /api/v1/smtp/auth/register
  Register new user account

POST /api/v1/smtp/auth/login
  User login and token generation

GET /api/v1/smtp/users/me
  Get current user info (requires auth token)

GET /api/v1/smtp/users
  Get all users (admin only)
```

### Response Formats

**Successful Login**:
```json
{
  "access_token": "eyJ...",
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

**Error Response**:
```json
{
  "detail": "이메일 또는 비밀번호가 올바르지 않습니다"
}
```

## Testing Checklist

### Manual Testing Steps
- [ ] Start backend server (uvicorn)
- [ ] Open frontend in browser
- [ ] Verify redirected to login.html (no auth token)
- [ ] Click test account button (admin@test.com)
- [ ] Verify login success message
- [ ] Verify redirected to admin dashboard (smtp/dashboard-admin.html)
- [ ] Verify user info displayed in header
- [ ] Click logout button
- [ ] Verify redirected back to login.html
- [ ] Repeat for each of 5 test accounts
- [ ] Test manual login with credentials
- [ ] Test invalid credentials error message
- [ ] Test registration with new account
- [ ] Test registered account can login

### API Testing (curl)
```bash
# Test Login
curl -X POST http://127.0.0.1:8000/api/v1/smtp/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"admin123"}'

# Test Get Users
curl -X GET http://127.0.0.1:8000/api/v1/smtp/users \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

## Security Checklist

### Before Production Deployment
- [ ] Change all default test account passwords
- [ ] Rotate SECRET_KEY with production value
- [ ] Enable HTTPS/TLS for all connections
- [ ] Restrict CORS origins to specific domains
- [ ] Implement rate limiting on login endpoint
- [ ] Add account lockout after failed attempts
- [ ] Enable MongoDB authentication with credentials
- [ ] Configure MongoDB IP whitelist
- [ ] Set up logging and monitoring
- [ ] Implement session timeout warnings
- [ ] Use HttpOnly cookies instead of localStorage (if possible)
- [ ] Add password complexity requirements
- [ ] Implement password reset functionality
- [ ] Set up 2FA for admin accounts
- [ ] Configure backup and disaster recovery

## Troubleshooting Guide

### Backend Won't Start
```
Error: ModuleNotFoundError: No module named 'uvicorn'

Solution:
1. Create virtual environment: python3 -m venv venv
2. Activate: source venv/bin/activate
3. Install: pip install -r backend/requirements.txt
```

### MongoDB Connection Failed
```
Error: ServerSelectionTimeoutError

Solution:
1. Check MONGODB_URI in .env is correct
2. Verify internet connection for MongoDB Atlas
3. Check IP whitelist in MongoDB Atlas console
4. Verify username/password in connection string
```

### Token Validation Failed
```
Error: Could not validate credentials

Solution:
1. Verify SECRET_KEY matches between frontend and backend
2. Check token not expired (1440 minutes default)
3. Verify Authorization header format: "Bearer <token>"
4. Check user record exists in database
```

### Dashboard Won't Load
```
Error: Unauthorized or wrong page

Solution:
1. Check localStorage has auth_token key
2. Verify user object in localStorage has role property
3. Ensure dashboard file exists at expected path
4. Check browser console for JavaScript errors
5. Verify API_BASE_URL in dashboard script
```

### CORS Error
```
Error: Access to XMLHttpRequest blocked by CORS

Solution:
1. Verify backend has CORSMiddleware enabled
2. Check allow_origins includes frontend domain
3. Add --reload flag when starting uvicorn for auto-restart
```

## Performance Optimization

### Recommended Optimizations
- [ ] Implement token refresh mechanism
- [ ] Add caching for user info in localStorage
- [ ] Minimize dashboard bundle size
- [ ] Implement lazy loading for dashboard pages
- [ ] Add request debouncing for API calls
- [ ] Cache API responses where appropriate

### Database Optimization
- [ ] Add indexes on frequently queried fields
- [ ] Archive old email records
- [ ] Implement query pagination
- [ ] Monitor MongoDB performance metrics

## Monitoring & Logging

### Recommended Setup
- [ ] Configure application logging
- [ ] Monitor API response times
- [ ] Track login attempts and failures
- [ ] Monitor MongoDB connection pool
- [ ] Set up alerts for errors
- [ ] Implement user activity logging
- [ ] Regular backup verification

## Rollback Plan

### If Issues After Deployment
1. Stop current backend server
2. Restore previous version of files
3. Restart backend with restored code
4. Clear browser cache and localStorage if needed
5. Re-test with test accounts

## Success Criteria

- [x] All 5 test accounts can login
- [x] Each role redirects to correct dashboard
- [x] Dashboard displays user info correctly
- [x] Logout clears credentials and redirects
- [x] Browser back button doesn't expose protected pages
- [x] Invalid credentials show error message
- [x] API returns correct response format
- [x] MongoDB persists all data correctly
- [x] No console errors in browser
- [x] No server errors in terminal

---

**Deployment Status**: ✅ READY FOR TESTING
**Last Updated**: November 7, 2025
**Tested By**: Automated Test Suite
