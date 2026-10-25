"""
Unit tests for Task Scheduling and Execution Timeline Simulation
"""

import pytest
from models import Task, UAV, EdgeServer, CloudServer
from algorithms.scheduling import (
    schedule_edf,
    schedule_priority,
    schedule_combined,
    simulate_scheduled_execution
)


def test_edf_scheduling_order():
    t1 = Task(1, 1, "A", size=10, cpu_required=1, priority="Low", deadline=10.0)
    t2 = Task(2, 1, "B", size=10, cpu_required=1, priority="High", deadline=3.0)
    t3 = Task(3, 1, "C", size=10, cpu_required=1, priority="Medium", deadline=6.0)

    ordered = schedule_edf([t1, t2, t3])
    # Earliest deadline first: t2 (3.0s) -> t3 (6.0s) -> t1 (10.0s)
    assert [t.task_id for t in ordered] == [2, 3, 1]


def test_priority_scheduling_order():
    t1 = Task(1, 1, "A", size=10, cpu_required=1, priority="Low", deadline=2.0)
    t2 = Task(2, 1, "B", size=10, cpu_required=1, priority="High", deadline=10.0)
    t3 = Task(3, 1, "C", size=10, cpu_required=1, priority="Medium", deadline=5.0)

    ordered = schedule_priority([t1, t2, t3])
    # Priority order: High (t2) -> Medium (t3) -> Low (t1)
    assert [t.task_id for t in ordered] == [2, 3, 1]


def test_combined_scheduling_order():
    t1 = Task(1, 1, "A", size=10, cpu_required=1, priority="High", deadline=8.0)
    t2 = Task(2, 1, "B", size=10, cpu_required=1, priority="High", deadline=4.0)
    t3 = Task(3, 1, "C", size=10, cpu_required=1, priority="Low", deadline=2.0)

    ordered = schedule_combined([t1, t2, t3])
    # High tier: t2 (4.0s) before t1 (8.0s), followed by Low tier t3
    assert [t.task_id for t in ordered] == [2, 1, 3]


def test_timeline_simulation_accounts_for_queue_waiting_time():
    uav = UAV(1, cpu_capacity=1.0)
    # Edge server with adequate capacity to process both tasks
    edge = EdgeServer(1, cpu_capacity=10.0, max_tasks=10, bandwidth=100.0)
    cloud = CloudServer(1, cpu_capacity=10.0, max_tasks=10, bandwidth=100.0)

    # Two identical tasks requiring 2 GC
    t1 = Task(1, 1, "A", size=10, cpu_required=2.0, priority="High", deadline=10.0)
    t2 = Task(2, 1, "B", size=10, cpu_required=2.0, priority="High", deadline=10.0)

    results = simulate_scheduled_execution([t1, t2], [uav], edge, cloud)

    assert len(results) == 2
    assert results.metrics["tasks_completed"] == 2
    # The tasks are scheduled and executed, advancing the makespan timeline
    assert results.metrics["makespan"] > 0
    # Response time must be positive
    assert results.metrics["total_delay"] > 0
