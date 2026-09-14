import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture(autouse=True)
def restore_activities_state():
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(copy.deepcopy(original))


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_seed_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    payload = response.json()
    assert "Chess Club" in payload
    chess_club = payload["Chess Club"]
    assert chess_club["description"] == "Learn strategies and compete in chess tournaments"
    assert chess_club["schedule"] == "Fridays, 3:30 PM - 5:00 PM"
    assert chess_club["max_participants"] == 12
    assert chess_club["participants"] == ["michael@mergington.edu", "daniel@mergington.edu"]


def test_signup_for_activity_success(client):
    activity_name = "Chess Club"
    email = "student@mergington.edu"
    encoded_activity = quote(activity_name)

    response = client.post(f"/activities/{encoded_activity}/signup?email={email}")

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_signup_for_activity_unknown_activity_returns_404(client):
    response = client.post("/activities/Unknown%20Club/signup?email=student@mergington.edu")

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_for_activity_duplicate_student_returns_400(client):
    response = client.post("/activities/Chess%20Club/signup?email=michael@mergington.edu")

    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}


def test_signup_for_activity_full_activity_returns_400(client):
    activity_name = "Chess Club"
    activities[activity_name]["participants"] = [
        f"student{i}@mergington.edu" for i in range(activities[activity_name]["max_participants"])
    ]

    response = client.post(f"/activities/{quote(activity_name)}/signup?email=new@mergington.edu")

    assert response.status_code == 400
    assert response.json() == {"detail": "Activity is full"}


def test_signup_for_activity_missing_email_returns_422(client):
    response = client.post("/activities/Chess%20Club/signup")

    assert response.status_code == 422


def test_unregister_from_activity_success(client):
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    encoded_activity = quote(activity_name)

    response = client.delete(f"/activities/{encoded_activity}/signup?email={email}")

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]


def test_unregister_from_activity_unknown_activity_returns_404(client):
    response = client.delete("/activities/Unknown%20Club/signup?email=student@mergington.edu")

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_from_activity_student_not_signed_up_returns_404(client):
    response = client.delete("/activities/Chess%20Club/signup?email=notregistered@mergington.edu")

    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up for this activity"}


def test_unregister_from_activity_missing_email_returns_422(client):
    response = client.delete("/activities/Chess%20Club/signup")

    assert response.status_code == 422
