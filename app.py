"""
Flask Application for Optimal UAV Task Offloading Simulator

Endpoints:
    - GET  /              : Web Dashboard UI
    - GET  /api/health    : Health check
    - GET  /api/config    : Default configuration and presets
    - POST /api/simulate  : Execute single algorithm with chosen parameters
    - POST /api/compare   : Execute fair comparison across all algorithms
"""

import sys
import os
from flask import Flask, render_template, request, jsonify

# Ensure local modules can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulation.simulator import Simulator, generate_benchmark_workload, generate_random_workload
from models import Task
from algorithms.dynamic_programming import DPInstanceTooLargeError

app = Flask(__name__)

# Algorithm complexity and theory metadata
ALGORITHM_THEORY = {
    "greedy": {
        "name": "Greedy Heuristic",
        "category": "Heuristic Optimization",
        "time_complexity": "O(N * (E + C))",
        "space_complexity": "O(N + U + E + C)",
        "optimality": "Local optimum only (No global optimality guarantee)",
        "explanation": (
            "Greedy iterates sequentially through tasks. For each task, it queries network latencies via Dijkstra, "
            "evaluates feasible execution locations (local UAV, Edge, Cloud) respecting remaining CPU and slot constraints, "
            "and assigns the task to the location offering the minimum instantaneous total delay."
        )
    },
    "dp": {
        "name": "Dynamic Programming (MMKP)",
        "category": "Exact Dynamic Programming",
        "time_complexity": "O(N * W_Edge * W_Cloud * ∏ W_UAV)",
        "space_complexity": "O(N * W_Edge * W_Cloud)",
        "optimality": "Guaranteed Global Optimum for the stated discretized MMKP model",
        "explanation": (
            "Formulated as a Multiple-Choice Multidimensional Knapsack Problem (MMKP). Capacities are discretized by quantum Δ. "
            "DP state: S_i = (w_e, w_c, u_1, ..., u_K). Recurrence: DP[i, S] = min_{loc} { DP[i-1, S - r_i(loc)] + Delay(i, loc) }. "
            "Guaranteed optimal allocation reconstructed via backwards pointer tracing."
        )
    },
    "edf": {
        "name": "Earliest Deadline First (EDF) Scheduling",
        "category": "Priority/Deadline Scheduling",
        "time_complexity": "O(N log N) ordering + O(N * (E + C)) timeline simulation",
        "space_complexity": "O(N)",
        "optimality": "Optimal for single-processor uniprocessor preemptive scheduling; heuristic in distributed multi-server offloading",
        "explanation": (
            "Tasks are sorted in ascending order of deadline (earliest deadline first). Execution timelines are then simulated "
            "on computing servers, factoring in queue waiting times, transmission delays, and actual completion times."
        )
    },
    "priority": {
        "name": "Priority-Based Scheduling",
        "category": "Priority Scheduling",
        "time_complexity": "O(N log N) ordering + O(N * (E + C)) timeline simulation",
        "space_complexity": "O(N)",
        "optimality": "Heuristic; prioritizes high-criticality tasks over deadline proximity",
        "explanation": (
            "Orders tasks by descending priority level (High > Medium > Low), resolving ties by earliest deadline. "
            "Simulates server queuing timelines to measure actual deadline satisfaction."
        )
    },
    "combined": {
        "name": "Combined Priority-Deadline Scheduling",
        "category": "Hybrid DAA Scheduling",
        "time_complexity": "O(N log N) ordering + O(N * (E + C)) timeline simulation",
        "space_complexity": "O(N)",
        "optimality": "Balanced multi-attribute heuristic",
        "explanation": (
            "Groups tasks into priority tiers first, then applies Earliest Deadline First (EDF) within each tier. "
            "Dispatches tasks through server queues to minimize high-priority deadline violations."
        )
    }
}


@app.route("/")
def index():
    """Renders dashboard."""
    return render_template("index.html")


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "app": "UAV-Task-Offloading-Optimizer",
        "version": "1.0.0"
    })


@app.route("/api/config", methods=["GET"])
def get_config():
    """Returns default configuration and available presets."""
    default_config = Simulator.get_default_config()
    presets = {
        "benchmark": {
            "name": "Academic Benchmark (Default)",
            "description": "Standard 4-task workload from academic baseline with 3 UAVs, 1 Edge, and 1 Cloud.",
            "num_uavs": 3,
            "num_tasks": 4,
            "num_edge": 1,
            "num_cloud": 1,
            "edge_cpu_capacity": 10.0,
            "cloud_cpu_capacity": 50.0,
            "random_seed": 42,
            "use_benchmark_workload": True,
            "discretization_step": 1.0
        },
        "edge_congestion": {
            "name": "Edge Capacity Stress Test",
            "description": "Heavy compute workload with constrained Edge capacity (6 GC/s) to force offloading decisions to Cloud or local UAVs.",
            "num_uavs": 3,
            "num_tasks": 8,
            "num_edge": 1,
            "num_cloud": 1,
            "edge_cpu_capacity": 6.0,
            "cloud_cpu_capacity": 40.0,
            "random_seed": 101,
            "use_benchmark_workload": False,
            "discretization_step": 1.0
        },
        "deadline_critical": {
            "name": "Strict Deadlines Scenario",
            "description": "Short deadlines testing EDF and priority scheduling timeline compliance under queue delays.",
            "num_uavs": 4,
            "num_tasks": 10,
            "num_edge": 2,
            "num_cloud": 1,
            "edge_cpu_capacity": 12.0,
            "cloud_cpu_capacity": 60.0,
            "random_seed": 777,
            "use_benchmark_workload": False,
            "discretization_step": 1.0
        },
        "dp_optimal_verification": {
            "name": "Exact DP Verifiable Small Instance",
            "description": "Compact 5-task instance designed for step-by-step mathematical verification of DP optimality.",
            "num_uavs": 2,
            "num_tasks": 5,
            "num_edge": 1,
            "num_cloud": 1,
            "edge_cpu_capacity": 8.0,
            "cloud_cpu_capacity": 30.0,
            "random_seed": 12,
            "use_benchmark_workload": False,
            "discretization_step": 0.5
        }
    }
    return jsonify({
        "default_config": default_config,
        "presets": presets,
        "algorithms": ALGORITHM_THEORY
    })


@app.route("/api/simulate", methods=["POST"])
def simulate():
    """
    Executes a single algorithm on requested configuration.
    JSON payload:
        {
            "algorithm": "greedy" | "dp" | "edf" | "priority" | "combined",
            "config": {...},
            "custom_tasks": [...] (optional)
        }
    """
    data = request.get_json(silent=True) or {}
    algo_key = data.get("algorithm", "greedy").lower().strip()

    config = Simulator.get_default_config()
    if "config" in data and isinstance(data["config"], dict):
        config.update(data["config"])

    try:
        # Validate integer & float fields
        config["num_uavs"] = max(1, min(10, int(config["num_uavs"])))
        config["num_tasks"] = max(1, min(50, int(config["num_tasks"])))
        config["num_edge"] = max(1, min(5, int(config["num_edge"])))
        config["num_cloud"] = max(1, min(3, int(config["num_cloud"])))
        config["edge_cpu_capacity"] = max(1.0, float(config["edge_cpu_capacity"]))
        config["cloud_cpu_capacity"] = max(5.0, float(config["cloud_cpu_capacity"]))
        config["random_seed"] = int(config.get("random_seed", 42))
        config["discretization_step"] = max(0.1, min(5.0, float(config.get("discretization_step", 1.0))))
    except (ValueError, TypeError) as ex:
        return jsonify({"error": f"Invalid configuration parameter: {str(ex)}"}), 400

    sim = Simulator(config)

    # Parse custom tasks if provided
    custom_tasks = None
    if "custom_tasks" in data and isinstance(data["custom_tasks"], list):
        try:
            custom_tasks = []
            for t in data["custom_tasks"]:
                custom_tasks.append(
                    Task(
                        task_id=int(t["task_id"]),
                        uav_id=int(t["uav_id"]),
                        task_type=str(t["task_type"]),
                        size=float(t["size"]),
                        cpu_required=float(t["cpu_required"]),
                        priority=str(t["priority"]),
                        deadline=float(t["deadline"])
                    )
                )
        except Exception as ex:
            return jsonify({"error": f"Invalid custom task format: {str(ex)}"}), 400

    try:
        result = sim.run_algorithm(algo_key, custom_tasks=custom_tasks)
    except DPInstanceTooLargeError as ex:
        return jsonify({
            "error": "DP_INSTANCE_TOO_LARGE",
            "message": str(ex),
            "algorithm": "Dynamic Programming",
            "recommendation": "Reduce task count (<= 20) or increase discretization step, or select Greedy/Scheduling."
        }), 400
    except Exception as ex:
        return jsonify({"error": f"Simulation failure: {str(ex)}"}), 500

    theory = ALGORITHM_THEORY.get(algo_key, {})

    return jsonify({
        "algorithm": result["algorithm"],
        "allocations": result["allocations"],
        "metrics": result["metrics"],
        "execution_time_ms": result["execution_time_ms"],
        "network": sim.get_network_topology(),
        "workload": [t.to_dict() for t in (custom_tasks or sim.tasks)],
        "theory": theory
    })


@app.route("/api/compare", methods=["POST"])
def compare():
    """
    Executes all algorithms against the identical workload.
    """
    data = request.get_json(silent=True) or {}
    config = Simulator.get_default_config()
    if "config" in data and isinstance(data["config"], dict):
        config.update(data["config"])

    try:
        config["num_uavs"] = max(1, min(10, int(config["num_uavs"])))
        config["num_tasks"] = max(1, min(50, int(config["num_tasks"])))
        config["num_edge"] = max(1, min(5, int(config["num_edge"])))
        config["num_cloud"] = max(1, min(3, int(config["num_cloud"])))
        config["edge_cpu_capacity"] = max(1.0, float(config["edge_cpu_capacity"]))
        config["cloud_cpu_capacity"] = max(5.0, float(config["cloud_cpu_capacity"]))
        config["random_seed"] = int(config.get("random_seed", 42))
        config["discretization_step"] = max(0.1, min(5.0, float(config.get("discretization_step", 1.0))))
    except (ValueError, TypeError) as ex:
        return jsonify({"error": f"Invalid configuration parameter: {str(ex)}"}), 400

    sim = Simulator(config)

    # Parse custom tasks if provided
    custom_tasks = None
    if "custom_tasks" in data and isinstance(data["custom_tasks"], list):
        try:
            custom_tasks = []
            for t in data["custom_tasks"]:
                custom_tasks.append(
                    Task(
                        task_id=int(t["task_id"]),
                        uav_id=int(t["uav_id"]),
                        task_type=str(t["task_type"]),
                        size=float(t["size"]),
                        cpu_required=float(t["cpu_required"]),
                        priority=str(t["priority"]),
                        deadline=float(t["deadline"])
                    )
                )
        except Exception as ex:
            return jsonify({"error": f"Invalid custom task format: {str(ex)}"}), 400

    comparison_data = sim.compare_all(custom_tasks=custom_tasks)
    comparison_data["theories"] = ALGORITHM_THEORY

    return jsonify(comparison_data)


if __name__ == "__main__":
    print("\nStarting UAV Task Offloading Optimizer Web Server on http://127.0.0.1:5000 ...")
    app.run(host="127.0.0.1", port=5000, debug=True)
