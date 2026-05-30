# VRP Optimizer: Production Readiness Roadmap

This document outlines the comprehensive roadmap to elevate the VRP Optimizer from a robust prototype to a **Core SDE Production-Level System**. It also details the immediate implementation for the CSV upload UX fix requested.

<!-- ## Immediate Task: CSV Upload UX Fix
Currently, when a user clicks "Run Simulation", the `uploadSimulationCsv` function executes but the frontend does not indicate any activity until the Modal container responds.

**Proposed Change:**
- Introduce an `isUploading` state in `LandingPage.tsx`.
- Disable the "Run Simulation" button and render a loading spinner with text indicating "Booting Modal Container & Uploading CSV...".
<!-- - This provides immediate visual feedback that the background process has started, bridging the gap before `App.tsx` transitions to the global `LoadingScreen`. -->  
---

## The Production-Level Roadmap

The following phases outline the missing architectural pillars required for top-tier software engineering resumes.

### Phase 1: CI/CD & Automated Quality Gates (The "Shippable" Pillar)
**Goal:** Prove that the codebase can scale collaboratively without breaking.
- **GitHub Actions Pipeline:** Implement a `.github/workflows/main.yml` file.
- **Automated Testing:** 
  - Add `pytest` for the FastAPI backend to unit-test the ALNS and OR-Tools logic.
  - Add `jest` or `vitest` for React component testing.
- **Linting & Formatting:** Enforce `flake8` / `black` for Python and `eslint` for TypeScript in the pipeline.
- **Automated Deployment:** Configure the pipeline to automatically deploy to Vercel and Modal only when all tests pass.

### Phase 2: Caching & API Resiliency (The "Scale" Pillar)
**Goal:** Demonstrate enterprise-level cost management and performance scaling.
- **Distance Matrix Cache:** Currently, the system hits Google Maps for every run. We will implement a `SQLite` or `Redis` cache mapping `(lat1, lng1) -> (lat2, lng2)`. If a route was previously calculated, it instantly returns the cached distance/time, saving 90% on latency and API costs.
- **API Circuit Breakers:** Implement exponential backoff for the Google Maps API requests to gracefully handle `OVER_QUERY_LIMIT` drops without failing the entire simulation.

### Phase 3: Observability & Tracing (The "Blindspot" Pillar)
**Goal:** Stop relying on terminal prints; track errors in production.
- **Sentry Integration:** Integrate Sentry into both the React frontend and FastAPI backend.
- **Structured Logging:** Convert standard Python `print()` statements in `modal_app.py` into structured JSON logs using the `logging` module. This allows tracking the exact performance (runtime, cost) of the algorithms historically.

### Phase 4: Data Persistence & Sharing (The "State" Pillar)
**Goal:** Allow users to share their simulation results via URLs.
- **Database Integration:** Connect the Modal backend to a persistent database (e.g., PostgreSQL via Supabase or Neon).
- **Unique Run URLs:** When a simulation finishes, save the `SimulationResult` JSON to the database. Generate a unique frontend route (e.g., `vrp-engine.vercel.app/sim/abc-123`) so results can be shared with recruiters or stakeholders.

### Phase 5: Algorithmic Parameter Sweeping (The "Math" Pillar)
**Goal:** Showcase distributed computing and mathematical benchmarking.
- **Distributed Execution:** Update the UI to select "Sweep Mode". The frontend will send a request to Modal to spawn 5 concurrent containers, each running ALNS with slightly different hyperparameters.
- **Convergence Comparison:** The frontend will graph all 5 convergence lines simultaneously, mathematically proving which hyperparameter set is optimal for a given dataset.
