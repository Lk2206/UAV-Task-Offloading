"""
Greedy Task Offloading Algorithm

Complexity Analysis:
    - Time Complexity: O(N * (1 + E + C)), where N is the number of tasks,
      E is the number of Edge servers, and C is the number of Cloud servers.
      For each task, we evaluate feasibility across candidate locations and select the minimum delay.
    - Space Complexity: O(N + U + E + C) for deep copies of resources and storing allocations.

Heuristic Note:
    Greedy makes locally optimal decisions per task without backtracking or considering
    future task demands. It does NOT guarantee a global optimum.
"""

import copy
from cost import (
    calculate_uav_cost,
    calculate_edge_cost,
    calculate_cloud_cost
)


class AllocationList(list):
    """List of allocations with attached aggregate metrics for backward compatibility."""
    def __init__(self, items, metrics=None):
        super().__init__(items)
        self.metrics = metrics or {}


def greedy_offloading(
    tasks,
    uavs,
    edge_servers,
    cloud_servers,
    network=None,
    clone_resources=True
):
    """
    Greedy task offloading with resource constraints.

    For every task:
    1. Clone resources (if clone_resources=True) to prevent mutation of shared state.
    2. Identify candidate locations: local originating UAV, Edge servers, Cloud servers.
    3. Query network graph (via Dijkstra) for communication latencies.
    4. Compute processing, transmission, and total delay.
    5. Filter out infeasible options (capacity exceeded or infinite delay).
    6. Select the feasible option with minimum total delay.
    7. Allocate resources and update remaining capacities.
    8. Mark task as 'Not Allocated' if no feasible option exists.
    """
    # Normalize inputs to lists
    uav_list = list(uavs) if isinstance(uavs, (list, tuple)) else [uavs]
    edge_list = list(edge_servers) if isinstance(edge_servers, (list, tuple)) else [edge_servers]
    cloud_list = list(cloud_servers) if isinstance(cloud_servers, (list, tuple)) else [cloud_servers]

    # Create isolated resource copies to prevent side effects
    if clone_resources:
        uav_map = {u.uav_id: u.clone() for u in uav_list}
        edge_map = {e.server_id: e.clone() for e in edge_list}
        cloud_map = {c.server_id: c.clone() for c in cloud_list}
    else:
        uav_map = {u.uav_id: u for u in uav_list}
        edge_map = {e.server_id: e for e in edge_list}
        cloud_map = {c.server_id: c for c in cloud_list}

    allocations = []
    total_delay = 0.0
    total_energy = 0.0
    total_tx_delay = 0.0
    total_proc_delay = 0.0
    allocated_count = 0
    unallocated_count = 0
    deadline_misses = 0

    for task in tasks:
        source_uav = uav_map.get(task.uav_id)
        uav_node = f"UAV {task.uav_id}"

        # Evaluate candidate options
        options = []

        # 1. Local UAV
        if source_uav is not None and source_uav.has_capacity(task):
            uav_cost = calculate_uav_cost(task, source_uav)
            if uav_cost["total_delay"] != float("inf"):
                options.append({
                    "target_type": "uav",
                    "target_obj": source_uav,
                    "location": f"UAV {source_uav.uav_id}",
                    "transmission_delay": 0.0,
                    "network_latency": 0.0,
                    "processing_delay": uav_cost["processing_time"],
                    "total_delay": uav_cost["total_delay"],
                    "energy": uav_cost["uav_energy"],
                    "path": [uav_node]
                })

        # 2. Edge Servers
        for edge_id, edge in edge_map.items():
            if edge.has_capacity(task):
                edge_node = f"Edge {edge.server_id}"
                latency = 0.0
                path = [uav_node, edge_node]
                if network is not None:
                    dist, p = network.get_shortest_path(uav_node, edge_node)
                    latency = dist if dist != float("inf") else 0.0
                    path = p if p else path

                edge_cost = calculate_edge_cost(task, edge, network_latency=latency)
                if edge_cost["total_delay"] != float("inf"):
                    options.append({
                        "target_type": "edge",
                        "target_obj": edge,
                        "location": f"Edge {edge.server_id}",
                        "transmission_delay": edge_cost["transmission_time"],
                        "network_latency": latency,
                        "processing_delay": edge_cost["processing_time"],
                        "total_delay": edge_cost["total_delay"],
                        "energy": edge_cost["uav_energy"],
                        "path": path
                    })

        # 3. Cloud Servers
        for cloud_id, cloud in cloud_map.items():
            if cloud.has_capacity(task):
                cloud_node = f"Cloud {cloud.server_id}"
                latency = 0.0
                path = [uav_node, cloud_node]
                if network is not None:
                    dist, p = network.get_shortest_path(uav_node, cloud_node)
                    latency = dist if dist != float("inf") else 0.0
                    path = p if p else path

                cloud_cost = calculate_cloud_cost(task, cloud, network_latency=latency)
                if cloud_cost["total_delay"] != float("inf"):
                    options.append({
                        "target_type": "cloud",
                        "target_obj": cloud,
                        "location": f"Cloud {cloud.server_id}",
                        "transmission_delay": cloud_cost["transmission_time"],
                        "network_latency": latency,
                        "processing_delay": cloud_cost["processing_time"],
                        "total_delay": cloud_cost["total_delay"],
                        "energy": cloud_cost["uav_energy"],
                        "path": path
                    })

        # Decision rule: Select option with minimum total delay
        if not options:
            unallocated_count += 1
            allocations.append({
                "task_id": task.task_id,
                "uav_id": task.uav_id,
                "task_type": task.task_type,
                "location": "Not Allocated",
                "transmission_delay": 0.0,
                "network_latency": 0.0,
                "processing_delay": 0.0,
                "delay": float("inf"),
                "deadline": task.deadline,
                "status": "Infeasible",
                "uav_energy": 0.0,
                "path": []
            })
            continue

        best_option = min(options, key=lambda opt: opt["total_delay"])

        # Commit resource allocation
        best_option["target_obj"].allocate(task)
        allocated_count += 1

        is_deadline_met = best_option["total_delay"] <= task.deadline
        if not is_deadline_met:
            deadline_misses += 1

        total_delay += best_option["total_delay"]
        total_energy += best_option["energy"]
        total_tx_delay += best_option["transmission_delay"]
        total_proc_delay += best_option["processing_delay"]

        allocations.append({
            "task_id": task.task_id,
            "uav_id": task.uav_id,
            "task_type": task.task_type,
            "location": best_option["location"],
            "transmission_delay": round(best_option["transmission_delay"], 4),
            "network_latency": round(best_option["network_latency"], 4),
            "processing_delay": round(best_option["processing_delay"], 4),
            "delay": round(best_option["total_delay"], 4),
            "deadline": task.deadline,
            "status": "On-Time" if is_deadline_met else "Missed Deadline",
            "uav_energy": round(best_option["energy"], 4),
            "path": best_option["path"]
        })

    # Compute resource utilizations
    edge_cpu_total = sum(e.cpu_capacity for e in edge_map.values())
    edge_cpu_used = sum(e.used_cpu for e in edge_map.values())
    edge_util = (edge_cpu_used / edge_cpu_total * 100.0) if edge_cpu_total > 0 else 0.0

    cloud_cpu_total = sum(c.cpu_capacity for c in cloud_map.values())
    cloud_cpu_used = sum(c.used_cpu for c in cloud_map.values())
    cloud_util = (cloud_cpu_used / cloud_cpu_total * 100.0) if cloud_cpu_total > 0 else 0.0

    uav_cpu_total = sum(u.cpu_capacity for u in uav_map.values())
    uav_cpu_used = sum(u.used_cpu for u in uav_map.values())
    uav_util = (uav_cpu_used / uav_cpu_total * 100.0) if uav_cpu_total > 0 else 0.0

    metrics = {
        "algorithm": "Greedy",
        "total_delay": round(total_delay, 4),
        "mean_delay": round(total_delay / allocated_count, 4) if allocated_count > 0 else 0.0,
        "total_tx_delay": round(total_tx_delay, 4),
        "total_proc_delay": round(total_proc_delay, 4),
        "total_energy": round(total_energy, 4),
        "tasks_completed": allocated_count,
        "tasks_unallocated": unallocated_count,
        "deadline_misses": deadline_misses,
        "on_time_tasks": allocated_count - deadline_misses,
        "edge_cpu_utilization": round(edge_util, 2),
        "cloud_cpu_utilization": round(cloud_util, 2),
        "uav_cpu_utilization": round(uav_util, 2)
    }

    return AllocationList(allocations, metrics)