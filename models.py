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
        self.task_id = task_id
        self.uav_id = uav_id
        self.task_type = task_type
        self.size = size
        self.cpu_required = cpu_required
        self.priority = priority
        self.deadline = deadline

    def __str__(self):
        return (
            f"Task {self.task_id} | "
            f"UAV {self.uav_id} | "
            f"{self.task_type} | "
            f"{self.size} MB | "
            f"{self.cpu_required} GHz | "
            f"Priority: {self.priority} | "
            f"Deadline: {self.deadline}s"
        )


class UAV:
    def __init__(
        self,
        uav_id,
        cpu_capacity,
        battery,
        bandwidth
    ):
        self.uav_id = uav_id
        self.cpu_capacity = cpu_capacity
        self.battery = battery
        self.bandwidth = bandwidth

    def __str__(self):
        return (
            f"UAV {self.uav_id} | "
            f"CPU: {self.cpu_capacity} GHz | "
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
        self.server_id = server_id
        self.cpu_capacity = cpu_capacity
        self.max_tasks = max_tasks
        self.bandwidth = bandwidth

        # Current resource usage
        self.used_cpu = 0
        self.current_tasks = 0

    def has_capacity(self, task):
        """Check whether Edge can accept a task."""

        if self.current_tasks >= self.max_tasks:
            return False

        if self.used_cpu + task.cpu_required > self.cpu_capacity:
            return False

        return True

    def allocate(self, task):
        """Allocate resources to a task."""

        self.used_cpu += task.cpu_required
        self.current_tasks += 1

    def __str__(self):
        return (
            f"Edge {self.server_id} | "
            f"CPU: {self.cpu_capacity} GHz | "
            f"Used CPU: {self.used_cpu} GHz | "
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
        self.server_id = server_id
        self.cpu_capacity = cpu_capacity
        self.max_tasks = max_tasks
        self.bandwidth = bandwidth

        # Current resource usage
        self.used_cpu = 0
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

    def __str__(self):
        return (
            f"Cloud {self.server_id} | "
            f"CPU: {self.cpu_capacity} GHz | "
            f"Used CPU: {self.used_cpu} GHz | "
            f"Tasks: {self.current_tasks}/{self.max_tasks} | "
            f"Bandwidth: {self.bandwidth} Mbps"
        )