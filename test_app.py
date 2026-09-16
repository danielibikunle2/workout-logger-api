import os
import tempfile

import pytest

os.environ["API_KEY"] = "test-secret-key"

import app as app_module  # noqa: E402  (must import after setting API_KEY)

HEADERS = {"X-API-Key": "test-secret-key"}


@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()
    app_module.DB_NAME = db_path

    conn = app_module.sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE Workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exercise TEXT NOT NULL,
            duration_minutes INTEGER,
            date TEXT NOT NULL,
            notes TEXT
        );
    """)
    conn.commit()
    conn.close()

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as test_client:
        yield test_client

    os.close(db_fd)
    os.unlink(db_path)


def test_health_check(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "message" in resp.get_json()


def test_log_workout_success(client):
    resp = client.post(
        "/workouts",
        json={"exercise": "Squats", "duration_minutes": 30, "notes": "Leg day"},
        headers=HEADERS,
    )
    assert resp.status_code == 201
    assert "id" in resp.get_json()


def test_log_workout_missing_exercise(client):
    resp = client.post("/workouts", json={"duration_minutes": 30}, headers=HEADERS)
    assert resp.status_code == 400


def test_log_workout_invalid_duration(client):
    resp = client.post(
        "/workouts",
        json={"exercise": "Squats", "duration_minutes": "not-a-number"},
        headers=HEADERS,
    )
    assert resp.status_code == 400


def test_log_workout_negative_duration(client):
    resp = client.post(
        "/workouts",
        json={"exercise": "Squats", "duration_minutes": -5},
        headers=HEADERS,
    )
    assert resp.status_code == 400


def test_log_workout_no_json_body(client):
    resp = client.post(
        "/workouts", data="not json", content_type="text/plain", headers=HEADERS
    )
    assert resp.status_code == 400


def test_log_workout_requires_api_key(client):
    resp = client.post("/workouts", json={"exercise": "Squats"})
    assert resp.status_code == 401


def test_get_workouts_empty(client):
    resp = client.get("/workouts")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_get_workouts_after_logging(client):
    client.post(
        "/workouts", json={"exercise": "Bench Press", "duration_minutes": 20}, headers=HEADERS
    )
    resp = client.get("/workouts")
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]["exercise"] == "Bench Press"


def test_filter_workouts_by_exercise(client):
    client.post("/workouts", json={"exercise": "Squats", "duration_minutes": 10}, headers=HEADERS)
    client.post("/workouts", json={"exercise": "Deadlift", "duration_minutes": 15}, headers=HEADERS)
    resp = client.get("/workouts?exercise=Squats")
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]["exercise"] == "Squats"


def test_delete_workout_success(client):
    post_resp = client.post(
        "/workouts", json={"exercise": "Rows", "duration_minutes": 10}, headers=HEADERS
    )
    workout_id = post_resp.get_json()["id"]
    del_resp = client.delete(f"/workouts/{workout_id}", headers=HEADERS)
    assert del_resp.status_code == 200


def test_delete_nonexistent_workout(client):
    resp = client.delete("/workouts/9999", headers=HEADERS)
    assert resp.status_code == 404


def test_delete_requires_api_key(client):
    post_resp = client.post(
        "/workouts", json={"exercise": "Rows", "duration_minutes": 10}, headers=HEADERS
    )
    workout_id = post_resp.get_json()["id"]
    resp = client.delete(f"/workouts/{workout_id}")
    assert resp.status_code == 401


def test_summary_empty(client):
    resp = client.get("/workouts/summary")
    assert resp.get_json() == []


def test_summary_aggregation(client):
    client.post("/workouts", json={"exercise": "Squats", "duration_minutes": 10}, headers=HEADERS)
    client.post("/workouts", json={"exercise": "Squats", "duration_minutes": 20}, headers=HEADERS)
    resp = client.get("/workouts/summary")
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]["exercise"] == "Squats"
    assert data[0]["times_done"] == 2
    assert data[0]["total_minutes"] == 30
