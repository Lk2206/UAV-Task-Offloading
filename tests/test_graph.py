"""
Unit tests for Graph Theory and Dijkstra's Shortest Path Algorithm
"""

import pytest
from algorithms.graph import Graph


def test_graph_node_and_edge_insertion():
    g = Graph()
    g.add_node("UAV 1")
    g.add_node("Edge 1")
    g.add_edge("UAV 1", "Edge 1", 2.5)

    assert "UAV 1" in g.get_nodes()
    assert "Edge 1" in g.get_nodes()
    neighbors = g.get_neighbors("UAV 1")
    assert len(neighbors) == 1
    assert neighbors[0] == ("Edge 1", 2.5)


def test_dijkstra_shortest_path_simple():
    g = Graph()
    g.add_edge("A", "B", 1.0)
    g.add_edge("B", "C", 2.0)
    g.add_edge("A", "C", 5.0)

    dist, path = g.get_shortest_path("A", "C")
    assert dist == 3.0
    assert path == ["A", "B", "C"]


def test_dijkstra_unreachable_node():
    g = Graph()
    g.add_edge("UAV 1", "Edge 1", 1.5)
    g.add_node("Isolated Server")

    dist, path = g.get_shortest_path("UAV 1", "Isolated Server")
    assert dist == float("inf")
    assert path == []


def test_dijkstra_rejects_negative_weights():
    g = Graph()
    with pytest.raises(ValueError, match="nonnegative"):
        g.add_edge("UAV 1", "Edge 1", -2.0)


def test_dijkstra_cycle_handling():
    g = Graph()
    g.add_edge("A", "B", 2.0)
    g.add_edge("B", "A", 2.0)
    g.add_edge("B", "C", 1.0)

    dist, path = g.get_shortest_path("A", "C")
    assert dist == 3.0
    assert path == ["A", "B", "C"]
