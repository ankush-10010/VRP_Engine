# 🚀 How to Run the Delivery Optimization App

You can run this application in two ways:
1. **Using Docker (Recommended)** - Easiest for getting everything up and running.
2. **Running Locally** - Best for development if you want to run services individually.

---

## ✅ Option 1: Using Docker (Recommended)

This sets up the **Backend**, **Database**, **Redis**, and **Worker** automatically.

### 1. Start the Backend Services
Run the following command in your terminal (root directory):
```bash
docker-compose up --build
```
This will start:
- Backend API (Port 8000)
- Celery Worker
- Redis
- PostgreSQL Database

### 2. Start the Frontend
The frontend is not in the docker-compose setup, so you need to run it manually.

Open a **new terminal** window:
```bash
cd frontend
npm install
npm run dev
```

### 3. Access the App
- **Frontend UI:** [http://localhost:5173](http://localhost:5173) (or 5174 if 5173 is taken)
- **Backend Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🛠️ Option 2: Running Locally (Manual Setup)

If you prefer to run things without Docker (or just want to use the `.bat` files), follow these steps.

### Prerequisites
- **Python 3.8+** installed
- **Redis** running locally (required for the worker)
- **Node.js** installed (for frontend)

### 1. Setup Backend
1. **Install Dependencies**
   Run:
   ```cmd
   install_deps.bat
   ```

2. **Start the Server**
   Run:
   ```cmd
   run_server.bat
   ```
   Server runs on: http://localhost:8000

3. **Start the Worker**
   Make sure Redis is running first! Then run:
   ```cmd
   run_worker.bat
   ```

### 2. Setup Frontend
1. Open a terminal in the `frontend` folder.
2. Run:
   ```bash
   npm install
   npm run dev
   ```

---

## 🔑 Environment Variables
Make sure you have a `.env` file in the root directory.

### For Docker (Recommended Default)
You usually don't need to change much, as Docker handles the networking.
```env
GOOGLE_MAPS_API_KEY=your_key_here
DATABASE_URL=postgresql://postgres:postgres@db:5432/optimization_db
# Docker uses internal hostnames 'redis' and 'db'
```

### For Local Execution (Important!)
If running `run_worker.bat` locally, you MUST update your `.env` to point to `localhost` instead of `redis`.
```env
# ... other keys ...
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```
*Configuring this incorrectly causes the "Error 11001 connecting to redis" you might see.*

## ❓ Troubleshooting
**"Cannot connect to redis... Error 11001"**
- This means your worker is trying to find a computer named "redis" but fails.
- **Fix:** If running locally, set `CELERY_BROKER_URL=redis://localhost:6379/0` in your `.env`.
- **Fix:** If running Docker, make sure the `redis` container is actually running (`docker ps`).

**How to check if Redis is running?**
- **Docker:** Run `docker ps` in a terminal. Look for `optimization_redis`.
- **Local:** Attempt to connecting using a CLI tool or check your Docker Desktop dashboard if you started it via `docker run`.

