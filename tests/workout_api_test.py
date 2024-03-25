"""
    This module is to test functionalities of workout resource
"""
import json
from werkzeug.datastructures import Headers

RESOURCE_URL = '/api/workout'

def test_get_workout(client):
    """
        test get workout request
    """
    #get workout
    response = client.get("/api/workout/1")
    assert response.status_code == 200

    data = json.loads(response.data)
    assert len(data) == 1

def test_get_workouts(client):
    """
        test get all workouts request
    """
    #get all workouts
    response = client.get(RESOURCE_URL)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 5

def test_post_workout(client):
    """
        test create workout request
    """
    valid = _get_workout_json()
    invalid_intensity_json = _get_invalid_workout_json()

    # test with wrong content type
    resp = client.post(RESOURCE_URL, data="notjson")
    assert resp.status_code in (400, 415)

    #test with wrong intensity
    resp = client.post(RESOURCE_URL, json=invalid_intensity_json)
    assert resp.status_code == 400

    # test with valid and see that it exists afterward
    resp = client.post(RESOURCE_URL, json=valid)
    assert resp.status_code == 201

    # invalid duration type
    valid["duration" ] = 10
    resp = client.post(RESOURCE_URL, json=valid)
    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert data["message"] == "Workout duration must be a float"
    # remove workout_name field for 400
    valid.pop("workout_name")
    resp = client.post(RESOURCE_URL, json=valid)
    assert resp.status_code == 400
    data = json.loads(resp.data)

def test_post_workout_with_db_error(client, mocker):
    """
        test create workout request when db error occurs
    """
    valid = _get_workout_json()
    mock_commit = mocker.patch('extensions.db.session.commit')
    # Make commit raise an exception
    mock_commit.side_effect = ValueError("Mocked exception")

    resp = client.post(RESOURCE_URL, json=valid)
    assert resp.status_code == 400

    data = json.loads(resp.data)
    assert data["message"] == "Mocked exception"

def test_put_workout(client):
    """
        test update workout request
    """
    valid = _get_workout_json()
    invalid_json = _get_invalid_workout_json()

    # test with wrong content type
    resp = client.put(f'{RESOURCE_URL}/1', data="notjson",
                       headers=Headers({"Content-Type": "text"}))
    assert resp.status_code in (400, 415)

    # test with wrong content type
    resp = client.put(f'{RESOURCE_URL}/1', json = {})
    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert data["message"] == "No input data provided"

    #test with wrong id
    resp = client.put(f'{RESOURCE_URL}/id', json=valid)
    assert resp.status_code == 404
    # test with not avaliable id
    resp = client.put(f'{RESOURCE_URL}/10000', json=valid)
    assert resp.status_code == 404
    # test with valid
    resp = client.put(f'{RESOURCE_URL}/1', json=valid)
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["message"] == "Workout updated successfully"
    # remove field
    valid.pop("workout_name")
    resp = client.put(f'{RESOURCE_URL}/1', json=valid)
    assert resp.status_code == 400

    #invalid intensity
    resp = client.put(f'{RESOURCE_URL}/1', json=invalid_json)
    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert data["message"] == "Invalid workout intensity"

def test_put_workout_with_db_error(client, mocker):
    """
        test update workout request when db error occurs
    """
    valid = _get_workout_json()
    mock_commit = mocker.patch('extensions.db.session.commit')
    # Make commit raise an exception
    mock_commit.side_effect = ValueError("Mocked exception")

    resp = client.put(f'{RESOURCE_URL}/1', json=valid)
    assert resp.status_code == 400

    data = json.loads(resp.data)
    assert data["message"] == "Invalid input data: Mocked exception"

def test_delete_workout(client):
    """
        test delete workout request
    """
    #delete workout with valid id
    resp = client.delete(f'{RESOURCE_URL}/2')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["message"] == "Workout deleted successfully"

    #delete same data
    resp = client.delete(f'{RESOURCE_URL}/2')
    assert resp.status_code == 404

    #delete data with invalid id
    resp = client.delete(f'{RESOURCE_URL}/2')
    assert resp.status_code == 404

def _get_workout_json():
    """
    Creates a valid workout JSON object to be used for PUT and POST tests.
    """
    return {
        "workout_name": "Sample Workout",
        "duration": 30.0,
        "workout_intensity": "slow",
        "equipment": "Dumbbells",
        "workout_type": "Strength"
    }

def _get_invalid_workout_json():
    """
    Creates an invalid workout JSON object to be used for PUT and POST tests.
    """
    return {
        "workout_name": "Sample Workout",
        "duration": 30.0,
        "workout_intensity": "invalid",
        "equipment": "Dumbbells",
        "workout_type": "Strength"
    }
