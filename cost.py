"""
Cost, Delay, and Energy Calculations for UAV Task Offloading

Units:
    - Task size: Megabytes (MB)
    - CPU required: Gigacycles (GC = 10^9 cycles)
    - Computing capacity: Gigacycles per second (GC/s)
    - Bandwidth: Megabits per second (Mbps)
    - Latency, Delays: Seconds (s)
    - Power: Watts (W) -> Energy: Joules (J = W * s)

Equations:
    - Transmission Time (s) = (Size [MB] * 8 [bits/byte]) / Bandwidth [Mbps]
    - Processing Time (s) = Required CPU [GC] / Computing Capacity [GC/s]
    - Total Delay (s) = Transmission Time + Network Latency + Processing Time
"""

# Power coefficients for energy modeling (Watts)
P_UAV_COMP = 2.0   # UAV CPU active compute power (W)
P_UAV_TX = 1.2     # UAV transmission RF power (W)
P_UAV_IDLE = 0.2   # UAV idle listening power (W)
P_SERVER_COMP = 50.0 # Server compute power consumption (W)


def calculate_processing_time(task, computing_capacity):
    """
    Calculate processing time.

    Formula:
        Processing Time (s) = Required CPU (GC) / Computing Capacity (GC/s)
    """
    if computing_capacity is None or computing_capacity <= 0:
        return float("inf")

    if task is None or task.cpu_required < 0:
        return float("inf")

    return task.cpu_required / float(computing_capacity)


def calculate_transmission_time(task_size_mb, bandwidth_mbps):
    """
    Calculate transmission time.

    Formula:
        Transmission Time (s) = (Task Size in MB * 8) / Bandwidth in Mbps
    """
    if bandwidth_mbps is None or bandwidth_mbps <= 0:
        return float("inf")

    if task_size_mb is None or task_size_mb < 0:
        return float("inf")

    return (float(task_size_mb) * 8.0) / float(bandwidth_mbps)


def calculate_uav_cost(task, uav):
    """
    Calculate cost for local UAV execution.
    Transmission time and network latency are zero for local execution.
    """
    if uav is None:
        return {
            "location": "UAV Unknown",
            "processing_time": float("inf"),
            "transmission_time": 0.0,
            "network_latency": 0.0,
            "total_delay": float("inf"),
            "uav_energy": float("inf"),
            "is_feasible": False
        }

    processing_time = calculate_processing_time(task, uav.cpu_capacity)
    transmission_time = 0.0
    network_latency = 0.0
    total_delay = processing_time

    # Local UAV computation energy (Joules = Watts * seconds)
    if total_delay != float("inf"):
        uav_energy = P_UAV_COMP * processing_time
    else:
        uav_energy = float("inf")

    return {
        "location": f"UAV {uav.uav_id}",
        "processing_time": processing_time,
        "transmission_time": transmission_time,
        "network_latency": network_latency,
        "total_delay": total_delay,
        "uav_energy": uav_energy,
        "is_feasible": total_delay != float("inf") and uav.has_capacity(task)
    }


def calculate_edge_cost(task, edge, network_latency=0.0):
    """
    Calculate cost for Edge Server offloading.
    Network latency is the shortest-path communication latency from UAV to Edge.
    """
    if edge is None:
        return {
            "location": "Edge Unknown",
            "processing_time": float("inf"),
            "transmission_time": float("inf"),
            "network_latency": float("inf"),
            "total_delay": float("inf"),
            "uav_energy": float("inf"),
            "is_feasible": False
        }

    processing_time = calculate_processing_time(task, edge.cpu_capacity)
    transmission_time = calculate_transmission_time(task.size, edge.bandwidth)
    latency = max(0.0, float(network_latency)) if network_latency != float("inf") else float("inf")

    if (
        processing_time == float("inf")
        or transmission_time == float("inf")
        or latency == float("inf")
    ):
        total_delay = float("inf")
        uav_energy = float("inf")
    else:
        total_delay = transmission_time + latency + processing_time
        # UAV transmits data, then waits in idle state until result arrives
        uav_energy = (P_UAV_TX * transmission_time) + (P_UAV_IDLE * (latency + processing_time))

    return {
        "location": f"Edge {edge.server_id}",
        "processing_time": processing_time,
        "transmission_time": transmission_time,
        "network_latency": latency,
        "total_delay": total_delay,
        "uav_energy": uav_energy,
        "is_feasible": total_delay != float("inf") and edge.has_capacity(task)
    }


def calculate_cloud_cost(task, cloud, network_latency=0.0):
    """
    Calculate cost for Cloud Server offloading.
    Network latency is the shortest-path communication latency from UAV to Cloud.
    """
    if cloud is None:
        return {
            "location": "Cloud Unknown",
            "processing_time": float("inf"),
            "transmission_time": float("inf"),
            "network_latency": float("inf"),
            "total_delay": float("inf"),
            "uav_energy": float("inf"),
            "is_feasible": False
        }

    processing_time = calculate_processing_time(task, cloud.cpu_capacity)
    transmission_time = calculate_transmission_time(task.size, cloud.bandwidth)
    latency = max(0.0, float(network_latency)) if network_latency != float("inf") else float("inf")

    if (
        processing_time == float("inf")
        or transmission_time == float("inf")
        or latency == float("inf")
    ):
        total_delay = float("inf")
        uav_energy = float("inf")
    else:
        total_delay = transmission_time + latency + processing_time
        uav_energy = (P_UAV_TX * transmission_time) + (P_UAV_IDLE * (latency + processing_time))

    return {
        "location": f"Cloud {cloud.server_id}",
        "processing_time": processing_time,
        "transmission_time": transmission_time,
        "network_latency": latency,
        "total_delay": total_delay,
        "uav_energy": uav_energy,
        "is_feasible": total_delay != float("inf") and cloud.has_capacity(task)
    }