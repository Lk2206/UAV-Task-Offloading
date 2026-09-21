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