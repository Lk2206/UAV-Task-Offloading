"""
Models for UAV Task Offloading Simulation
Units:
    - Task size: Megabytes (MB)
    - CPU required: Gigacycles (GC = 10^9 CPU cycles)
    - CPU capacity: Gigacycles per second (GC/s)
    - Bandwidth: Megabits per second (Mbps)
    - Latency & Deadlines: Seconds (s)
    - Battery: Percentage (%)
"""

import copy


class Task:
    def __init__(
        self,
        task_id,
        uav_id,
        task_type,
        size,
        cpu_required,
        priority,
        deadline
    ):
        self.task_id = int(task_id)
        self.uav_id = int(uav_id)
        self.task_type = str(task_type)
        self.size = float(size)                  # in MB
        self.cpu_required = float(cpu_required)  # in Gigacycles (GC)
        self.priority = str(priority)            # 'High', 'Medium', 'Low'
        self.deadline = float(deadline)          # in seconds

    def clone(self):
        """Create an independent copy of this task."""
        return Task(
            self.task_id,
            self.uav_id,
            self.task_type,
            self.size,
            self.cpu_required,
            self.priority,
            self.deadline
        )

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "uav_id": self.uav_id,
            "task_type": self.task_type,
            "size": self.size,
            "cpu_required": self.cpu_required,
            "priority": self.priority,
            "deadline": self.deadline
        }

    def __str__(self):
        return (
            f"Task {self.task_id} | "
            f"UAV {self.uav_id} | "
            f"{self.task_type} | "
            f"{self.size} MB | "
            f"{self.cpu_required} GC | "
            f"Priority: {self.priority} | "
            f"Deadline: {self.deadline}s"
        )


class UAV:
    def __init__(
        self,
        uav_id,
        cpu_capacity,
        battery=100.0,
        bandwidth=15.0,
        max_tasks=5
    ):
        self.uav_id = int(uav_id)
        self.cpu_capacity = float(cpu_capacity)  # in GC/s
        self.battery = float(battery)            # in %
        self.bandwidth = float(bandwidth)        # in Mbps (for uplink)
        self.max_tasks = int(max_tasks)

        # Dynamic resource usage
        self.used_cpu = 0.0
        self.current_tasks = 0

    def has_capacity(self, task):
        """Check whether the originating UAV can execute the task locally."""
        if self.current_tasks >= self.max_tasks:
            return False
        if self.used_cpu + task.cpu_required > self.cpu_capacity:
            return False
        return True

    def allocate(self, task):
        """Allocate resources on the UAV for local processing."""
        self.used_cpu += task.cpu_required
        self.current_tasks += 1

    def reset(self):
        """Reset allocated resources."""
        self.used_cpu = 0.0
        self.current_tasks = 0

    def clone(self):
        """Deep copy UAV state."""
        cloned = UAV(
            self.uav_id,
            self.cpu_capacity,
            self.battery,
            self.bandwidth,
            self.max_tasks
        )
        cloned.used_cpu = self.used_cpu
        cloned.current_tasks = self.current_tasks
        return cloned

    def to_dict(self):
        return {
            "uav_id": self.uav_id,
            "cpu_capacity": self.cpu_capacity,
            "battery": self.battery,
            "bandwidth": self.bandwidth,
            "max_tasks": self.max_tasks,
            "used_cpu": self.used_cpu,
            "current_tasks": self.current_tasks
        }

    def __str__(self):
        return (
            f"UAV {self.uav_id} | "
            f"CPU: {self.cpu_capacity} GC/s | "
            f"Battery: {self.battery}% | "
            f"Bandwidth: {self.bandwidth} Mbps"
        )


class EdgeServer:
    def __init__(
        self,
        server_id,
        cpu_capacity,
        max_tasks,
        bandwidth
    ):
        self.server_id = int(server_id)
        self.cpu_capacity = float(cpu_capacity)  # in GC/s
        self.max_tasks = int(max_tasks)
        self.bandwidth = float(bandwidth)        # in Mbps

        # Dynamic resource usage
        self.used_cpu = 0.0
        self.current_tasks = 0

    def has_capacity(self, task):
        """Check whether Edge server can accept a task."""
        if self.current_tasks >= self.max_tasks:
            return False
        if self.used_cpu + task.cpu_required > self.cpu_capacity:
            return False
        return True

    def allocate(self, task):
        """Allocate resources to a task."""
        self.used_cpu += task.cpu_required
        self.current_tasks += 1

    def reset(self):
        """Reset allocated resources."""
        self.used_cpu = 0.0
        self.current_tasks = 0

    def clone(self):
        """Deep copy EdgeServer state."""
        cloned = EdgeServer(
            self.server_id,
            self.cpu_capacity,
            self.max_tasks,
            self.bandwidth
        )
        cloned.used_cpu = self.used_cpu
        cloned.current_tasks = self.current_tasks
        return cloned

    def to_dict(self):
        return {
            "server_id": self.server_id,
            "cpu_capacity": self.cpu_capacity,
            "max_tasks": self.max_tasks,
            "bandwidth": self.bandwidth,
            "used_cpu": self.used_cpu,
            "current_tasks": self.current_tasks
        }

    def __str__(self):
        return (
            f"Edge {self.server_id} | "
            f"CPU: {self.cpu_capacity} GC/s | "
            f"Used CPU: {self.used_cpu} GC/s | "
            f"Tasks: {self.current_tasks}/{self.max_tasks} | "
            f"Bandwidth: {self.bandwidth} Mbps"
        )


class CloudServer:
    def __init__(
        self,
        server_id,
        cpu_capacity,
        max_tasks,
        bandwidth
    ):
        self.server_id = int(server_id)
        self.cpu_capacity = float(cpu_capacity)  # in GC/s
        self.max_tasks = int(max_tasks)
        self.bandwidth = float(bandwidth)        # in Mbps

        # Dynamic resource usage
        self.used_cpu = 0.0
        self.current_tasks = 0

    def has_capacity(self, task):
        """Check whether Cloud can accept a task."""
        if self.current_tasks >= self.max_tasks:
            return False
        if self.used_cpu + task.cpu_required > self.cpu_capacity:
            return False
        return True

    def allocate(self, task):
        """Allocate resources to a task."""
        self.used_cpu += task.cpu_required
        self.current_tasks += 1

    def reset(self):
        """Reset allocated resources."""
        self.used_cpu = 0.0
        self.current_tasks = 0

    def clone(self):
        """Deep copy CloudServer state."""
        cloned = CloudServer(
            self.server_id,
            self.cpu_capacity,
            self.max_tasks,
            self.bandwidth
        )
        cloned.used_cpu = self.used_cpu
        cloned.current_tasks = self.current_tasks
        return cloned

    def to_dict(self):
        return {
            "server_id": self.server_id,
            "cpu_capacity": self.cpu_capacity,
            "max_tasks": self.max_tasks,
            "bandwidth": self.bandwidth,
            "used_cpu": self.used_cpu,
            "current_tasks": self.current_tasks
        }

    def __str__(self):
        return (
            f"Cloud {self.server_id} | "
            f"CPU: {self.cpu_capacity} GC/s | "
            f"Used CPU: {self.used_cpu} GC/s | "
            f"Tasks: {self.current_tasks}/{self.max_tasks} | "
            f"Bandwidth: {self.bandwidth} Mbps"
        )