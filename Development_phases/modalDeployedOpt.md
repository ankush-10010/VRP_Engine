# 🚚 VRP Optimization Suite: Modal Serverless Architecture

This document serves as the master record of the VRP (Vehicle Routing Problem) project's evolution. It details the journey from a local data science prototype to a production-grade, serverless web application deployed on Modal.

---

## 🏗️ Architectural Evolution

### Phase 1: The Local Prototype (Legacy Scripts)
* **Architecture:** A sequence of sequential Python scripts (`dataset_prep.py` -> `geodata.py` -> `build_matrix.py` -> `run_solver.py`).
* **State Management:** Wrote intermediary outputs (CSVs, JSONs) to the local hard drive.
* **Limitations:** Highly manual, blocking CPU execution, single-user only, required the user to have Python and dependencies installed locally.

### Phase 2: The Distributed Microservices App (Docker + Celery)
* **Architecture:** A FastAPI backend, Redis message broker, Celery background worker, and PostGIS database, all orchestrated via `docker-compose`.
* **Improvement:** Introduced asynchronous processing. The heavy Google Maps API calls and OR-Tools math were pushed to a background worker, preventing the web browser from experiencing Gateway Timeouts.
* **Limitations:** Required managing heavy infrastructure (Redis, Database, Workers) 24/7, incurring costs and maintenance overhead.

### Phase 3: The Serverless Cloud (Current - Modal Deployment)
* **Architecture:** A fully stateless, serverless application deployed on Modal. Modal wraps the FastAPI application and provides instant horizontal scaling for background tasks.
* **Improvement:** 
  * **Zero Infrastructure:** Deleted Docker, Celery, and Redis.
  * **Statelessness:** Removed local PostgreSQL dependencies. The pipeline is pure compute: Data In -> Optimized Routes Out.
  * **Infinite Scale:** Modal automatically spins up cloud GPUs/CPUs to handle simultaneous user requests and spins them down immediately after, ensuring high performance at minimal cost.

---

## ✨ Current Features & Capabilities

### 1. Advanced OOP Solver Engine
The routing logic was completely refactored from functional scripts into a robust, object-oriented software library (`app/core_engine/solvers/`).
* **The Strategy Pattern (`BaseVRPSolver`):** An abstract base class enforcing a strict `solve()` interface for all routing algorithms.
* **The Factory Pattern (`SolverFactory`):** Allows the backend to dynamically instantiate and swap algorithms at runtime based on the user's frontend request.
* **Available Solvers:**
  * **`ORToolsSolver`:** Utilizes Google OR-Tools for industry-standard, constraint-based VRP optimization.
  * **`ALNSSolver`:** A custom heuristic implementation using Adaptive Large Neighborhood Search with greedy repair and random destroy operators.

### 2. Streamlined API Endpoints
The backend was cleaned up to expose only the necessary endpoints for a polling-based frontend integration:
1. `POST /api/v1/simulation/upload-csv`: The main entrypoint. Accepts a CSV file, spawns the massive 4-step pipeline (Parse -> Geocode -> Matrix -> Solve) in the Modal cloud, and returns a unique `task_id`.
2. `GET /api/v1/matrix-status/{task_id}`: The frontend polling endpoint. Securely checks the Modal `FunctionCall` status without blocking the server, returning the massive JSON route payload only when the math is 100% complete.
3. `POST /api/v1/geocode`: A synchronous utility endpoint.

### 3. Comprehensive Analytical Payload
The backend now returns a rich JSON response designed to feed a highly interactive React dashboard:
* **`routes`:** Detailed step-by-step coordinates, ETAs, and departure times for every vehicle.
* **`analytics`:** High-level KPIs (Fleet utilization %, success rate, total distance).
* **`optimization_log`:** A turn-by-turn log comparing the cost performance of OR-Tools vs. ALNS, designed to be plotted on a line chart.
* **`events`:** A chronological simulation timeline of how orders arrived, succeeded, or failed.

---

## 🚀 How to Run the Project

Since the project is now serverless and stateless, running it is incredibly simple.

**1. Install Modal**
```bash
pip install modal
```

**2. Authenticate (First time only)**
```bash
modal setup
```

**3. Serve the Application**
Navigate to the `Optimization` directory and run:
```bash
modal serve modal_app.py
```

Modal will build the cloud image, attach your Google Maps API key, and provide you with a live `https://...modal.run` URL. You can plug this URL directly into your React frontend to test the full pipeline over the internet.