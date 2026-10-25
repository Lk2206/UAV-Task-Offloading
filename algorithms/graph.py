"""
Weighted Graph and Dijkstra's Shortest Path Algorithm for UAV Network Routing

Complexity Analysis:
    - Graph Representation: Adjacency list storing outgoing edges.
      Space Complexity: O(V + E) where V is the number of nodes (UAVs, Edge, Cloud)
      and E is the number of communication links.
    - Dijkstra's Algorithm (Min-Heap Priority Queue):
      Time Complexity: O((V + E) log V).
        * Each vertex is extracted from the heap at most once: O(V log V).
        * Each directed edge is traversed at most once, performing a heap push: O(E log V).
      Space Complexity: O(V) for distance table, visited set, and min-heap.
"""

import heapq


class Graph:
    def __init__(self):
        # Adjacency list mapping node -> list of (destination, weight)
        self.graph = {}

    def add_node(self, node):
        """Add a node to the graph if it does not already exist."""
        if node not in self.graph:
            self.graph[node] = []

    def add_edge(self, source, destination, weight):
        """
        Add a weighted directed edge from source to destination.
        Validates that the weight is nonnegative.
        """
        if weight < 0:
            raise ValueError(f"Dijkstra requires nonnegative weights. Got {weight} on edge {source} -> {destination}")

        self.add_node(source)
        self.add_node(destination)
        self.graph[source].append((destination, float(weight)))

    def get_nodes(self):
        """Return all nodes in the graph."""
        return list(self.graph.keys())

    def get_neighbors(self, node):
        """Return outgoing edges for a given node."""
        return self.graph.get(node, [])

    def display(self):
        """Display the graph adjacency structure."""
        print("\n===== UAV NETWORK GRAPH =====")
        for node in self.graph:
            print(f"{node} -> ", end="")
            for destination, weight in self.graph[node]:
                print(f"{destination} ({weight:.2f}s)", end=" | ")
            print()

    def dijkstra(self, start, return_paths=False):
        """
        Dijkstra's shortest path algorithm using a min-heap priority queue.
        Supports unreachable nodes and path reconstruction.

        Parameters:
            start: Start node identifier
            return_paths (bool): If True, returns (distances, paths).
                                 If False, returns distances dict (backward compatible).

        Returns:
            distances: dict of {node: float_distance}
            paths (optional): dict of {node: [path_nodes]}
        """
        if start not in self.graph:
            self.add_node(start)

        # Initialize distances with infinity
        distances = {node: float("inf") for node in self.graph}
        previous = {node: None for node in self.graph}
        distances[start] = 0.0

        # Priority queue stores tuples of (current_distance, node)
        pq = [(0.0, start)]

        while pq:
            current_dist, current_node = heapq.heappop(pq)

            # Skip outdated entries in min-heap
            if current_dist > distances[current_node]:
                continue

            for neighbor, weight in self.graph[current_node]:
                new_dist = current_dist + weight
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    previous[neighbor] = current_node
                    heapq.heappush(pq, (new_dist, neighbor))

        # Reconstruct paths
        paths = {}
        for node in self.graph:
            if distances[node] == float("inf"):
                paths[node] = []
            else:
                path = []
                curr = node
                while curr is not None:
                    path.append(curr)
                    curr = previous[curr]
                path.reverse()
                paths[node] = path

        if return_paths:
            return distances, paths
        return distances

    def get_shortest_path(self, start, target):
        """
        Return the shortest distance and reconstructed path from start to target.
        Returns:
            (distance, [node_sequence])
            If unreachable: (float('inf'), [])
        """
        distances, paths = self.dijkstra(start, return_paths=True)
        dist = distances.get(target, float("inf"))
        path = paths.get(target, [])
        return dist, path