# ==========================================
# Weighted Graph for UAV Task Offloading
# ==========================================


class Graph:
    def __init__(self):
        # Adjacency list
        self.graph = {}

    def add_node(self, node):
        """Add a node to the graph."""

        if node not in self.graph:
            self.graph[node] = []

    def add_edge(self, source, destination, weight):
        """Add a weighted directed edge."""

        self.add_node(source)
        self.add_node(destination)

        self.graph[source].append(
            (destination, weight)
        )

    def display(self):
        """Display the graph."""

        print("\n===== UAV NETWORK GRAPH =====")

        for node in self.graph:
            print(f"{node} -> ", end="")

            for destination, weight in self.graph[node]:
                print(
                    f"{destination} ({weight}s)",
                    end=" | "
                )

            print()
    def dijkstra(self, start):
        """
        Find the shortest path from the start node
        to every other node using Dijkstra's algorithm.
        """

        # Initialize distances
        distances = {}

        for node in self.graph:
            distances[node] = float("inf")

        distances[start] = 0

        # Track visited nodes
        visited = set()

        while len(visited) < len(self.graph):

            # Find the unvisited node with
            # the smallest distance
            current_node = None
            current_distance = float("inf")

            for node in self.graph:

                if node not in visited and distances[node] < current_distance:
                    current_node = node
                    current_distance = distances[node]

            # If no reachable node remains
            if current_node is None:
                break

            # Mark current node as visited
            visited.add(current_node)

            # Relax neighbouring edges
            for neighbour, weight in self.graph[current_node]:

                new_distance = (
                    distances[current_node] + weight
                )

                if new_distance < distances[neighbour]:
                    distances[neighbour] = new_distance

        return distances