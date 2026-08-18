from fastapi.testclient import TestClient

from src.app import activities, app


client = TestClient(app)


def test_root_redirects_to_frontend():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_catalog():
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == activities
    assert response.json()["Chess Club"]["max_participants"] == 12


def test_signup_adds_participant():
    email = "new-student@mergington.edu"

    response = client.post("/activities/Chess Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert email in activities["Chess Club"]["participants"]


def test_signup_rejects_duplicate_participant():
    email = activities["Chess Club"]["participants"][0]

    response = client.post("/activities/Chess Club/signup", params={"email": email})

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }


def test_signup_rejects_unknown_activity():
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_requires_email():
    response = client.post("/activities/Chess Club/signup")

    assert response.status_code == 422


def test_unregister_removes_participant():
    email = "leaving-student@mergington.edu"
    activities["Chess Club"]["participants"].append(email)

    response = client.delete("/activities/Chess Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
    assert email not in activities["Chess Club"]["participants"]


def test_unregister_rejects_unknown_activity():
    response = client.delete(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_rejects_nonparticipant():
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "not-enrolled@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }


def test_unregister_requires_email():
    response = client.delete("/activities/Chess Club/signup")

    assert response.status_code == 422


def test_signup_listing_and_unregister_share_state():
    email = "state-check@mergington.edu"

    signup_response = client.post(
        "/activities/Science Club/signup", params={"email": email}
    )
    activities_response = client.get("/activities")
    unregister_response = client.delete(
        "/activities/Science Club/signup", params={"email": email}
    )

    assert signup_response.status_code == 200
    assert email in activities_response.json()["Science Club"]["participants"]
    assert unregister_response.status_code == 200
    assert email not in activities["Science Club"]["participants"]