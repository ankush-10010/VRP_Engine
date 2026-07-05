# 🚚 VRP Engine: User Guide

> **💡 QUICK START TIP:** 
> For the fastest testing of the website, we highly recommend using the **Master Database (default Database CSV)**. Just click **"Run Demo Simulation"** to instantly see the engine in action without needing to configure your own data!

Welcome to the Fleet Optimization VRP Engine. This tool uses advanced algorithms to solve complex Vehicle Routing Problems (VRP). Here is a simple guide on how to configure and run your simulations.

---

## 1. Getting Started (Data Source)
You have two ways to run the simulation:
*   **Demo Mode:** Don't upload anything. Just click **"Run Demo Simulation"** to use our pre-loaded master database.
*   **Custom Mode:** Drag and drop your own `.csv` file into the upload zone. Make sure it follows the provided template format. Once uploaded, click **"Run Custom Simulation"**.

## 2. Basic Configuration
*   **Algorithm Strategy:** 
    *   `ALNS + OR-Tools (Comparison):` Runs both solvers side-by-side so you can compare their efficiency and cost on the dashboard.
    *   `ALNS Only:` Uses our custom Adaptive Large Neighborhood Search heuristic.
    *   `OR-Tools Only:` Uses Google's mathematical routing solver.
    *   `Greedy Only:` The absolute fastest method to calculate a route, but the least optimized. Great for instant testing!
*   **Fleet Size:** The maximum number of trucks you have available to dispatch.
*   **Vehicle Capacity:** The maximum number of orders (or weight) a single truck can carry before it must return to the depot.

---

## 3. Advanced Hyperparameters
If you click the **"Advanced Hyperparameters"** dropdown, you can tune the internal brain of the ALNS algorithm. If you are unsure, leave these at their default values—they are already highly optimized!

*   **Iterations:** How many times the algorithm will attempt to improve the route. Higher numbers yield better routes but will take longer to process on the backend.
*   **Segment Length:** The algorithm learns which routing strategies work best. This setting determines how many iterations it waits before updating its "memory" of what works.
*   **Reaction Factor (0.0 to 1.0):** How aggressively the algorithm adapts to new successful routing strategies. A higher value means it learns faster from recent successes.
*   **Destroy Bounds (%):** During optimization, the algorithm "destroys" (removes) a portion of the route and rebuilds it to find shortcuts. This sets the minimum and maximum percentage of the route to destroy each time.
*   **Optimization Interval (Sec):** How often the secondary background layer runs to strictly enforce time windows and constraints.
*   **Costs (Fixed / KM):** 
    *   `Fixed:` The base cost to dispatch a single truck (e.g., driver wage).
    *   `Per KM:` The fuel/maintenance cost per kilometer driven. 
    *   *Note: The engine uses this to mathematically decide if it is cheaper to use fewer trucks with longer routes, or more trucks with shorter routes.*
