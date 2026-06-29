# WorkFinder API

A production-ready job finding platform API built with Django REST Framework, JWT authentication, and featuring AI job matching, real-time chat, admin dashboard, and notification system.

## Features

- **JWT Authentication** (Register, Login, Logout, Token Refresh)
- **AI Job Matching** - Upload resume (PDF/DOCX/TXT) and get intelligent job matches
- **Real-time Chat** - WebSocket-based messaging between employers and job seekers
- **Notification System** - Real-time notifications with read/unread status
- **Admin Dashboard** - Comprehensive admin panel for superusers
- **Advanced Search** - Full-text search with filters and ranking
- **Job Management** - Create, update, delete jobs with rich details
- **Application Tracking** - Track application status with notifications
- **Favorites** - Save jobs for later
- **Reports & Analytics**

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

## API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

## API Endpoints

### Authentication
- `POST /api/auth/register/` - Register a new user
- `POST /api/auth/login/` - Login (obtain tokens)
- `POST /api/auth/logout/` - Logout (blacklist refresh token)
- `POST /api/auth/token/refresh/` - Refresh access token

### Profiles
- `POST /api/create-seeker-profile/` - Create seeker profile
- `POST /api/create-employer-profile/` - Create employer profile

### Jobs & Categories
- `GET /api/jobs/` - List all jobs (with filters)
- `GET /api/jobs/search/?q=query` - Search jobs
- `POST /api/jobs/` - Create a job
- `GET /api/categories/` - List all categories

### AI Matching
- `POST /api/analyze-resume/` - Upload and analyze resume
- `POST /api/match-jobs/` - Get AI job recommendations

### Notifications
- `GET /api/notifications/` - List notifications
- `POST /api/notifications/read-all/` - Mark all as read

### Real-time WebSocket
- `ws/chat/<chat_id>/` - Connect to chat WebSocket
- `ws/notifications/` - Connect to notifications WebSocket

## Admin Dashboard

Access the admin dashboard at `/admin/dashboard/` (Django superuser only).

Features:
- Statistics cards
- Charts and analytics
- User management
- Job management
- Reports

## Security Features

- JWT token authentication
- Password validation (min 10 characters)
- CSRF protection
- XSS protection
- Secure file uploads (max 10MB)
- Rate limiting
- Security headers
- Permission-based access control