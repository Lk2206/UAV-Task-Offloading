"""
Unit tests for the Unified Simulator and Comparison engine
"""

import pytest
from simulation.simulator import Simulator, generate_random_workload


def test_workload_generator_deterministic_seed():
    tasks1 = generate_random_workload(num_tasks=6, num_uavs=3, seed=123)
    tasks2 = generate_random_workload(num_tasks=6, num_uavs=3, seed=123)
    tasks3 = generate_random_workload(num_tasks=6, num_uavs=3, seed=999)

    assert len(tasks1) == 6
    assert [t.size for t in tasks1] == [t.size for t in tasks2]
    assert [t.cpu_required for t in tasks1] == [t.cpu_required for t in tasks2]
    # Different seed produces different workload
    assert [t.size for t in tasks1] != [t.size for t in tasks3]


def test_compare_all_uses_identical_workload():
    sim = Simulator()
    comp = sim.compare_all()

    assert "greedy" in comp["results"]
    assert "edf" in comp["results"]
    assert "priority" in comp["results"]
    assert "combined" in comp["results"]
    assert "dp" in comp["results"]

    # All algorithms should have executed on the same number of tasks
    workload_len = len(comp["workload"])
    assert len(comp["results"]["greedy"]["allocations"]) == workload_len
    assert len(comp["results"]["edf"]["allocations"]) == workload_len
    assert len(comp["results"]["dp"]["allocations"]) == workload_len


def test_simulator_network_topology():
    sim = Simulator()
    topo = sim.get_network_topology()

    assert "nodes" in topo
    assert "edges" in topo
    assert len(topo["nodes"]) >= 5 # 3 UAVs, 1 Edge, 1 Cloud
    assert len(topo["edges"]) >= 3 # Links connecting UAVs to Edge and Edge to Cloud
