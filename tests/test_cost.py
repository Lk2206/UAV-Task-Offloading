"""
Unit tests for Cost, Delay, and Energy calculations
"""

import pytest
from models import Task, UAV, EdgeServer, CloudServer
from cost import (
    calculate_processing_time,
    calculate_transmission_time,
    calculate_uav_cost,
    calculate_edge_cost,
    calculate_cloud_cost
)


def test_processing_time_calculation():
    task = Task(1, 1, "Image", size=100, cpu_required=4.0, priority="High", deadline=5.0)
    # 4 GC / 2 GC/s = 2.0 s
    assert calculate_processing_time(task, 2.0) == 2.0
    # Zero or negative capacity returns infinity
    assert calculate_processing_time(task, 0) == float("inf")
    assert calculate_processing_time(task, -1.0) == float("inf")


def test_transmission_time_calculation():
    # 100 MB * 8 = 800 Mbits / 100 Mbps = 8.0 s
    assert calculate_transmission_time(100.0, 100.0) == 8.0
    # Zero or negative bandwidth returns infinity
    assert calculate_transmission_time(100.0, 0) == float("inf")
    assert calculate_transmission_time(100.0, -10.0) == float("inf")


def test_uav_local_cost_zero_transmission():
    task = Task(1, 1, "Analytics", size=200, cpu_required=2.0, priority="Medium", deadline=4.0)
    uav = UAV(1, cpu_capacity=2.0, battery=90, bandwidth=15)
    cost = calculate_uav_cost(task, uav)

    assert cost["transmission_time"] == 0.0
    assert cost["network_latency"] == 0.0
    assert cost["processing_time"] == 1.0
    assert cost["total_delay"] == 1.0
    assert cost["is_feasible"] is True


def test_edge_cost_includes_network_latency():
    task = Task(1, 1, "Mapping", size=100, cpu_required=5.0, priority="Low", deadline=10.0)
    edge = EdgeServer(1, cpu_capacity=10.0, max_tasks=5, bandwidth=100.0)
    # Transmission = (100 * 8) / 100 = 8.0 s
    # Processing = 5.0 / 10.0 = 0.5 s
    # Latency = 1.5 s -> Total Delay = 8.0 + 1.5 + 0.5 = 10.0 s
    cost = calculate_edge_cost(task, edge, network_latency=1.5)

    assert cost["transmission_time"] == 8.0
    assert cost["network_latency"] == 1.5
    assert cost["processing_time"] == 0.5
    assert cost["total_delay"] == 10.0


def test_cloud_cost_calculation():
    task = Task(1, 1, "Detect", size=50, cpu_required=5.0, priority="High", deadline=5.0)
    cloud = CloudServer(1, cpu_capacity=50.0, max_tasks=20, bandwidth=1000.0)
    # Transmission = (50 * 8) / 1000 = 0.4 s
    # Processing = 5.0 / 50.0 = 0.1 s
    # Latency = 2.5 s -> Total Delay = 0.4 + 2.5 + 0.1 = 3.0 s
    cost = calculate_cloud_cost(task, cloud, network_latency=2.5)

    assert cost["transmission_time"] == 0.4
    assert cost["network_latency"] == 2.5
    assert cost["processing_time"] == 0.1
    assert round(cost["total_delay"], 2) == 3.0
