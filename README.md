<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white" />
  <img src="https://img.shields.io/badge/TypeScript-5.9-3178C6?logo=typescript&logoColor=white" />
  <img src="https://img.shields.io/badge/Modal-Serverless-7C3AED?logo=data:image/svg+xml;base64,&logoColor=white" />
  <img src="https://img.shields.io/badge/OR--Tools-Google-4285F4?logo=google&logoColor=white" />
</p>

# 🚚 Real-Time Vehicle Routing Engine

> A production-grade, serverless delivery routing system that solves the Capacitated Vehicle Routing Problem (CVRP) using a three-layer hybrid optimization architecture — combining Google OR-Tools, Adaptive Large Neighborhood Search (ALNS), and greedy heuristics — with live WebSocket-streamed convergence visualization.

<p align="center">
  <strong>
    <a href="https://vrp-engine.vercel.app">Live Demo</a> · 
    <a href="#architecture">Architecture</a> · 
    <a href="#the-solver-hierarchy">Solver Deep Dive</a> · 
    <a href="#getting-started">Getting Started</a>
  </strong>
</p>

---

## Table of Contents

- [Why This Exists](#why-this-exists)
- [Architecture](#architecture)
- [The Solver Hierarchy](#the-solver-hierarchy)
  - [Layer 1 — Greedy Assignment](#layer-1--greedy-assignment-real-time)
  - [Layer 2 — Google OR-Tools](#layer-2--google-or-tools-batch-optimization)
  - [Layer 3 — ALNS Metaheuristic](#layer-3--alns-metaheuristic)
  - [Strategy Modes](#strategy-modes)
- [WebSocket Streaming Architecture](#websocket-streaming-architecture)
- [Frontend Dashboard](#frontend-dashboard)
- [Cost Model](#cost-model)
- [CI/CD Pipeline](#cicd-pipeline)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Configuration Reference](#configuration-reference)
- [Tech Stack](#tech-stack)

---

## Why This Exists

The Vehicle Routing Problem (VRP) is NP-Hard — there is no known polynomial-time algorithm that can produce an optimal solution as the number of delivery stops grows. In practice, real-world logistics companies face a brutal tradeoff: either spend hours computing a mathematically optimal route, or accept a "good enough" greedy solution and leave money on the table.

This engine eliminates that tradeoff by running **three optimization layers simultaneously**, each operating at a different time horizon:

| Layer | Algorithm | Latency | Purpose |
|-------|-----------|---------|---------|
| **L1** | Greedy + Tabu Search | < 50ms | Instant order assignment as deliveries arrive |
| **L2** | Google OR-Tools (CVRP) | 5–30s | Periodic batch re-optimization using constraint programming |
| **L3** | ALNS with Simulated Annealing | 2–10s | Metaheuristic refinement that escapes local optima |

The system processes a time-stepped simulation of real delivery data (e.g., 500+ orders across Delhi NCR), streaming algorithmic convergence metrics to a React dashboard over WebSockets in real time.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER'S BROWSER                                │
│                                                                         │
│   ┌─────────────┐     HTTP POST         ┌───────────────────────┐      │
│   │  Landing     │ ───────────────────►  │  FastAPI Endpoint     │      │
│   │  Page (CSV   │   (CSV + Config)      │  /upload-csv          │      │
│   │  Upload)     │                       │  Returns: task_id,    │      │
│   └─────────────┘                       │           job_id      │      │
│          │                               └───────────┬───────────┘      │
│          │                                           │                  │
│          ▼                                           │ .spawn.aio()     │
│   ┌─────────────┐     WebSocket (wss)               ▼                  │
│   │  Results     │ ◄─────────────────    ┌───────────────────────┐      │
│   │  Dashboard   │   Live Progress       │  Modal Cloud Worker   │      │
│   │  (Maps,      │   Streams             │  ┌─────────────────┐ │      │
│   │   Charts,    │                       │  │ Hybrid Sim Loop  │ │      │
│   │   KPIs)      │                       │  │                  │ │      │
│   └─────────────┘                       │  │  L1 → L2 → L3   │ │      │
│                                          │  │  ↓               │ │      │
│                                          │  │  progress_dict   │ │      │
│                                          │  └─────────────────┘ │      │
│                                          └───────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────┘
```

**Data flow:**

1. The user uploads a CSV of delivery orders through the React frontend
2. The frontend sends an HTTP POST to the FastAPI endpoint hosted on Modal
3. Modal spawns an asynchronous background task (`modal_simulation_task`) to run the heavy computation
4. The frontend opens a WebSocket connection to receive live progress
5. As each solver finds improvements, the backend writes to a shared `modal.Dict` — the WebSocket handler polls this dict and streams updates to the browser
6. The dashboard renders live route updates on Google Maps, real-time convergence graphs, and operational KPIs

---

## The Solver Hierarchy

The simulation engine orchestrates three solver layers in a time-stepped loop. Orders arrive minute-by-minute (simulating real-world delivery dynamics), and each layer operates at a different optimization granularity.

### Layer 1 — Greedy Assignment (Real-Time)

**File:** [`app/services/solver.py`](app/services/solver.py)

Every time a new order arrives in the simulation, Layer 1 handles it instantly:

1. **Greedy Best-Insertion:** Evaluates every possible insertion point across all active vehicle routes. Picks the position that causes the minimum distance increase, subject to:
   - Vehicle capacity constraint (default: 20 units per vehicle)
   - Route duration constraint (≤ 200 minutes per route)

2. **Tabu Search Refinement:** After insertion, runs 50 iterations of 2-opt intra-route swaps with a tabu list (deque, maxlen=7) to locally improve the route.

```
Order arrives → Greedy Insert (best position) → Tabu 2-opt (50 iters) → Assignment
```

**Latency:** < 50ms per order. This ensures the system never falls behind real-time order arrival.

---

### Layer 2 — Google OR-Tools (Batch Optimization)

**File:** [`app/core_engine/solvers/ortools_solver.py`](app/core_engine/solvers/ortools_solver.py)

At configurable intervals (default: every 1800 simulation-seconds), the engine pauses and hands the **entire current routing state** to Google's OR-Tools constraint programming solver:

- **Routing Model:** Creates a `RoutingIndexManager` with all current stops + depot
- **Primary Objective:** Minimize total fleet distance (distance matrix × 100 for integer precision)
- **Capacity Dimension:** Enforces per-vehicle demand limits
- **Time Dimension:** Soft upper bound of 200 minutes with 30-second slack
- **Drop Penalties:** 1,000,000 per unserved node (disjunction penalties ensure the solver tries hard to serve everyone)
- **Search Strategy:** `PATH_CHEAPEST_ARC` first solution → `GUIDED_LOCAL_SEARCH` metaheuristic
- **Timeout:** Configurable (default 5 seconds)

OR-Tools excels at finding strong solutions quickly when the problem fits neatly into its constraint model, but it can get trapped in local optima on highly irregular datasets.

---

### Layer 3 — ALNS Metaheuristic

**File:** [`app/core_engine/solvers/alns_solver.py`](app/core_engine/solvers/alns_solver.py)

Immediately after OR-Tools finishes, ALNS takes the current best solution and attempts to improve it further using a destroy-and-repair metaheuristic with simulated annealing acceptance:

```
┌──────────────────────────────────────────────────────────────────┐
│  ALNS Iteration Loop (default: 500 iterations)                   │
│                                                                   │
│  1. DESTROY: Remove 50–90% of orders randomly from routes        │
│  2. REPAIR:  Greedily re-insert removed orders (min distance)    │
│  3. EVALUATE: Calculate new objective (fleet cost + penalties)    │
│  4. ACCEPT?: Simulated Annealing (T₀=1000, cooling=0.995)       │
│     ├── If better than global best → Accept + Stream to frontend │
│     └── If worse → Accept with probability e^(-Δ/T)             │
│  5. Cool temperature: T ← T × 0.995                              │
│                                                                   │
│  On each new global best → progress_callback() → WebSocket       │
└──────────────────────────────────────────────────────────────────┘
```

**Why ALNS wins on irregular data:**  
OR-Tools uses a structured constraint model that struggles with highly asymmetric distance matrices (common in Indian urban routing). ALNS's random destruction allows it to escape these local optima by exploring radically different route configurations, often finding 5–15% cost improvements over OR-Tools.

**Live streaming:** Every time ALNS discovers a new global best during its 500 iterations, it fires the `progress_callback`, which immediately pushes the improved routes and cost to the frontend via WebSocket. This creates the visible "staircase" convergence pattern on the dashboard chart.

---

### Strategy Modes

The system supports multiple solver configurations via the `strategy` field:

| Strategy | Behavior | Use Case |
|----------|----------|----------|
| `"benchmark"` | Runs L2 (OR-Tools) then L3 (ALNS), picks the winner | A/B comparison of solvers |
| `"alns"` | ALNS only (skips OR-Tools) | Fast metaheuristic iteration |
| `"ortools"` | OR-Tools only (skips ALNS) | Exact constraint solving |

The solver selection is handled by a **Strategy + Factory** pattern ([`factory.py`](app/core_engine/solvers/factory.py)), making it trivial to add new solvers.

---

## WebSocket Streaming Architecture

The system uses a **hybrid HTTP + WebSocket** communication pattern designed to handle the unique constraints of serverless infrastructure:

### Connection Lifecycle

```
Browser                          FastAPI (Modal)                    Modal Worker
  │                                   │                                  │
  │──── POST /upload-csv ────────────►│                                  │
  │◄─── {task_id, job_id} ───────────│──── .spawn.aio() ───────────────►│
  │                                   │                                  │
  │──── WSS /ws/{job_id}/{task_id} ──►│                                  │
  │◄─── "ping" (every 5s) ───────────│◄── progress_dict.put() ─────────│
  │◄─── {type: "progress", ...} ─────│                                  │
  │◄─── {type: "progress", ...} ─────│    (ALNS finds better route)     │
  │◄─── {type: "progress", ...} ─────│                                  │
  │              ...                  │              ...                  │
  │◄─── {type: "complete", ...} ─────│◄── task.get() returns ──────────│
  │──── close ───────────────────────►│                                  │
```

### Fault Tolerance

Modal enforces a **300-second maximum** on any single WebSocket connection. For simulations that run longer (common with large datasets), the frontend implements **automatic reconnection**:

1. When the WebSocket drops unexpectedly, the `onclose` handler detects this
2. After a 2-second delay, it calls `connect()` again
3. The reconnected WebSocket picks up the latest state from `progress_dict`
4. The user sees no interruption — the dashboard continues updating seamlessly

**Server-side heartbeats:** During blocking OR-Tools calls (which lock the Python event loop), the WebSocket handler sends `{"type": "ping"}` every 5 seconds to prevent idle timeout.

---

## Frontend Dashboard

The React dashboard is built with a **Material Design 3** dark theme using a custom Tailwind CSS design system with glassmorphism aesthetics.

### Dashboard Sections

| Section | Description |
|---------|-------------|
| **KPI Ribbon** | 5 metric cards — Total Orders, Success Rate, Fleet Utilization (with progress bar), Total Fleet Cost, Unassigned Orders |
| **Route Map** | Interactive Google Maps with color-coded polylines per vehicle. Click vehicle cards to filter routes. |
| **Convergence Chart** | Recharts line graph showing L1 (Greedy), L2 (OR-Tools), and L3 (ALNS) cost over time. Dynamically hides unused solver lines. |
| **Fleet Manifest** | Scrollable vehicle cards showing stops, cost, and duration per route |
| **Event Timeline** | Color-coded log of simulation events (order arrivals, assignments, optimizations, rejections) |
| **Export** | Download full simulation results as JSON |

### State Machine

The application follows a strict state machine pattern:

```
IDLE ──(upload)──► POLLING ──(first WS msg)──► STREAMING ──(complete)──► COMPLETED
                      │                              │
                      └──────────(error)─────────────┴──► ERROR
```

- **IDLE:** Landing page with CSV upload and hyperparameter configuration
- **POLLING:** Loading screen while Modal container boots (cold start: ~3–5s)
- **STREAMING:** Dashboard visible, routes and charts updating live via WebSocket
- **COMPLETED:** Final results locked in, all data available for export

---

## Cost Model

The fleet cost objective used by all three solver layers:

```
Total Cost = (Fixed Cost per Truck × Number of Active Trucks)
           + (Variable Cost per km × Total Fleet Distance in km)
```

**Default values:**
- Fixed cost per truck: ₹5,000 (represents insurance, maintenance, driver salary amortization)
- Variable cost per km: ₹15 (fuel + wear)

**Unassigned order penalty:** Any order that cannot be feasibly assigned receives a penalty of `fixed_cost × 10`, heavily incentivizing the solver to find valid insertions.

---

## CI/CD Pipeline

The project uses a **GitHub Actions** pipeline ([`.github/workflows/CI-CD-basicSyntax.yml`](.github/workflows/CI-CD-basicSyntax.yml)) with four stages:

```
┌──────────────────┐     ┌──────────────────┐
│   backend-ci     │     │   frontend-ci    │    ← Run in parallel
│   • Flake8 lint  │     │   • npm install  │
│   • pytest       │     │   • npm run build│
└────────┬─────────┘     └──────────────────┘
         │
         ▼
┌──────────────────┐     ┌──────────────────┐
│   docker-build   │     │   deploy-modal   │    ← Only on push to main
│   • docker build │     │   • modal deploy │
│   (validation)   │     │   (production)   │
└──────────────────┘     └──────────────────┘
```

| Job | Trigger | What It Does |
|-----|---------|-------------|
| `backend-ci` | Push/PR to `main` | Installs Python 3.11 deps, runs Flake8 linting (`E9,F63,F7,F82`), executes pytest suite |
| `frontend-ci` | Push/PR to `main` | Installs Node 18 deps, runs TypeScript compilation + Vite production build |
| `docker-build` | After `backend-ci` passes | Builds the Docker image to validate the Dockerfile compiles |
| `deploy-modal` | Push to `main` only | Deploys `modal_app.py` to Modal cloud using stored `MODAL_TOKEN` secrets |

### Test Suite

| Test | File | Description |
|------|------|-------------|
| `test_parsing_feature` | [`tests/test_pipeline.py`](tests/test_pipeline.py) | Verifies CSV parsing of the Kaggle dataset format |
| `test_scratch_calculation_feature` | [`tests/test_pipeline.py`](tests/test_pipeline.py) | End-to-end simulation with mocked Google Maps API |
| `test_upload_matrix_feature` | [`tests/test_pipeline.py`](tests/test_pipeline.py) | Simulation using a pre-computed real distance matrix |
| `test_modal_integration` | [`tests/test_integration.py`](tests/test_integration.py) | Ephemeral Modal cloud integration test (spins up a real container) |

---

## Project Structure

```
.
├── app/
│   ├── api/
│   │   └── endpoints.py             # FastAPI routes + WebSocket handler
│   ├── core_engine/
│   │   └── solvers/
│   │       ├── base.py               # Abstract BaseVRPSolver interface
│   │       ├── factory.py            # Strategy pattern — SolverFactory
│   │       ├── alns_solver.py        # ALNS metaheuristic (destroy/repair + SA)
│   │       └── ortools_solver.py     # Google OR-Tools CVRP solver
│   ├── models/
│   │   └── schemas.py                # Pydantic data models (Order, Route, Config)
│   └── services/
│       ├── simulation.py             # Core hybrid simulation engine
│       ├── solver.py                 # Cost functions + L1 greedy/tabu solver
│       ├── geocoding.py              # Google Maps geocoding service
│       ├── matrix.py                 # Distance/time matrix computation
│       └── parsing.py                # CSV parsing for delivery order data
│
├── frontend/
│   └── src/
│       ├── App.tsx                   # Root component + WebSocket state machine
│       ├── api/
│       │   └── api.ts                # HTTP client + TypeScript interfaces
│       └── components/
│           ├── LandingPage.tsx        # CSV upload + hyperparameter config UI
│           ├── LoadingScreen.tsx       # Modal cold-start loading animation
│           ├── ResultsDashboard.tsx    # KPIs, map, charts, fleet manifest
│           ├── ResultsMap.tsx         # Google Maps route polyline rendering
│           └── OptimizationChart.tsx   # Chart.js L2 vs L3 convergence
│
├── tests/
│   ├── test_pipeline.py              # Unit + integration tests (pytest)
│   ├── test_integration.py           # Modal cloud ephemeral test
│   └── data/
│       └── test_orders_10.csv        # 10-row test dataset
│
├── .github/workflows/
│   └── CI-CD-basicSyntax.yml         # GitHub Actions CI/CD pipeline
│
├── modal_app.py                       # Modal serverless deployment entry point
├── Dockerfile                         # Docker image definition
├── docker-compose.yml                 # Multi-container dev environment
├── requirements.txt                   # Python dependencies
└── vercel.json                        # Vercel SPA routing config
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- A [Modal](https://modal.com) account (free tier available)
- A Google Maps API key (for geocoding and map rendering)

### 1. Clone the Repository

```bash
git clone https://github.com/ankush-10010/VRP_Engine.git
cd VRP_Engine
```

### 2. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Authenticate with Modal
modal token new

# Deploy to Modal cloud
modal deploy modal_app.py
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set the API base URL (points to your Modal deployment)
# Create a .env file or export directly:
echo "VITE_API_BASE_URL=https://YOUR_MODAL_USERNAME--vrp-optimizer-fastapi-modal-wrapper.modal.run/api/v1" > .env

# Start development server
npm run dev
```

### 4. Run Tests

```bash
# Backend tests (from project root)
pytest -v

# Frontend build validation
cd frontend && npm run build
```

---

## Configuration Reference

All solver parameters are configurable through the frontend UI or the `SimulationConfig` schema:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `strategy` | `"alns"` | Solver mode: `"benchmark"`, `"alns"`, `"ortools"` |
| `num_vehicles` | `10` | Maximum fleet size |
| `vehicle_capacity` | `20` | Max demand units per vehicle |
| `fixed_cost_per_truck` | `5000.0` | Fixed cost per active vehicle (₹) |
| `variable_cost_per_km` | `15.0` | Distance-based cost per km (₹) |
| `layer_2_interval` | `1800` | Seconds between batch re-optimizations (simulation time) |
| `ortools_timeout` | `5` | OR-Tools solver time limit (wall clock seconds) |
| `alns_iterations` | `500` | Number of destroy-repair cycles per ALNS run |
| `alns_destroy_min_pct` | `0.50` | Minimum percentage of orders to destroy per iteration |
| `alns_destroy_max_pct` | `0.90` | Maximum percentage of orders to destroy per iteration |
| `alns_segment_length` | `50` | Segment length for adaptive weight updates |
| `alns_reaction_factor` | `0.7` | Learning rate for operator weight adaptation |

### Distance Matrix Modes

| Mode | Description |
|------|-------------|
| **Master Database** | Uses a pre-calculated Google Maps distance matrix stored server-side. Fastest option — zero API calls at runtime. |
| **Calculate from Scratch** | Geocodes all addresses and computes the full distance matrix via Google Maps API. Requires a valid API key. |
| **Upload Custom** | User provides their own distance/time matrix as a JSON file. Useful for private or synthetic datasets. |

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend Framework** | FastAPI | Async HTTP + WebSocket endpoints |
| **Solver (Exact)** | Google OR-Tools | Constraint programming CVRP solver |
| **Solver (Metaheuristic)** | Custom ALNS | Adaptive Large Neighborhood Search with SA |
| **Serverless Compute** | Modal | GPU/CPU containers with shared state dict |
| **Frontend** | React 19 + TypeScript 5.9 | Component-based SPA |
| **Build Tool** | Vite 7 | Fast HMR + production bundling |
| **Styling** | Tailwind CSS 3.4 | Material Design 3 custom theme |
| **Charts** | Recharts + Chart.js | Live convergence visualization |
| **Maps** | Google Maps JavaScript API | Route polyline rendering |
| **CI/CD** | GitHub Actions | Automated testing + Modal deployment |
| **Frontend Hosting** | Vercel | Edge-deployed SPA |
| **Testing** | pytest + Vitest | Backend unit tests + frontend build validation |

---

<p align="center">
  <sub>Built with ☕ and combinatorial optimization. If P = NP, none of this was necessary.</sub>
</p>
