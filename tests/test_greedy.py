"""
Unit tests for Greedy Task Offloading Heuristic
"""

import pytest
from models import Task, UAV, EdgeServer, CloudServer
from algorithms.greedy import greedy_offloading


def test_greedy_allocates_lowest_feasible_delay():
    uav = UAV(1, cpu_capacity=2.0, bandwidth=10.0)
    edge = EdgeServer(1, cpu_capacity=10.0, max_tasks=5, bandwidth=100.0)
    cloud = CloudServer(1, cpu_capacity=50.0, max_tasks=20, bandwidth=1000.0)

    # Task requiring 1 GC: Local takes 1 / 2 = 0.5s. Edge takes (100*8)/100 + 1/10 = 8.1s.
    # Local UAV is much faster due to zero transmission delay.
    task = Task(1, 1, "Quick Task", size=100, cpu_required=1.0, priority="Low", deadline=5.0)

    results = greedy_offloading([task], [uav], edge, cloud)
    assert len(results) == 1
    assert results[0]["location"] == "UAV 1"
    assert results[0]["delay"] == 0.5


def test_greedy_capacity_constraints_and_unallocated_reporting():
    # UAV with very small capacity (0.5 GC/s)
    uav = UAV(1, cpu_capacity=0.5, bandwidth=10.0)
    # Edge with max_tasks=1 and capacity 2.0 GC
    edge = EdgeServer(1, cpu_capacity=2.0, max_tasks=1, bandwidth=100.0)
    # Cloud with max_tasks=1 and capacity 2.0 GC
    cloud = CloudServer(1, cpu_capacity=2.0, max_tasks=1, bandwidth=1000.0)

    # 3 tasks requiring 2 GC each
    tasks = [
        Task(1, 1, "Task A", size=10, cpu_required=2.0, priority="High", deadline=5.0),
        Task(2, 1, "Task B", size=10, cpu_required=2.0, priority="High", deadline=5.0),
        Task(3, 1, "Task C", size=10, cpu_required=2.0, priority="High", deadline=5.0),
    ]

    results = greedy_offloading(tasks, [uav], edge, cloud)
    assert len(results) == 3

    allocated = [r for r in results if r["location"] != "Not Allocated"]
    unallocated = [r for r in results if r["location"] == "Not Allocated"]

    # At most 2 tasks can be placed (1 on Edge, 1 on Cloud); 3rd must be Not Allocated
    assert len(allocated) == 2
    assert len(unallocated) == 1
    assert results.metrics["tasks_unallocated"] == 1


def test_greedy_does_not_mutate_original_resource_states():
    uav = UAV(1, cpu_capacity=2.0)
    edge = EdgeServer(1, cpu_capacity=10.0, max_tasks=5, bandwidth=100.0)
    cloud = CloudServer(1, cpu_capacity=50.0, max_tasks=20, bandwidth=1000.0)

    task = Task(1, 1, "Task", size=50, cpu_required=3.0, priority="High", deadline=5.0)

    greedy_offloading([task], [uav], edge, cloud, clone_resources=True)

    # Verify input server objects remain unchanged
    assert edge.used_cpu == 0.0
    assert edge.current_tasks == 0
    assert cloud.used_cpu == 0.0
    assert cloud.current_tasks == 0
    assert uav.used_cpu == 0.0
