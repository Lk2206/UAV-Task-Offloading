"""
Unified Simulation Engine for UAV Task Offloading

Integrates:
- Workload generation with configurable deterministic seeds
- Network topology construction with Dijkstra routing
- Execution of Greedy, Dynamic Programming, EDF, Priority, and Combined Scheduling
- Comprehensive metric collection and fair algorithm comparison
"""

import time
import random
import copy
from models import Task, UAV, EdgeServer, CloudServer
from algorithms.graph import Graph
from algorithms.greedy import greedy_offloading
from algorithms.scheduling import (
    schedule_edf,
    schedule_priority,
    schedule_combined,
    simulate_scheduled_execution
)
from algorithms.dynamic_programming import (
    dynamic_programming_offloading,
    DPInstanceTooLargeError,
    MAX_RECOMMENDED_TASKS
)


TASK_TYPES = [
    {"name": "Image Processing", "size_range": (300, 600), "cpu_range": (3.0, 5.0), "priority": "High", "deadline_range": (4.0, 7.0)},
    {"name": "Object Detection", "size_range": (150, 350), "cpu_range": (2.0, 4.0), "priority": "High", "deadline_range": (3.0, 6.0)},
    {"name": "Mapping", "size_range": (600, 950), "cpu_range": (4.0, 6.5), "priority": "Medium", "deadline_range": (6.0, 10.0)},
    {"name": "Surveillance", "size_range": (50, 150), "cpu_range": (0.8, 2.0), "priority": "Low", "deadline_range": (8.0, 14.0)},
    {"name": "Video Analytics", "size_range": (400, 750), "cpu_range": (3.5, 6.0), "priority": "Medium", "deadline_range": (5.0, 9.0)},
]


def generate_benchmark_workload():
    """Generates the canonical 4-task academic benchmark workload."""
    return [
        Task(1, 1, "Image Processing", 500.0, 4.0, "High", 5.0),
        Task(2, 2, "Object Detection", 250.0, 3.0, "High", 4.0),
        Task(3, 3, "Mapping", 800.0, 5.0, "Medium", 8.0),
        Task(4, 1, "Surveillance", 100.0, 1.0, "Low", 10.0)
    ]


def generate_random_workload(
    num_tasks=8,
    num_uavs=3,
    seed=42,
    size_multiplier=1.0,
    cpu_multiplier=1.0
):
    """
    Generates a deterministic synthetic workload based on seed and parameter bounds.
    """
    rng = random.Random(seed)
    tasks = []

    for task_id in range(1, num_tasks + 1):
        uav_id = rng.randint(1, num_uavs)
        t_template = rng.choice(TASK_TYPES)

        size = round(rng.uniform(*t_template["size_range"]) * size_multiplier, 1)
        cpu = round(rng.uniform(*t_template["cpu_range"]) * cpu_multiplier, 1)
        deadline = round(rng.uniform(*t_template["deadline_range"]), 1)
        priority = t_template["priority"]

        tasks.append(
            Task(
                task_id=task_id,
                uav_id=uav_id,
                task_type=t_template["name"],
                size=size,
                cpu_required=cpu,
                priority=priority,
                deadline=deadline
            )
        )

    return tasks


class Simulator:
    def __init__(self, config=None):
        self.config = config or self.get_default_config()
        self.uavs = []
        self.edge_servers = []
        self.cloud_servers = []
        self.network = Graph()
        self.tasks = []
        self.setup_environment()

    @staticmethod
    def get_default_config():
        return {
            "num_uavs": 3,
            "num_tasks": 4,
            "num_edge": 1,
            "num_cloud": 1,
            "uav_cpu_capacity": 2.5,   # GC/s average
            "edge_cpu_capacity": 10.0, # GC/s
            "cloud_cpu_capacity": 50.0,# GC/s
            "edge_max_tasks": 8,
            "cloud_max_tasks": 20,
            "uav_bandwidth": 12.0,     # Mbps
            "edge_bandwidth": 100.0,   # Mbps
            "cloud_bandwidth": 1000.0, # Mbps
            "random_seed": 42,
            "use_benchmark_workload": True,
            "discretization_step": 1.0
        }

    def setup_environment(self, custom_config=None):
        """Constructs computing nodes and network graph."""
        cfg = custom_config or self.config

        # 1. Instantiate UAVs
        self.uavs = []
        uav_capacities = [2.0, 3.0, 2.5, 2.8, 3.2]
        uav_bandwidths = [10.0, 15.0, 12.0, 14.0, 11.0]
        for i in range(1, cfg["num_uavs"] + 1):
            cpu = uav_capacities[(i - 1) % len(uav_capacities)]
            bw = uav_bandwidths[(i - 1) % len(uav_bandwidths)]
            self.uavs.append(
                UAV(
                    uav_id=i,
                    cpu_capacity=cpu,
                    battery=80.0,
                    bandwidth=bw,
                    max_tasks=5
                )
            )

        # 2. Instantiate Edge Servers
        self.edge_servers = []
        for i in range(1, cfg["num_edge"] + 1):
            self.edge_servers.append(
                EdgeServer(
                    server_id=i,
                    cpu_capacity=float(cfg["edge_cpu_capacity"]),
                    max_tasks=int(cfg["edge_max_tasks"]),
                    bandwidth=float(cfg["edge_bandwidth"])
                )
            )

        # 3. Instantiate Cloud Servers
        self.cloud_servers = []
        for i in range(1, cfg["num_cloud"] + 1):
            self.cloud_servers.append(
                CloudServer(
                    server_id=i,
                    cpu_capacity=float(cfg["cloud_cpu_capacity"]),
                    max_tasks=int(cfg["cloud_max_tasks"]),
                    bandwidth=float(cfg["cloud_bandwidth"])
                )
            )

        # 4. Construct Network Graph
        self.network = Graph()
        # Add UAV -> Edge links with realistic latencies (1.0 - 2.5s)
        base_latencies = [2.0, 1.5, 2.2, 1.8, 2.4]
        for u in self.uavs:
            u_node = f"UAV {u.uav_id}"
            for e_idx, e in enumerate(self.edge_servers):
                e_node = f"Edge {e.server_id}"
                lat = base_latencies[(u.uav_id + e_idx - 1) % len(base_latencies)]
                self.network.add_edge(u_node, e_node, lat)

        # Add Edge -> Cloud links with backbone latency (2.0 - 3.0s)
        for e in self.edge_servers:
            e_node = f"Edge {e.server_id}"
            for c in self.cloud_servers:
                c_node = f"Cloud {c.server_id}"
                self.network.add_edge(e_node, c_node, 2.5)

        # 5. Workload setup
        if cfg.get("use_benchmark_workload", False) and cfg["num_tasks"] == 4 and cfg["num_uavs"] == 3:
            self.tasks = generate_benchmark_workload()
        else:
            self.tasks = generate_random_workload(
                num_tasks=cfg["num_tasks"],
                num_uavs=cfg["num_uavs"],
                seed=cfg.get("random_seed", 42)
            )

    def get_network_topology(self):
        """Returns JSON-serializable nodes and edges for network visualization."""
        nodes = []
        for u in self.uavs:
            nodes.append({
                "id": f"UAV {u.uav_id}",
                "label": f"UAV {u.uav_id}",
                "type": "uav",
                "cpu": u.cpu_capacity,
                "bandwidth": u.bandwidth,
                "battery": u.battery
            })
        for e in self.edge_servers:
            nodes.append({
                "id": f"Edge {e.server_id}",
                "label": f"Edge {e.server_id}",
                "type": "edge",
                "cpu": e.cpu_capacity,
                "bandwidth": e.bandwidth,
                "max_tasks": e.max_tasks
            })
        for c in self.cloud_servers:
            nodes.append({
                "id": f"Cloud {c.server_id}",
                "label": f"Cloud {c.server_id}",
                "type": "cloud",
                "cpu": c.cpu_capacity,
                "bandwidth": c.bandwidth,
                "max_tasks": c.max_tasks
            })

        edges = []
        for src, adj in self.network.graph.items():
            for dst, weight in adj:
                edges.append({
                    "source": src,
                    "target": dst,
                    "latency": weight
                })

        return {"nodes": nodes, "edges": edges}

    def run_algorithm(self, algorithm_name, custom_tasks=None):
        """
        Runs a single algorithm on the current or provided tasks.
        Guarantees isolation of resource states.
        """
        tasks_to_run = [t.clone() for t in (custom_tasks or self.tasks)]
        algo = algorithm_name.lower().strip()

        start_time = time.perf_counter()

        if algo == "greedy":
            result = greedy_offloading(
                tasks_to_run,
                self.uavs,
                self.edge_servers,
                self.cloud_servers,
                network=self.network,
                clone_resources=True
            )
        elif algo in ("dp", "dynamic_programming"):
            step = float(self.config.get("discretization_step", 1.0))
            result = dynamic_programming_offloading(
                tasks_to_run,
                self.uavs,
                self.edge_servers,
                self.cloud_servers,
                network=self.network,
                discretization_step=step
            )
        elif algo == "edf":
            ordered = schedule_edf(tasks_to_run)
            result = simulate_scheduled_execution(
                ordered,
                self.uavs,
                self.edge_servers,
                self.cloud_servers,
                policy_name="Earliest Deadline First (EDF)",
                network=self.network
            )
        elif algo == "priority":
            ordered = schedule_priority(tasks_to_run)
            result = simulate_scheduled_execution(
                ordered,
                self.uavs,
                self.edge_servers,
                self.cloud_servers,
                policy_name="Priority-Based Scheduling",
                network=self.network
            )
        elif algo in ("combined", "combined_scheduling"):
            ordered = schedule_combined(tasks_to_run)
            result = simulate_scheduled_execution(
                ordered,
                self.uavs,
                self.edge_servers,
                self.cloud_servers,
                policy_name="Combined Priority-Deadline Scheduling",
                network=self.network
            )
        else:
            raise ValueError(f"Unknown algorithm: {algorithm_name}")

        exec_time_ms = round((time.perf_counter() - start_time) * 1000.0, 3)

        metrics = dict(result.metrics)
        metrics["execution_time_ms"] = exec_time_ms

        return {
            "algorithm": metrics.get("algorithm", algorithm_name),
            "allocations": list(result),
            "metrics": metrics,
            "execution_time_ms": exec_time_ms
        }

    def compare_all(self, custom_tasks=None):
        """
        Executes all supported algorithms against the identical workload and resource state.
        Calculates fair performance comparisons.
        """
        tasks_pool = [t.clone() for t in (custom_tasks or self.tasks)]
        algorithms = [
            ("Greedy", "greedy"),
            ("Earliest Deadline First (EDF)", "edf"),
            ("Priority Scheduling", "priority"),
            ("Combined Scheduling", "combined")
        ]

        results = {}

        # 1. Run heuristics and scheduling algorithms
        for display_name, algo_key in algorithms:
            results[algo_key] = self.run_algorithm(algo_key, tasks_pool)

        # 2. Run Dynamic Programming if within tractable limits
        dp_supported = len(tasks_pool) <= MAX_RECOMMENDED_TASKS
        if dp_supported:
            try:
                results["dp"] = self.run_algorithm("dp", tasks_pool)
            except DPInstanceTooLargeError as ex:
                results["dp"] = {
                    "algorithm": "Dynamic Programming",
                    "status": "unsupported",
                    "reason": str(ex),
                    "allocations": [],
                    "metrics": {
                        "algorithm": "Dynamic Programming",
                        "status": "Instance too large",
                        "total_delay": None,
                        "mean_delay": None,
                        "tasks_completed": None,
                        "tasks_unallocated": None,
                        "deadline_misses": None,
                        "execution_time_ms": None
                    }
                }
        else:
            results["dp"] = {
                "algorithm": "Dynamic Programming",
                "status": "unsupported",
                "reason": (
                    f"Instance contains {len(tasks_pool)} tasks (limit: {MAX_RECOMMENDED_TASKS}). "
                    f"Multidimensional knapsack DP state space O(N * W_E * W_C) grows exponentially."
                ),
                "allocations": [],
                "metrics": {
                    "algorithm": "Dynamic Programming",
                    "status": "Instance too large",
                    "total_delay": None,
                    "mean_delay": None,
                    "tasks_completed": None,
                    "tasks_unallocated": None,
                    "deadline_misses": None,
                    "execution_time_ms": None
                }
            }

        # 3. Calculate comparative percentage improvement over Greedy
        greedy_delay = results["greedy"]["metrics"]["total_delay"]
        for key, res in results.items():
            if res.get("status") == "unsupported":
                res["metrics"]["delay_improvement_pct"] = None
                continue
            delay = res["metrics"]["total_delay"]
            if greedy_delay > 0 and delay is not None:
                imp = ((greedy_delay - delay) / greedy_delay) * 100.0
                res["metrics"]["delay_improvement_pct"] = round(imp, 2)
            else:
                res["metrics"]["delay_improvement_pct"] = 0.0

        return {
            "workload": [t.to_dict() for t in tasks_pool],
            "results": results,
            "network": self.get_network_topology()
        }
