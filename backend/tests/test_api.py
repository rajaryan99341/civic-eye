import os
import tempfile
import pytest
from app import create_app
from config import Config

@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, "DATABASE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(tmp_path / "uploads"))
    app = create_app(testing=True)
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client

def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json()["product"] == "CIVIC EYE"

def test_registration_and_login(client):
    registered = client.post("/api/auth/register", json={"name":"Test Citizen","email":"test@example.com","password":"Password123"})
    assert registered.status_code == 201
    login = client.post("/api/auth/login", json={"email":"test@example.com","password":"Password123","portal":"citizen"})
    assert login.status_code == 200
    assert login.get_json()["token"]
