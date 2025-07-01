# Global Policy Tracker

A full-stack web application for tracking, submitting, and managing global policy data.  
Live Demo: [https://policy-tracker-f.onrender.com/](https://policy-tracker-f.onrender.com/)

---

## Project Structure

---

## Features

- **Policy Submission:** Users can submit new policy data and upload supporting files.
- **Admin Panel:** Admins can review, approve, or reject policy submissions.
- **CSV Export:** Download policy data as CSV.
- **Theming:** Switch between different UI themes.
- **Responsive UI:** Built with Next.js and modern CSS.

---

## Installation

### Prerequisites

- [Node.js](https://nodejs.org/) (v16+ recommended)
- [Python](https://www.python.org/) (v3.10+ recommended)
- [Poetry](https://python-poetry.org/) (for backend dependency management)

### Backend Setup

```sh
cd backend
<<<<<<< HEAD
poetry install         # or pip install -r requirements.txt
poetry run uvicorn main:app --reload
=======
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
>>>>>>> 6e97e192b086c174d8e38447457a9a201c718aa2
```
