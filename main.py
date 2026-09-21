from models import Task, UAV, EdgeServer, CloudServer


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