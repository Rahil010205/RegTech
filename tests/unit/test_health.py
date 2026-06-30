"""Health endpoint tests."""

def test_liveness(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["message"] == "ok"


def test_readiness(client):
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json()["message"] == "ready"
