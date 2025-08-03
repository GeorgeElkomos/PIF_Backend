# SubmitIQ Backend API

A security-first Django REST API project with role-based authentication and approval workflow.

## Features

- 🔐 **JWT Authentication** with token rotation and blacklisting
- 👥 **Role-based Access Control** (Administrator/Company)
- ✅ **User Approval Workflow** (Pending/Accepted/Rejected)
- 🛡️ **Security-first Design** with comprehensive validation
- 📚 **API Documentation** with Swagger/ReDoc
- 🏗️ **Clean Architecture** with Repository and Service patterns

## User Roles

### Administrator
- **Username**: `PIF_SubmitIQ`
- **Email**: `PIF_SubmitIQ@PIF.com`
- **Password**: `PIF_SubmitIQ123`
- **Permissions**: Can approve/reject Company registrations

### Company
- Self-registration with automatic "Pending" status
- Requires Administrator approval to access the system

## API Endpoints

### Authentication
- `POST /api/v1/auth/register/` - Company registration
- `POST /api/v1/auth/login/` - User login
- `POST /api/v1/auth/logout/` - User logout
- `POST /api/v1/auth/token/refresh/` - Refresh access token

### User Profile
- `GET /api/v1/auth/profile/` - Get user profile
- `PATCH /api/v1/auth/profile/` - Update user profile
- `POST /api/v1/auth/profile/change-password/` - Change password

### Documentation
- `/api/docs/` - Swagger UI
- `/api/redoc/` - ReDoc
- `/api/schema/` - OpenAPI Schema

## Security Features

### Password Requirements
- Minimum 12 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

### JWT Configuration
- **Access Token Lifetime**: 7 minutes
- **Refresh Token Lifetime**: 4 hours
- **Token Rotation**: Enabled
- **Token Blacklisting**: Enabled

### Rate Limiting
- **Anonymous users**: 100 requests/hour
- **Authenticated users**: 1000 requests/hour

## Quick Start

### 1. Activate Virtual Environment
```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Setup
Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

### 4. Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Administrator
```bash
python manage.py create_admin
```

### 6. Run Server
```bash
python manage.py runserver
```

### 7. Access API Documentation
- Visit: http://localhost:8000/api/docs/

## Project Structure

```
submitiq/
├── authentication/          # User authentication & management
│   ├── models.py           # Custom User model
│   ├── serializers.py      # API serializers
│   ├── views.py            # API views
│   ├── services/           # Business logic layer
│   └── repositories/       # Data access layer
├── dashboard/              # Dashboard functionality
├── common/                 # Shared utilities
├── submitiq/
│   ├── settings/          # Environment-specific settings
│   │   ├── base.py       # Base configuration
│   │   ├── local.py      # Development settings
│   │   └── production.py # Production settings
│   └── urls.py           # URL routing
├── logs/                  # Application logs
├── static/               # Static files
├── media/                # Media uploads
└── templates/            # HTML templates
```

## User Registration Flow

1. **Company Registration**
   - Company submits registration form
   - Account created with "Pending" status
   - Account is inactive until approved

2. **Administrator Approval**
   - Administrator logs in
   - Reviews pending registrations
   - Approves or rejects applications

3. **Company Access**
   - Approved companies can log in
   - Rejected companies cannot access system

## Development Guidelines

### Security Best Practices
- All passwords are validated for strength
- JWT tokens have short lifetimes
- Failed authentication attempts are logged
- Rate limiting prevents brute force attacks
- Input validation on all endpoints

### Code Organization
- **Models**: Database schema and business entities
- **Serializers**: Input validation and data transformation
- **Views**: API endpoints (thin layer)
- **Services**: Business logic and workflows
- **Repositories**: Data access and queries

## Environment Variables

```bash
# Django Core
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3

# JWT Settings
ACCESS_TOKEN_LIFETIME_MINUTES=7
REFRESH_TOKEN_LIFETIME_HOURS=4

# Security
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000

# Rate Limiting
THROTTLE_ANON_RATE=100/hour
THROTTLE_USER_RATE=1000/hour

# Logging
LOG_LEVEL=INFO
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=authentication

# Run specific test
pytest authentication/tests/test_authentication.py
```

## Production Deployment

1. Set `DEBUG=False` in environment
2. Configure production database
3. Set up proper CORS origins
4. Enable SSL/HTTPS
5. Configure logging
6. Set up monitoring

## Support

For questions or issues, please refer to the project documentation or contact the development team.
