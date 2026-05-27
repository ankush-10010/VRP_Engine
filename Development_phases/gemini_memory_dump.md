# VRP Optimizer Architecture & Context Dump (System State Memory)

**INSTRUCTION FOR LLM:** Ingest the following context regarding the state of the VRP (Vehicle Routing Problem) Optimizer application. This contains critical architectural paradigms, recent bug fixes, and system limitations.

## 1. Tech Stack
- **Frontend:** React, Vite, TailwindCSS, Recharts (for analytics), `@react-google-maps/api` (for routing).
- **Backend:** FastAPI wrapped in Modal Serverless (`@modal.asgi_app`), Python, Pandas (for CSV parsing).
- **Optimization Engines:** OR-Tools (Layer 2 routing) and ALNS (Adaptive Large Neighborhood Search, Layer 3 routing).

## 2. Frontend State & Map Architecture (`ResultsMap.tsx` & `ResultsDashboard.tsx`)
- **Multi-Select Filtering:** The UI supports multi-selecting vehicles to display. The state is managed via an `activeVehicleIds: number[]` array. `ROUTE_COLORS` are statically bound via `vehicle_id % ROUTE_COLORS.length` rather than map index to prevent color scrambling during array filtration.
- **Google Maps Directions API Integration:**
  - *Waypoint Chunking:* Google Maps imposes a strict 25-waypoint limit. To support highly dense VRP outputs (>25 stops per truck), routes are aggressively sliced into overlapping segments (1 origin, 1 destination, 23 waypoints). These are iterated over to produce chained `DirectionsRenderer` instances per vehicle.
  - *Rate Limit Throttling:* To prevent client-side `OVER_QUERY_LIMIT` errors (max 10 req/s) when mapping massive fleets, chunks are processed sequentially using `for...of` loops with an injected `await new Promise(r => setTimeout(r, 200))` delay.
  - *React Unmounting Quirk (The "Ghost Triangle" Fix):* `@react-google-maps/api` fails to cleanly unmount `Polyline` fallbacks if they overlap with a resolving `DirectionsRenderer`. This is solved by strictly evaluating the `directions` state: `undefined` renders *nothing* (fetching), `null` renders `<Polyline>` (API failure fallback), and a populated array renders `DirectionsRenderer`.
- **API Wrapper (`api.ts`):** 
  - To handle Modal serverless cold starts (5-10s spin-up time), the `uploadSimulationCsv` function is wrapped in a silent 3-attempt retry loop with a 2-second delay. This gracefully masks 502/404 proxy drops during container boot.

## 3. Backend Data Preprocessing (`app/services/parsing.py`)
- **Temporal Compression (High-Density Forcing):** The simulation requires high order density to force ALNS and OR-Tools into divergent optimization paths. 
- *Implementation:* During CSV parsing, `FORCE_SINGLE_DAY = True` is used. Every order's UNIX timestamp is mathematically mapped to a static base date (`September 10, 2024`) while strictly preserving the hour and minute. 
- *Truncation:* A hard limit of `50` chronologically sorted orders is enforced prior to execution to prevent RAM/Timeouts on the Modal container. The full-dataset variable assignment is preserved but commented out for future scaling.

## 4. Legacy ALNS Hyperparameters (Recovered from v1 `hybrid_solver_layers.py`)
For reference or config injection, the original highly tuned ALNS parameters were:
- `ALNS_ITERATIONS`: 50
- `ALNS_SEGMENT_LENGTH`: 50
- `ALNS_REACTION_FACTOR`: 0.7
- `ALNS_DESTROY_MIN_PERCENT`: 0.15 (15%)
- `ALNS_DESTROY_MAX_PERCENT`: 0.40 (40%)
- Cooling Rate: 0.995 (Simulated Annealing)

**SYSTEM STATUS:** Stable. Map rendering is chunked and throttled. Backend data parsing simulates high-density temporal environments. Modal cold starts are masked via client-side retries.
