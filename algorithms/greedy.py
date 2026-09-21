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
    Greedy task offloading.

    For every task:
    1. Find its source UAV.
    2. Calculate cost on UAV, Edge and Cloud.
    3. Remove infeasible options.
    4. Select the location with minimum delay.
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

        options = [
            uav_cost,
            edge_cost,
            cloud_cost
        ]

        # ----------------------------------
        # Remove infeasible options
        # ----------------------------------

        feasible_options = [
            option
            for option in options
            if option["total_delay"] != float("inf")
        ]

        # ----------------------------------
        # Choose minimum-cost option
        # ----------------------------------

        if not feasible_options:

            allocations.append({
                "task_id": task.task_id,
                "task_type": task.task_type,
                "location": "Not Allocated",
                "delay": float("inf")
            })

            continue

        best_option = min(
            feasible_options,
            key=lambda option: option["total_delay"]
        )

        allocations.append({
            "task_id": task.task_id,
            "task_type": task.task_type,
            "location": best_option["location"],
            "delay": best_option["total_delay"]
        })

    return allocations