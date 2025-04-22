# **Policy Tracker: Full Stack Application**

A full-stack system that tracks AI and digital policies across different countries. The backend is built using **FastAPI** with **MongoDB** as the database, and the frontend is developed using **Next.js**. The application offers a RESTful API to interact with policy data, and it visualizes the data with an interactive world map.

---

## 🏗️ **Project Setup and Installation**

This guide will help you set up both the **Backend** and **Frontend** sections of the project.

---

### 📂 **Project Structure**

```
policy-tracker/
│
├── backend/                  # FastAPI Backend
│   ├── main.py               # FastAPI application
│   ├── requirements.txt      # Python dependencies
│   ├── venv/                 # Virtual environment
│   └── .env                  # Environment variables
│
└── frontend/                 # Next.js Frontend
    ├── pages/                # React pages
    ├── components/           # React components
    ├── public/               # Static assets
    ├── package.json          # Node.js dependencies
    └── .env.local            # Frontend environment variables
```

---

## **1️⃣ Backend Setup (FastAPI + MongoDB)**

### **Prerequisites:**

Make sure you have the following software installed:

- **Python 3.11+** (Download [here](https://www.python.org/downloads/))
- **MongoDB** (Follow the instructions [here](https://www.mongodb.com/docs/manual/installation/))
- **Git** (Download [here](https://git-scm.com/))

### **Install Backend Dependencies:**

1. Clone the repository and navigate to the backend directory:

   ```bash
   git clone https://github.com/your-username/policy-tracker.git
   cd policy-tracker/backend
   ```

2. Set up a Python virtual environment:

   ```bash
   python -m venv venv
   ```

   Activate the virtual environment:

   - **Windows:**

     ```bash
     .\venv\Scripts\Activate
     ```

   - **Mac/Linux:**

     ```bash
     source venv/bin/activate
     ```

3. Install backend dependencies:

   ```bash
   pip install -r requirements.txt
   ```

   If `requirements.txt` is missing, generate it:

   ```bash
   pip freeze > requirements.txt
   ```

4. Set up your environment variables by creating a `.env` file in the `backend/` directory with the following:

   ```env
   MONGO_URI=mongodb://localhost:27017
   SECRET_KEY=your_secret_key
   DEBUG=True
   ```

5. Run the backend server using **Uvicorn**:

   ```bash
   uvicorn main:app --reload
   ```

   The backend should be running at:

   ```
   http://127.0.0.1:8000
   ```

---

## **2️⃣ Frontend Setup (Next.js)**

### **Prerequisites:**

Make sure you have the following installed:

- **Node.js** (Install [here](https://nodejs.org/))
- **Git** (Install [here](https://git-scm.com/))

### **Install Frontend Dependencies:**

1. Navigate to the frontend directory:

   ```bash
   cd policy-tracker/frontend
   ```

2. Install the necessary Node.js dependencies:

   ```bash
   npm install
   ```

3. Set up the frontend environment variables by creating a `.env.local` file in the `frontend/` directory with the following:

   ```env
   NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
   ```

   This points the frontend to the backend server.

4. Run the frontend development server:

   ```bash
   npm run dev
   ```

   The frontend should be running at:

   ```
   http://localhost:3000
   ```

---

## **3️⃣ Running Both Backend and Frontend**

To run both the **backend** and **frontend** simultaneously, follow these steps:

1. **Backend:** Start the FastAPI backend server:

   ```bash
   uvicorn main:app --reload
   ```

2. **Frontend:** Start the Next.js frontend server:

   ```bash
   npm run dev
   ```

Both the backend and frontend should now be running, and you can view the full application by navigating to:

- **Frontend (React + Next.js):** [http://localhost:3000](http://localhost:3000)
- **Backend (FastAPI):** [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🧑‍💻 **Development Workflow**

### **1️⃣ Create a New Branch for Features/Changes**

For any changes, create a new branch:

```bash
git checkout -b feature/my-new-feature
```

### **2️⃣ Commit and Push Changes**

Add, commit, and push your changes:

```bash
git add .
git commit -m "Add new feature"
git push origin feature/my-new-feature
```

### **3️⃣ Create a Pull Request**

Once your feature branch is pushed, open a pull request for review on GitHub.

---

## **API Documentation**

Once the backend is running, you can access the **API documentation** at:

- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🎨 **Frontend Overview**

The frontend provides a user interface to interact with the AI and digital policy data, visualizing it with an interactive world map. You can add, view, and analyze the policy data for various countries. It is built using **React** and **Next.js** for server-side rendering.

---

## 📝 **License**

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 💬 **Contributing**

We welcome contributions! Please feel free to submit issues, pull requests, or suggestions.

---

## 🎉 **Acknowledgements**

- **FastAPI**: A modern, fast (high-performance) web framework for building APIs with Python.
- **Next.js**: A React framework for building server-rendered applications.
- **MongoDB**: A NoSQL database used to store policy data.

---


