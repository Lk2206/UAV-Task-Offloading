# Team Collaboration & Project Onboarding Guide

> **Project Title**: Optimal UAV Task Offloading in Edge–Cloud Computing  
> **Repository**: `Lk2206/UAV-Task-Offloading`  
> **Primary Technologies**: Python 3, Flask, Vanilla JavaScript, HTML5/CSS3, Chart.js, pytest

---

## 1. Executive Summary for Team Members

### What is this project?
This project is an **optimization and simulation platform** designed to solve the **UAV Task Offloading Problem**. 

When Unmanned Aerial Vehicles (UAVs / drones) fly real-world missions (e.g., surveillance, terrain mapping, emergency response), they generate computationally heavy tasks (e.g., object detection, high-resolution image processing).
However, drones have:
- **Low battery reserves**
- **Weak onboard compute capacity**
- **Strict real-time deadlines** (e.g., obstacle collision avoidance in 3–5 seconds)

Our system decides **where** each task should execute to **minimize total delay and meet deadlines**:
1. **Locally on the originating UAV**: Zero network transmission delay, but slow processing and high drone battery drain.
2. **On an Edge Server (MEC)**: Base station close to the UAV with moderate compute power and low network latency.
3. **On a Central Cloud Server**: High processing capacity, but subject to long transmission delays and core backbone latency.

---

## 2. Architecture & Codebase Map

Here is where everything lives and what each module does:

```
UAV-Task-Offloading/
│
├── app.py                      # Flask backend Web Server (REST API + dashboard routes)
├── main.py                     # Standalone CLI demonstration script
├── models.py                   # Data models (Task, UAV, EdgeServer, CloudServer)
├── cost.py                     # Mathematical delay & energy formulas
├── requirements.txt            # Python dependencies (Flask, pytest)
├── README.md                   # Formal academic documentation & mathematical model
├── TEAM_GUIDE.md               # Team onboarding guide (this document)
│
├── algorithms/                 # Core DAA Algorithms
│   ├── graph.py                # Graph data structure & Dijkstra's Algorithm (Min-Heap)
│   ├── greedy.py               # Greedy Heuristic (Fast, local optimum)
│   ├── dynamic_programming.py  # Exact DP solver (MMKP Knapsack formulation)
│   └── scheduling.py           # Priority, EDF, & Combined timeline scheduling
│
├── simulation/                 # Simulation Engine
│   └── simulator.py            # Workload generator (with random seed) & comparative runner
│
├── templates/
│   └── index.html              # Modern dark navy dashboard UI
│
├── static/
│   ├── css/style.css           # Styling (responsive grid, glowing accents, badges)
│   └── js/app.js               # Client controller (Chart.js charts + Canvas topology)
│
└── tests/                      # Automated Test Suite (30 tests)
    ├── test_api.py             # Flask endpoint tests
    ├── test_cost.py            # Delay & energy calculation tests
    ├── test_dp.py              # Dynamic programming correctness tests
    ├── test_graph.py           # Dijkstra & graph validation tests
    ├── test_greedy.py          # Greedy capacity & non-mutation tests
    ├── test_scheduling.py      # EDF/Priority scheduling tests
    └── test_simulator.py       # Fair workload comparison tests
```

---

## 3. How the Algorithms Work (Viva / Demo Explanation)

When explaining this project to professors, evaluators, or team members:

### 1. Dijkstra’s Algorithm (`algorithms/graph.py`)
- **Purpose**: Computes the shortest transmission latency path through the simulated network topology (UAV $\to$ Edge $\to$ Cloud).
- **Implementation**: Uses Python's `heapq` (binary min-heap).
- **Time Complexity**: $\mathcal{O}((V + E) \log V)$
- **Key Detail**: Validates that edge weights are nonnegative and reconstructs the actual routing path.

### 2. Greedy Heuristic (`algorithms/greedy.py`)
- **Purpose**: Evaluates candidate locations for each task one-by-one and greedily selects the location with the lowest instantaneous total delay.
- **Time Complexity**: $\mathcal{O}(N \cdot (E + C))$
- **Key Detail**: Clones server resources before execution so it never corrupts subsequent runs. If resources run out, it marks tasks as `"Not Allocated"`.

### 3. Dynamic Programming (`algorithms/dynamic_programming.py`)
- **Purpose**: Solves the exact global optimum for offloading decisions.
- **Formulation**: Formulated as a **Multiple-Choice Multidimensional Knapsack Problem (MMKP)**.
- **State Space**: Tracks discretized CPU capacities consumed at Edge, Cloud, and each UAV: $\text{DP}(i, w_e, w_c, \mathbf{u})$.
- **Optimality**: Guaranteed mathematically optimal for the discrete model. Backpointers reconstruct the exact chosen locations.
- **Safety Guard**: Bounded to instances ($N \le 25$) to prevent exponential memory consumption.

### 4. Scheduling & Execution Timeline (`algorithms/scheduling.py`)
- **Earliest Deadline First (EDF)**: Sorts tasks by ascending deadline.
- **Priority-Based**: Sorts tasks by High $\to$ Medium $\to$ Low priority.
- **Combined**: High-priority tier first, sorted by earliest deadline within each tier.
- **Queue Simulation**: Tasks queue on servers; waiting time is factored into completion time ($\text{Completion} = \text{Start} + \text{Processing}$).

---

## 4. How to Run Locally on Windows

### Step 1: Open Terminal (PowerShell or Command Prompt)
Navigate to the project folder:
```powershell
cd d:\TY\DAA\DAA_CP\UAV-Task-Offloading
```

### Step 2: Set Up Virtual Environment
```powershell
# Create venv
python -m venv .venv

# Activate venv in PowerShell:
.\.venv\Scripts\Activate.ps1

# Or activate venv in Command Prompt (cmd.exe):
.venv\Scripts\activate.bat
```

### Step 3: Install Required Libraries
```powershell
python -m pip install -r requirements.txt
```

### Step 4: Run the Interactive Web Dashboard
```powershell
python app.py
```
Open your browser and visit: **`http://127.0.0.1:5000/`**

### Step 5: Run the CLI Demonstration
```powershell
python main.py
```

### Step 6: Run All Automated Tests
```powershell
python -m pytest -v
```
*(All 30 tests should pass cleanly!)*

---

## 5. Web Dashboard Guide for Team Members

When you open **`http://127.0.0.1:5000/`**:

1. **Top KPI Cards**: Displays active UAV count, total tasks, Edge servers, and Cloud servers.
2. **Preset Dropdown**: Choose between:
   - *Academic Benchmark*: Canonical 4-task workload.
   - *Edge Capacity Stress Test*: Constrains Edge CPU to trigger Cloud offloading.
   - *Strict Deadlines*: Demonstrates deadline violations and EDF prioritization.
   - *DP Verifiable Small*: Compact 5-task instance for optimal verification.
3. **Algorithm Buttons**: Click any algorithm (Greedy, DP, EDF, Priority, Combined) to simulate that policy.
4. **"Compare All Algorithms" Button**: Runs all 5 algorithms on the **exact same workload** and renders 4 comparative Chart.js charts:
   - Total Delay & Makespan (lower is better)
   - Runtime in milliseconds (Greedy speed vs. DP complexity)
   - Completed Tasks vs. Deadline Misses
   - CPU Utilization by node
5. **Interactive Network Canvas**: Shows live visual nodes (UAVs, Edge, Cloud) with Dijkstra communication links.

---

## 6. How to Push Changes to GitHub

To push your latest commits to your remote GitHub repository:

```powershell
git push origin main
```

If you or a teammate pull updates on another machine:
```powershell
git pull origin main
```
