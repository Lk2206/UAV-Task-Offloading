"""
Task Scheduling Algorithms: EDF, Priority-Based, and Combined Scheduling

Scheduling determines the execution ORDER of tasks.
Offloading determines the execution LOCATION of tasks.

Complexity Analysis:
    - Task Ordering Policies (EDF, Priority, Combined):
      Time Complexity: O(N log N) using Python's Timsort algorithm.
      Space Complexity: O(N) to store the ordered sequence.
    - Timeline Simulation:
      Time Complexity: O(N * (1 + E + C)), tracking queuing delays and makespan.
      Space Complexity: O(N + U + E + C) for queue state.
"""

from cost import (
    calculate_uav_cost,
    calculate_edge_cost,
    calculate_cloud_cost
)


PRIORITY_VALUE = {
    "High": 3,
    "Medium": 2,
    "Low": 1
}


def schedule_edf(tasks):
    """
    Earliest Deadline First (EDF):
    Orders tasks with the smallest deadline first.
    Ties broken by higher priority, then task ID.
    Complexity: O(N log N).
    """
    return sorted(
        tasks,
        key=lambda task: (
            task.deadline,
            -PRIORITY_VALUE.get(task.priority, 1),
            task.task_id
        )
    )


def schedule_priority(tasks):
    """
    Priority-Based Scheduling:
    Orders tasks by highest priority first.
    Ties broken by earliest deadline, then task ID.
    Complexity: O(N log N).
    """
    return sorted(
        tasks,
        key=lambda task: (
            -PRIORITY_VALUE.get(task.priority, 1),
            task.deadline,
            task.task_id
        )
    )


def schedule_combined(tasks):
    """
    Combined Priority-Deadline Scheduling:
    First groups by priority (High -> Medium -> Low),
    and within each priority tier orders by Earliest Deadline First.
    Complexity: O(N log N).
    """
    return sorted(
        tasks,
        key=lambda task: (
            -PRIORITY_VALUE.get(task.priority, 1),
            task.deadline,
            task.size,
            task.task_id
        )
    )


# Backward-compatible alias for existing main.py import
schedule_tasks = schedule_combined


def simulate_scheduled_execution(
    ordered_tasks,
    uavs,
    edge_servers,
    cloud_servers,
    policy_name="Scheduled",
    network=None
):
    """
    Simulates actual execution timelines for ordered tasks across computing resources.

    Accounts for:
    - Network transmission & Dijkstra latency
    - Server queue availability time
    - Waiting time in server queue
    - Actual completion time and deadline checks
    - Makespan of the entire system
    """
    uav_list = list(uavs) if isinstance(uavs, (list, tuple)) else [uavs]
    edge_list = list(edge_servers) if isinstance(edge_servers, (list, tuple)) else [edge_servers]
    cloud_list = list(cloud_servers) if isinstance(cloud_servers, (list, tuple)) else [cloud_servers]

    uav_map = {u.uav_id: u.clone() for u in uav_list}
    edge_map = {e.server_id: e.clone() for e in edge_list}
    cloud_map = {c.server_id: c.clone() for c in cloud_list}

    # Queue availability timestamp for each server
    queue_free_time = {}
    for u_id in uav_map:
        queue_free_time[f"UAV {u_id}"] = 0.0
    for e_id in edge_map:
        queue_free_time[f"Edge {e_id}"] = 0.0
    for c_id in cloud_map:
        queue_free_time[f"Cloud {c_id}"] = 0.0

    allocations = []
    total_response_time = 0.0
    total_energy = 0.0
    total_waiting_time = 0.0
    completed_count = 0
    unallocated_count = 0
    deadline_misses = 0

    for task in ordered_tasks:
        source_uav = uav_map.get(task.uav_id)
        uav_node = f"UAV {task.uav_id}"

        options = []

        # Local UAV option
        if source_uav and source_uav.has_capacity(task):
            loc_key = f"UAV {source_uav.uav_id}"
            cost = calculate_uav_cost(task, source_uav)
            if cost["total_delay"] != float("inf"):
                tx_delay = 0.0
                latency = 0.0
                proc_time = cost["processing_time"]
                arrival_at_server = 0.0
                start_time = max(arrival_at_server, queue_free_time[loc_key])
                wait_time = start_time - arrival_at_server
                completion_time = start_time + proc_time

                options.append({
                    "target_type": "uav",
                    "target_obj": source_uav,
                    "location": loc_key,
                    "tx_delay": tx_delay,
                    "latency": latency,
                    "proc_delay": proc_time,
                    "wait_time": wait_time,
                    "start_time": start_time,
                    "completion_time": completion_time,
                    "energy": cost["uav_energy"],
                    "path": [uav_node]
                })

        # Edge Server options
        for edge in edge_map.values():
            if edge.has_capacity(task):
                loc_key = f"Edge {edge.server_id}"
                latency = 0.0
                path = [uav_node, loc_key]
                if network is not None:
                    dist, p = network.get_shortest_path(uav_node, loc_key)
                    latency = dist if dist != float("inf") else 0.0
                    path = p if p else path

                cost = calculate_edge_cost(task, edge, network_latency=latency)
                if cost["total_delay"] != float("inf"):
                    tx_delay = cost["transmission_time"]
                    proc_time = cost["processing_time"]
                    arrival_at_server = tx_delay + latency
                    start_time = max(arrival_at_server, queue_free_time[loc_key])
                    wait_time = start_time - arrival_at_server
                    completion_time = start_time + proc_time

                    options.append({
                        "target_type": "edge",
                        "target_obj": edge,
                        "location": loc_key,
                        "tx_delay": tx_delay,
                        "latency": latency,
                        "proc_delay": proc_time,
                        "wait_time": wait_time,
                        "start_time": start_time,
                        "completion_time": completion_time,
                        "energy": cost["uav_energy"],
                        "path": path
                    })

        # Cloud Server options
        for cloud in cloud_map.values():
            if cloud.has_capacity(task):
                loc_key = f"Cloud {cloud.server_id}"
                latency = 0.0
                path = [uav_node, loc_key]
                if network is not None:
                    dist, p = network.get_shortest_path(uav_node, loc_key)
                    latency = dist if dist != float("inf") else 0.0
                    path = p if p else path

                cost = calculate_cloud_cost(task, cloud, network_latency=latency)
                if cost["total_delay"] != float("inf"):
                    tx_delay = cost["transmission_time"]
                    proc_time = cost["processing_time"]
                    arrival_at_server = tx_delay + latency
                    start_time = max(arrival_at_server, queue_free_time[loc_key])
                    wait_time = start_time - arrival_at_server
                    completion_time = start_time + proc_time

                    options.append({
                        "target_type": "cloud",
                        "target_obj": cloud,
                        "location": loc_key,
                        "tx_delay": tx_delay,
                        "latency": latency,
                        "proc_delay": proc_time,
                        "wait_time": wait_time,
                        "start_time": start_time,
                        "completion_time": completion_time,
                        "energy": cost["uav_energy"],
                        "path": path
                    })

        if not options:
            unallocated_count += 1
            allocations.append({
                "task_id": task.task_id,
                "uav_id": task.uav_id,
                "task_type": task.task_type,
                "location": "Not Allocated",
                "transmission_delay": 0.0,
                "network_latency": 0.0,
                "waiting_time": 0.0,
                "processing_delay": 0.0,
                "delay": float("inf"),
                "completion_time": float("inf"),
                "deadline": task.deadline,
                "status": "Infeasible",
                "uav_energy": 0.0,
                "path": []
            })
            continue

        # Choose the location offering the earliest completion time
        best = min(options, key=lambda opt: opt["completion_time"])

        best["target_obj"].allocate(task)
        queue_free_time[best["location"]] = best["completion_time"]
        completed_count += 1

        is_met = best["completion_time"] <= task.deadline
        if not is_met:
            deadline_misses += 1

        total_response_time += best["completion_time"]
        total_waiting_time += best["wait_time"]
        total_energy += best["energy"]

        allocations.append({
            "task_id": task.task_id,
            "uav_id": task.uav_id,
            "task_type": task.task_type,
            "location": best["location"],
            "transmission_delay": round(best["tx_delay"], 4),
            "network_latency": round(best["latency"], 4),
            "waiting_time": round(best["wait_time"], 4),
            "processing_delay": round(best["proc_delay"], 4),
            "delay": round(best["completion_time"], 4),
            "completion_time": round(best["completion_time"], 4),
            "deadline": task.deadline,
            "status": "On-Time" if is_met else "Missed Deadline",
            "uav_energy": round(best["energy"], 4),
            "path": best["path"]
        })

    makespan = max(queue_free_time.values()) if queue_free_time else 0.0

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
        "algorithm": policy_name,
        "total_delay": round(total_response_time, 4),
        "mean_delay": round(total_response_time / completed_count, 4) if completed_count > 0 else 0.0,
        "makespan": round(makespan, 4),
        "total_waiting_time": round(total_waiting_time, 4),
        "total_energy": round(total_energy, 4),
        "tasks_completed": completed_count,
        "tasks_unallocated": unallocated_count,
        "deadline_misses": deadline_misses,
        "on_time_tasks": completed_count - deadline_misses,
        "edge_cpu_utilization": round(edge_util, 2),
        "cloud_cpu_utilization": round(cloud_util, 2),
        "uav_cpu_utilization": round(uav_util, 2)
    }

    from algorithms.greedy import AllocationList
    return AllocationList(allocations, metrics)