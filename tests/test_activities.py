from fastapi.testclient import TestClient
import copy
import urllib.parse

from src import app as app_module

client = TestClient(app_module.app)


import pytest


@pytest.fixture(autouse=True)
def restore_activities():
    # Make a deep copy of the activities and restore after each test to avoid side effects
    orig = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(orig)


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # Basic sanity: expect Chess Club to be present
    assert "Chess Club" in data


def test_signup_and_unregister_flow():
    activity = "Chess Club"
    email = "testuser@example.com"

    # Ensure the email is not already in participants
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert email not in data[activity]["participants"]

    # Sign up
    signup_url = f"/activities/{urllib.parse.quote(activity)}/signup?email={urllib.parse.quote(email)}"
    resp = client.post(signup_url)
    assert resp.status_code == 200
    body = resp.json()
    assert "Signed up" in body.get("message", "")

    # Confirm participant shows up
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert email in data[activity]["participants"]

    # Unregister
    unregister_url = f"/activities/{urllib.parse.quote(activity)}/unregister?email={urllib.parse.quote(email)}"
    resp = client.post(unregister_url)
    assert resp.status_code == 200
    body = resp.json()
    assert "Unregistered" in body.get("message", "")

    # Confirm participant removed
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert email not in data[activity]["participants"]


def test_unregister_not_signed_up_fails():
    activity = "Programming Class"
    email = "not-signed-up@example.com"
    unregister_url = f"/activities/{urllib.parse.quote(activity)}/unregister?email={urllib.parse.quote(email)}"
    resp = client.post(unregister_url)
    assert resp.status_code == 400
    data = resp.json()
    assert data.get("detail") == "Student is not signed up for this activity"
 