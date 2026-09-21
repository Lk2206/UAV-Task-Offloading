# ==========================================
# Cost and Delay Calculation
# ==========================================


def calculate_processing_time(task, computing_capacity):
    """
    Calculate processing time.

    Formula:
        Processing Time = CPU Requirement / Computing Capacity
    """

    if computing_capacity <= 0:
        return float("inf")

    if task.cpu_required > computing_capacity:
        return float("inf")

    return task.cpu_required / computing_capacity


def calculate_transmission_time(task_size_mb, bandwidth_mbps):
    """
    Calculate transmission time.

    Formula:
        Transmission Time =
        (Task Size in MB * 8) / Bandwidth in Mbps
    """

    if bandwidth_mbps <= 0:
        return float("inf")

    return (task_size_mb * 8) / bandwidth_mbps


def calculate_uav_cost(task, uav):
    """
    Calculate cost for local UAV processing.
    """

    processing_time = calculate_processing_time(
        task,
        uav.cpu_capacity
    )

    transmission_time = 0

    total_delay = processing_time + transmission_time

    return {
        "location": f"UAV {uav.uav_id}",
        "processing_time": processing_time,
        "transmission_time": transmission_time,
        "total_delay": total_delay
    }


def calculate_edge_cost(task, edge):
    """
    Calculate cost for Edge processing.
    """

    processing_time = calculate_processing_time(
        task,
        edge.cpu_capacity
    )

    transmission_time = calculate_transmission_time(
        task.size,
        edge.bandwidth
    )

    total_delay = processing_time + transmission_time

    return {
        "location": f"Edge {edge.server_id}",
        "processing_time": processing_time,
        "transmission_time": transmission_time,
        "total_delay": total_delay
    }


def calculate_cloud_cost(task, cloud):
    """
    Calculate cost for Cloud processing.
    """

    processing_time = calculate_processing_time(
        task,
        cloud.cpu_capacity
    )

    transmission_time = calculate_transmission_time(
        task.size,
        cloud.bandwidth
    )

    total_delay = processing_time + transmission_time

    return {
        "location": f"Cloud {cloud.server_id}",
        "processing_time": processing_time,
        "transmission_time": transmission_time,
        "total_delay": total_delay
    }