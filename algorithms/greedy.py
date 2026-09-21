# ==========================================
# Greedy Task Offloading Algorithm
# ==========================================

from cost import (
    calculate_uav_cost,
    calculate_edge_cost,
    calculate_cloud_cost
)


def greedy_offloading(tasks, uavs, edge, cloud):
    """
    Greedy task offloading with resource constraints.

    For every task:
    1. Calculate the cost at each location.
    2. Remove infeasible locations.
    3. Select the location with minimum delay.
    4. Update resource usage.
    """

    allocations = []

    for task in tasks:

        # ----------------------------------
        # Find source UAV
        # ----------------------------------

        source_uav = None

        for uav in uavs:
            if uav.uav_id == task.uav_id:
                source_uav = uav
                break

        # ----------------------------------
        # Calculate costs
        # ----------------------------------

        uav_cost = calculate_uav_cost(
            task,
            source_uav
        )

        edge_cost = calculate_edge_cost(
            task,
            edge
        )

        cloud_cost = calculate_cloud_cost(
            task,
            cloud
        )

        # ----------------------------------
        # Check resource constraints
        # ----------------------------------

        options = []

        # UAV
        if uav_cost["total_delay"] != float("inf"):
            options.append(uav_cost)

        # Edge
        if (
            edge.has_capacity(task)
            and edge_cost["total_delay"] != float("inf")
        ):
            options.append(edge_cost)

        # Cloud
        if (
            cloud.has_capacity(task)
            and cloud_cost["total_delay"] != float("inf")
        ):
            options.append(cloud_cost)

        # ----------------------------------
        # No feasible location
        # ----------------------------------

        if not options:

            allocations.append({
                "task_id": task.task_id,
                "task_type": task.task_type,
                "location": "Not Allocated",
                "delay": float("inf")
            })

            continue

        # ----------------------------------
        # Greedy selection
        # ----------------------------------

        best_option = min(
            options,
            key=lambda option: option["total_delay"]
        )

        # ----------------------------------
        # Update resources
        # ----------------------------------

        if best_option["location"].startswith("Edge"):
            edge.allocate(task)

        elif best_option["location"].startswith("Cloud"):
            cloud.allocate(task)

        # ----------------------------------
        # Store result
        # ----------------------------------

        allocations.append({
            "task_id": task.task_id,
            "task_type": task.task_type,
            "location": best_option["location"],
            "delay": best_option["total_delay"]
        })

    return allocations