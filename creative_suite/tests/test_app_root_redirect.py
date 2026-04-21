from fastapi.testclient import TestClient
from creative_suite.app import create_app


def test_root_redirects_to_studio():
    client = TestClient(create_app(), follow_redirects=False)
    r = client.get("/")
    assert r.status_code == 307
    assert r.headers["location"] == "/studio"
