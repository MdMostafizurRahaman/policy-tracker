# AI Policy Tracker

A comprehensive platform for tracking AI policies worldwide with an interactive map, policy submission system, and AI-powered chat assistant.

## Project Structure

### Backend (`/backend`)

```
backend/
├── app/                    # Main application directory
│   ├── config/            # Configuration files
│   │   ├── database.py    # Database connection
│   │   └── settings.py    # Application settings
│   ├── models/            # Pydantic models
│   │   ├── user.py        # User-related models
│   │   ├── policy.py      # Policy-related models
│   │   └── chat.py        # Chat-related models
│   ├── routers/           # API routes
│   │   ├── auth.py        # Authentication endpoints
│   │   ├── policies.py    # Policy management endpoints
│   │   ├── chat.py        # Chat/AI assistant endpoints
│   │   └── admin.py       # Admin endpoints
│   ├── services/          # Business logic
│   │   ├── auth_service.py      # Authentication logic
│   │   ├── email_service.py     # Email handling
│   │   └── chatbot_service.py   # AI chatbot logic
│   ├── utils/             # Utility functions
│   │   └── security.py    # Security utilities
│   ├── main.py            # FastAPI application entry point
│   └── requirements.txt   # Python dependencies
└── run.py                 # Backend startup script
```

### Frontend (`/frontend`)

```
frontend/
├── app/                   # Next.js app directory (legacy components)
│   ├── components/        # Legacy UI components
│   ├── admin/            # Admin dashboard
│   ├── chatBot/          # Chat assistant
│   ├── Submission/       # Policy submission
│   ├── layout.tsx        # App layout
│   └── page.js           # Main page
├── src/                  # New structured source code
│   ├── components/       # Reusable components
│   │   ├── auth/         # Authentication components
│   │   ├── ui/           # UI components (Button, Input, etc.)
│   │   ├── chat/         # Chat components
│   │   ├── policy/       # Policy-related components
│   │   └── admin/        # Admin components
│   ├── services/         # API service layers
│   │   └── api.js        # API client and service classes
│   ├── utils/            # Utility functions and constants
│   │   └── constants.js  # App constants and validation
│   └── hooks/            # Custom React hooks
│       └── index.js      # Authentication and utility hooks
├── public/               # Static assets
├── package.json          # Node.js dependencies
└── next.config.ts        # Next.js configuration
```

## Features

### 🔐 Authentication System
- User registration with email verification
- Secure login with JWT tokens
- Password reset functionality
- Google OAuth support (configurable)
- Admin role management

### 🗺️ Interactive World Map
- Visual representation of AI policies by country
- Country-specific policy popups
- Globe view and traditional map view
- Real-time policy data visualization

### 📝 Policy Management
- Submit new AI policies for review
- Search and filter policies
- Admin approval workflow
- Policy categorization and tagging

### 🤖 AI Chat Assistant
- Natural language policy queries
- Smart policy search and recommendations
- Conversation history
- Context-aware responses

### 👨‍💼 Admin Dashboard
- Pending policy reviews
- User management
- System statistics
- Bulk operations

## Getting Started

### Prerequisites
- Node.js (v18 or higher)
- Python (v3.8 or higher)
- MongoDB

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
cd app
pip install -r requirements.txt
```

4. Start the backend:
```bash
python ../run.py
```

Backend will run on: http://localhost:8000

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

Frontend will run on: http://localhost:3000

## Deployment

### Backend Deployment
1. Install dependencies
2. Set environment variables
3. Run with production WSGI server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend Deployment
1. Build the application:
```bash
npm run build
```

2. Start production server:
```bash
npm start
```
