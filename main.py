from models import Task, UAV, EdgeServer, CloudServer
from cost import (
    calculate_uav_cost,
    calculate_edge_cost,
    calculate_cloud_cost
)
from algorithms.graph import Graph
from algorithms.greedy import greedy_offloading
from algorithms.scheduling import schedule_tasks

# =============================
# Create UAVs
# =============================

uav1 = UAV(
    uav_id=1,
    cpu_capacity=2,
    battery=80,
    bandwidth=10
)

uav2 = UAV(
    uav_id=2,
    cpu_capacity=3,
    battery=70,
    bandwidth=15
)

uav3 = UAV(
    uav_id=3,
    cpu_capacity=2.5,
    battery=90,
    bandwidth=12
)

# Store all UAVs in a list
uavs = [
    uav1,
    uav2,
    uav3
]

# =============================
# Create Servers
# =============================

edge1 = EdgeServer(
    server_id=1,
    cpu_capacity=10,
    max_tasks=8,
    bandwidth=100
)

cloud1 = CloudServer(
    server_id=1,
    cpu_capacity=50,
    max_tasks=20,
    bandwidth=1000
)


# =============================
# Create Tasks
# =============================

tasks = [

    Task(
        task_id=1,
        uav_id=1,
        task_type="Image Processing",
        size=500,
        cpu_required=4,
        priority="High",
        deadline=5
    ),

    Task(
        task_id=2,
        uav_id=2,
        task_type="Object Detection",
        size=250,
        cpu_required=3,
        priority="High",
        deadline=4
    ),

    Task(
        task_id=3,
        uav_id=3,
        task_type="Mapping",
        size=800,
        cpu_required=5,
        priority="Medium",
        deadline=8
    ),

    Task(
        task_id=4,
        uav_id=1,
        task_type="Surveillance",
        size=100,
        cpu_required=1,
        priority="Low",
        deadline=10
    )
]


# =============================
# Display Simulation
# =============================

print("\n===== UAV TASK OFFLOADING SIMULATION =====\n")

print("UAVs:")
print(uav1)
print(uav2)
print(uav3)

print("\nServers:")
print(edge1)
print(cloud1)

print("\nTasks:")

for task in tasks:
    print(task)

# =============================
# Calculate Cost and Delay
# =============================

print("\n===== COST AND DELAY ANALYSIS =====")

for task in tasks:

    # Find the UAV that generated the task
    if task.uav_id == uav1.uav_id:
        source_uav = uav1

    elif task.uav_id == uav2.uav_id:
        source_uav = uav2

    else:
        source_uav = uav3

    # Calculate costs
    uav_cost = calculate_uav_cost(task, source_uav)
    edge_cost = calculate_edge_cost(task, edge1)
    cloud_cost = calculate_cloud_cost(task, cloud1)

    print(f"\nTask {task.task_id}: {task.task_type}")

    print(
        f"  {uav_cost['location']}: "
        f"{uav_cost['total_delay']:.2f} s"
    )

    print(
        f"  {edge_cost['location']}: "
        f"{edge_cost['total_delay']:.2f} s"
    )

    print(
        f"  {cloud_cost['location']}: "
        f"{cloud_cost['total_delay']:.2f} s"
    )

# =============================
# Create UAV Network Graph
# =============================

network = Graph()

# Add communication links
network.add_edge("UAV 1", "Edge 1", 2.0)
network.add_edge("UAV 2", "Edge 1", 1.5)
network.add_edge("UAV 3", "Edge 1", 2.2)

network.add_edge("Edge 1", "Cloud 1", 2.5)

# Display graph
network.display()
# =============================
# Dijkstra Shortest Paths
# =============================

shortest_paths = network.dijkstra("UAV 1")

print("\n===== DIJKSTRA SHORTEST PATHS =====")

for node, distance in shortest_paths.items():

    if distance == float("inf"):
        print(f"UAV 1 -> {node}: Not reachable")

    else:
        print(
            f"UAV 1 -> {node}: "
            f"{distance:.2f} seconds"
        )

# =============================
# Greedy Task Offloading
# =============================

greedy_results = greedy_offloading(
    tasks,
    uavs,
    edge1,
    cloud1
)

print("\n===== GREEDY OFFLOADING RESULTS =====")

total_greedy_delay = 0

for result in greedy_results:

    print(
        f"Task {result['task_id']} "
        f"({result['task_type']}) "
        f"-> {result['location']} "
        f"| Delay: {result['delay']:.2f} s"
    )

    if result["delay"] != float("inf"):
        total_greedy_delay += result["delay"]


print(
    f"\nTotal Greedy Delay: "
    f"{total_greedy_delay:.2f} seconds"
)
# =============================
# Task Scheduling
# =============================

scheduled_tasks = schedule_tasks(tasks)

print("\n===== TASK SCHEDULING =====")

for position, task in enumerate(
    scheduled_tasks,
    start=1
):

    print(
        f"{position}. "
        f"Task {task.task_id} "
        f"({task.task_type}) | "
        f"Priority: {task.priority} | "
        f"Deadline: {task.deadline}s"
    )