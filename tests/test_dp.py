"""
Unit tests for Dynamic Programming (MMKP Formulation)
"""

import pytest
from models import Task, UAV, EdgeServer, CloudServer
from algorithms.dynamic_programming import (
    dynamic_programming_offloading,
    DPInstanceTooLargeError
)


def test_dp_empty_workload():
    uav = UAV(1, cpu_capacity=2.0)
    edge = EdgeServer(1, cpu_capacity=10.0, max_tasks=5, bandwidth=100.0)
    cloud = CloudServer(1, cpu_capacity=50.0, max_tasks=20, bandwidth=1000.0)

    result = dynamic_programming_offloading([], [uav], edge, cloud)
    assert len(result) == 0
    assert result.metrics["total_delay"] == 0.0
    assert result.metrics["tasks_completed"] == 0


def test_dp_manually_verifiable_optimal_instance():
    """
    Manually verifiable 2-task instance:
    - Task 1: cpu_required = 3 GC, size = 10 MB
    - Task 2: cpu_required = 3 GC, size = 10 MB
    - UAV has capacity 2 GC/s -> Local capacity 2 GC (neither task can run locally)
    - Edge has capacity 4 GC -> Can only fit ONE task (3 <= 4, but 3 + 3 = 6 > 4)
    - Cloud has capacity 10 GC -> Can fit remaining task

    On Edge: delay is (10*8)/100 + 3/10 = 0.8 + 0.3 = 1.1s.
    On Cloud: delay is (10*8)/1000 + 3/50 = 0.08 + 0.06 = 0.14s.
    Wait: On Cloud bandwidth is faster, so Cloud delay is 0.14s, Edge delay is 1.1s.
    Therefore, the optimal DP assignment will place one task on Cloud (0.14s)
    and one on Edge (1.1s), with sum = 1.24s.
    Both tasks cannot be placed on Cloud if Cloud capacity was limited, but here Cloud has 10 GC.
    Let's constrain Cloud capacity to 3 GC as well!
    If Cloud capacity = 3 GC, and Edge capacity = 3 GC:
    Exactly 1 task on Edge and 1 task on Cloud!
    """
    uav = UAV(1, cpu_capacity=2.0)
    edge = EdgeServer(1, cpu_capacity=3.0, max_tasks=5, bandwidth=100.0)
    cloud = CloudServer(1, cpu_capacity=3.0, max_tasks=5, bandwidth=1000.0)

    t1 = Task(1, 1, "Task1", size=10, cpu_required=3.0, priority="High", deadline=5.0)
    t2 = Task(2, 1, "Task2", size=10, cpu_required=3.0, priority="High", deadline=5.0)

    res = dynamic_programming_offloading([t1, t2], [uav], edge, cloud, discretization_step=1.0)

    assert len(res) == 2
    locations = {res[0]["location"], res[1]["location"]}
    # Must use both Edge and Cloud because neither alone has capacity for 6 GC
    assert "Edge 1" in locations
    assert "Cloud 1" in locations
    assert res.metrics["tasks_completed"] == 2
    assert res.metrics["tasks_unallocated"] == 0


def test_dp_unallocated_reporting_when_capacity_exceeded():
    uav = UAV(1, cpu_capacity=1.0)
    edge = EdgeServer(1, cpu_capacity=1.0, max_tasks=1, bandwidth=100.0)
    cloud = CloudServer(1, cpu_capacity=1.0, max_tasks=1, bandwidth=1000.0)

    # 4 tasks requiring 2 GC each; no node can fit any task
    tasks = [
        Task(i, 1, f"Task{i}", size=10, cpu_required=2.0, priority="Low", deadline=5.0)
        for i in range(1, 5)
    ]

    res = dynamic_programming_offloading(tasks, [uav], edge, cloud, discretization_step=1.0)
    assert len(res) == 4
    # All tasks must be reported as unallocated
    for alloc in res:
        assert alloc["location"] == "Not Allocated"
        assert alloc["status"] == "Infeasible"
    assert res.metrics["tasks_unallocated"] == 4


def test_dp_rejects_excessively_large_instances():
    uav = UAV(1, cpu_capacity=2.0)
    edge = EdgeServer(1, cpu_capacity=10.0, max_tasks=5, bandwidth=100.0)
    cloud = CloudServer(1, cpu_capacity=50.0, max_tasks=20, bandwidth=1000.0)

    # 30 tasks exceeds MAX_RECOMMENDED_TASKS
    tasks = [
        Task(i, 1, f"Task{i}", size=10, cpu_required=1.0, priority="Low", deadline=5.0)
        for i in range(1, 35)
    ]

    with pytest.raises(DPInstanceTooLargeError, match="exceeds DP threshold"):
        dynamic_programming_offloading(tasks, [uav], edge, cloud)
