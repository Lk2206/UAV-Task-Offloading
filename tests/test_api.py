"""
Integration tests for Flask Web API
"""

import pytest
import json
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_route(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"UAV Task Offloading Optimizer" in res.data


def test_health_api(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert data["app"] == "UAV-Task-Offloading-Optimizer"


def test_config_api(client):
    res = client.get("/api/config")
    assert res.status_code == 200
    data = res.get_json()
    assert "default_config" in data
    assert "presets" in data
    assert "algorithms" in data


def test_simulate_greedy(client):
    payload = {
        "algorithm": "greedy",
        "config": {
            "num_uavs": 3,
            "num_tasks": 4,
            "use_benchmark_workload": True
        }
    }
    res = client.post("/api/simulate", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert "allocations" in data
    assert "metrics" in data
    assert len(data["allocations"]) == 4


def test_simulate_invalid_params_validation(client):
    payload = {
        "algorithm": "greedy",
        "config": {
            "num_uavs": "invalid_number"
        }
    }
    res = client.post("/api/simulate", json=payload)
    assert res.status_code == 400
    data = res.get_json()
    assert "error" in data


def test_compare_endpoint(client):
    payload = {
        "config": {
            "num_uavs": 3,
            "num_tasks": 4,
            "use_benchmark_workload": True
        }
    }
    res = client.post("/api/compare", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert "results" in data
    assert "greedy" in data["results"]
    assert "dp" in data["results"]
    assert "edf" in data["results"]
