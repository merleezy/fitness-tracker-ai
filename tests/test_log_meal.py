from flask import url_for

from app import app, db
from app.models import Meal, User


def create_user(username: str, email: str) -> User:
    user = User(
        username=username,
        name="Test User",
        email=email,
    )
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    return user


def test_log_meal_authorized(client):
    with app.app_context():
        user = create_user("alice", "alice@example.com")
        user_id = user.id
        username = user.username

    with client.session_transaction() as session:
        session["user_id"] = user_id
        session["username"] = username

    response = client.post(
        f"/log_meal/{username}",
        data={
            "name": "Lunch",
            "calories": 600,
            "protein": 30,
            "carbs": 50,
            "fats": 20,
        },
    )

    assert response.status_code == 302
    with app.app_context():
        assert Meal.query.filter_by(user_id=user_id).count() == 1

    with app.test_request_context():
        expected_location = url_for("user_dashboard", username=username)
    assert response.headers["Location"].endswith(expected_location)


def test_log_meal_unauthorized_redirects_with_flash(client):
    with app.app_context():
        owner = create_user("bob", "bob@example.com")
        intruder = create_user("charlie", "charlie@example.com")
        owner_username = owner.username
        owner_id = owner.id
        intruder_username = intruder.username
        intruder_id = intruder.id

    with client.session_transaction() as session:
        session["user_id"] = intruder_id
        session["username"] = intruder_username

    response = client.get(f"/log_meal/{owner_username}")

    assert response.status_code == 302
    with app.test_request_context():
        expected_location = url_for("user_dashboard", username=intruder_username)
    assert response.headers["Location"].endswith(expected_location)

    with client.session_transaction() as session:
        assert session.get("_flashes")
        categories_and_messages = session["_flashes"]
        assert ("danger", "Unauthorized access.") in categories_and_messages

    with app.app_context():
        assert Meal.query.filter_by(user_id=owner_id).count() == 0
