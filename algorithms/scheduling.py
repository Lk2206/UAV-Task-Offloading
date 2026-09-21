# ==========================================
# Task Scheduling Algorithm
# Priority + Earliest Deadline First
# ==========================================


PRIORITY_VALUE = {
    "High": 3,
    "Medium": 2,
    "Low": 1
}


def schedule_tasks(tasks):
    """
    Schedule tasks using:
    1. Higher priority first
    2. Earlier deadline for equal priority
    """

    scheduled_tasks = sorted(
        tasks,
        key=lambda task: (
            -PRIORITY_VALUE[task.priority],
            task.deadline
        )
    )

    return scheduled_tasks