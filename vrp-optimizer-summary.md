# VRP Optimizer — Comprehensive Context & Architecture Summary

*This document aggregates the full architectural context from the Gemini Vault and the complete structural survey of the codebase.*

## 1. Project Identity & Architecture Summary

- **Name:** Real-Time Vehicle Routing Engine (VRP Optimizer)
- **Stack:** FastAPI (Python) + React/TypeScript + Modal (Serverless) + Google Maps API
- **Repository:** GitHub — `ankush-10010/VRP_Engine`
- **Live URLs:**
  - Frontend: `https://vrp-engine.vercel.app`
  - Backend: `https://ankushraj10010--vrp-optimizer-fastapi-modal-wrapper.modal.run`

**Workflow Summary:**
1. The user uploads a CSV of delivery orders through the React frontend
2. The frontend sends this via HTTP POST to a FastAPI endpoint hosted on Modal
3. Modal spawns a background task (`modal_simulation_task.spawn`) to run the heavy computation
4. The frontend connects via **WebSocket** to receive live progress updates
5. The simulation engine processes orders in a time-stepped loop

---

## 2. Solver Hierarchy (3-Layer)

1. **Layer 1 — Greedy Assignment:** Immediate, assigns orders to nearest available vehicle
2. **Layer 2 — OR-Tools (Batch):** Google's constraint-programming solver, runs every `layer_2_interval` seconds (default 1800s simulation time). Solves the full CVRP optimally within a timeout
3. **Layer 3 — ALNS (Metaheuristic):** Adaptive Large Neighborhood Search. Runs after OR-Tools. Uses destroy/repair operators with simulated annealing acceptance. Streams intermediate improvements via `progress_callback`

---

## 3. Key Technical Details

- **Distance Matrix:** Pre-calculated using Google Maps Distance Matrix API and stored in a database. Avoids O(N²) API calls per run
- **Matrix Modes:** `database` (pre-calculated), `api` (live Google Maps), `custom` (user-provided)
- **Cost Model:** `fixed_cost_per_truck × active_trucks + variable_cost_per_km × total_distance`
- **WebSocket Architecture:**
  - HTTP POST for CSV upload → returns `task_id` and `job_id`
  - Frontend opens WSS connection to `/api/v1/simulation/ws/{job_id}/{task_id}`
  - Backend streams `progress` messages with routes, costs, analytics, and optimization_log
  - Backend sends `complete` message with final results
  - **Auto-reconnect** on frontend handles Modal's 300-second connection timeout
  - Server-side **heartbeat pings** every 5 seconds during blocking OR-Tools calls

---

## 4. Frontend Architecture

- **States:** IDLE → POLLING → STREAMING → COMPLETED (or ERROR)
- **Key Components:**
  - `LandingPage` — CSV upload, algorithm selection, hyperparameter config
  - `LoadingScreen` — Shown during initial Modal container boot
  - `ResultsDashboard` — Google Maps visualization, route details, analytics
  - `OptimizationChart` — Chart.js / Recharts line graph showing L2 vs L3 convergence
- **Default Config:** ALNS strategy, 1800s interval, 500 iterations, 50-90% destroy bounds

---

## 5. Deployment & Constraints

- **Backend:** `modal deploy modal_app.py` — deploys to Modal cloud
- **Frontend:** Vercel (auto-deploys from GitHub)
- **CI/CD:** GitHub Actions pipeline with pytest + vitest + ESLint
- **Known Constraints:**
  - Modal enforces 300-second WebSocket timeout (handled by auto-reconnect)
  - OR-Tools blocks the Python event loop during solving (handled by heartbeat pings)
  - Single Modal worker is single-threaded; no concurrent Python execution during C++ OR-Tools calls

---

## 6. Project Directory Tree

### Top-Level Files
- `.github/workflows/CI-CD-basicSyntax.yml` — CI/CD pipeline
- `.gitnexus/` — GitNexus code intelligence index
- `AGENTS.md` — GitNexus agent instructions
- `further_improving_plan.md` — Production roadmap
- `modal_app.py` — Modal serverless deployment entry point
- `requirements.txt` — Python dependencies
- `vercel.json` — Vercel deployment config

### `app/` Structure (Backend)
- `api/endpoints.py` — FastAPI routes + WebSocket handler
- `core_engine/solvers/`
  - `alns_solver.py` — ALNS metaheuristic implementation
  - `base.py` — Abstract solver base class
  - `ortools_solver.py` — Google OR-Tools CVRP solver
- `models/schemas.py` — Pydantic models
- `services/`
  - `simulation.py` — Hybrid simulation engine (core orchestration)
  - `solver.py` — Cost/distance/time calculation utilities

### `frontend/src/` Structure (React)
- `api/api.ts` — API client + types
- `components/`
  - `LandingPage.tsx` — CSV upload + config UI
  - `LoadingScreen.tsx` — Loading animation
  - `OptimizationChart.tsx` — Convergence graph
  - `ResultsDashboard.tsx` — Main results dashboard with Google Maps
- `App.tsx` — Root component + WebSocket logic
- `index.css` — Global styles (Material Design 3 theme)
- `main.tsx` — Vite entry point

---

## 7. Detailed File Summaries

### `modal_app.py`
The Modal serverless deployment entry point. 
- `app = modal.App("vrp-optimizer")`
- `progress_dict = modal.Dict.from_name("vrp-progress", create_if_missing=True)` for cross-container progress streaming
- `modal_simulation_task` parses CSV, builds matrices, and calls `run_hybrid_simulation()`
- `fastapi_modal_wrapper` serves the FastAPI app

### `app/api/endpoints.py`
- `POST /simulation/upload-csv`: Spawns background task asynchronously using `.spawn.aio()`
- `WebSocket /simulation/ws/{job_id}/{task_id}`: Polls `progress_dict` every 0.5s, sends `ping` heartbeats every 5s, streams progress, handles disconnects gracefully.

### `app/services/simulation.py`
The core hybrid simulation engine `run_hybrid_simulation()`.
- Runs time-stepped loop in 1-minute increments
- Manages L1 (Greedy), L2 (OR-Tools batch), and L3 (ALNS)
- Includes `on_progress` callback that appends to `optimization_log` and writes to `progress_dict` for WS streaming.

### `app/core_engine/solvers/alns_solver.py`
Main ALNS loop running default 500 iterations.
- Uses `_destroy_random()` (removes 50-90% of orders) and `_repair_greedy()` (inserts based on min distance).
- Uses Simulated Annealing (temp=1000, cooling=0.995).

### `app/core_engine/solvers/ortools_solver.py`
Creates a routing model using `ortools.constraint_solver`.
- Enforces demand limits and a soft upper bound of 200 minutes per vehicle.
- Solves using `PARALLEL_CHEAPEST_INSERTION`.

### `frontend/src/App.tsx`
Root React component state machine: `IDLE → POLLING → STREAMING → COMPLETED | ERROR`.
- Manages `useEffect` WebSocket logic including the automatic reconnection fallback (2-second wait on close).

### `frontend/src/components/LandingPage.tsx`
Rich Material Design 3 config UI for strategy selection, fleet settings, advanced hyperparameters, and matrix mode.

### `frontend/src/components/ResultsDashboard.tsx`
Full results UI with KPI Ribbon, interactive Google Maps (`ResultsMap`), expandable route details table, Event timeline, and Export JSON feature.

### `frontend/src/components/OptimizationChart.tsx`
Graph showing L2 vs L3 convergence, dynamically filtering empty data to properly scale the axes.

### `.github/workflows/ci.yml`
Pipeline triggered on main branches. Runs `backend-ci` (Python 3.11, pytest, flake8), `frontend-ci` (Node 20, npm run build), `docker-build`, and `deploy-modal`.
