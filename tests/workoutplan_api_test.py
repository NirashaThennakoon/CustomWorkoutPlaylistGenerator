"""
    This module is to test functionalities of workout plan resource
"""
import json
import pytest
from werkzeug.datastructures import Headers

RESOURCE_URL = '/api/workoutPlan'

@pytest.fixture
def mock_post(mocker):
    """
    Mock requests.psot method
    """
    return mocker.patch('requests.post')

def test_get_workoutplan(client):
    """
        test get workput plan request
    """
    #get workout plan by id
    response = client.get(f'{RESOURCE_URL}/1')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert len(data) == 1

def test_post_workout_plan(client, mock_post):
    """
        test create workput plan request
    """
    valid_data = _get_json_for_post()

    # Mock the response of the internal post request
    mock_post.return_value.json.return_value = {"playlist_id": 2}

    # test with wrong content type
    resp = client.post(RESOURCE_URL, data="notjson", headers=Headers({"Content-Type": "text"}))
    assert resp.status_code in (400, 415)

    # test with wrong content type
    resp = client.post(RESOURCE_URL, json={})
    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert data["message"] == "Invalid input data on Create Workout Plan"

    # Test with valid data
    resp = client.post(RESOURCE_URL, json=valid_data)
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert data["message"] == "Workout plan created successfully", "workout_plan_id 1"

    # Remove workout_name field for 400
    valid_data.pop("plan_name")
    resp = client.post(RESOURCE_URL, json=valid_data)
    assert resp.status_code == 400

    # Remove workout_name field for 400
    invalid = _get_json_without_workout_ids()
    resp = client.post(RESOURCE_URL, json=invalid)
    assert resp.status_code == 400

def test_put_workout_plan(client):
    """
        test update workput plan request
    """
    valid = _get_workout_plan_json()

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
    assert data["message"] == "Workout plan updated successfully"
    # remove field
    valid.pop("plan_name")
    resp = client.put(f'{RESOURCE_URL}/1', json=valid)
    assert resp.status_code == 400

def test_put_workout_plan_with_db_error(client, mocker):
    """
        test update workput plan request when db error occurs
    """
    valid = _get_workout_plan_json()
    # Mock the db commit
    mock_commit = mocker.patch('extensions.db.session.commit')
    # Make commit raise an exception
    mock_commit.side_effect = ValueError("Mocked exception")

    resp = client.put(f'{RESOURCE_URL}/1', json=valid)
    assert resp.status_code == 400

    data = json.loads(resp.data)
    assert data["message"] == "Mocked exception"

def test_delete_workout_plan(client):
    """
        test delete workput plan request
    """
    #delete workout plan with valid id
    resp = client.delete(f'{RESOURCE_URL}/3')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["message"] == "Workout plan deleted successfully"
    #delete same data
    resp = client.delete(f'{RESOURCE_URL}/3')
    assert resp.status_code == 404

    #delete workout plan with wrong id
    resp = client.delete(f'{RESOURCE_URL}/id')
    assert resp.status_code == 404

def _get_workout_plan_json():
    """
    Creates a valid workout plan JSON object to be used for PUT and POST tests.
    """
    return {
        "plan_name": "Sample Workout Plan",
        "duration": 30.0,
        "user_id": 1,
        "playlist_id": 1
    }

def _get_json_for_post():
    """
    Creates a valid workout plan JSON object to be used for POST tests.
    """
    return {
        "plan_name": "test-workout-plan-1",
        "workout_ids": [1, 3 ,5],
        "duration": 78.9
    }

def _get_json_without_workout_ids():
    """
    Creates a invalid workout plan JSON object to be used for POST tests.
    """
    return {
        "plan_name": "test-workout-plan-1"
    }
