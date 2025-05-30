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
poetry install         # or pip install -r requirements.txt
poetry run uvicorn main:app --reload
```
