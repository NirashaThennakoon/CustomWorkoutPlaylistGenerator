"""
    This module is to test functionalities of workout resource
"""
import json
from jsonschema import validate
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
    _check_namespace(client, data)
    _check_control_get_method("collection", client, data)
    _check_control_put_method("edit", client, data)
    _check_control_delete_method("delete", client, data)
    data["workout_id"] == 1

def test_get_workoutItem(client):
    """
        test get workout item request
    """
    #get workout
    response = client.get("/api/workoutItem/3")
    assert response.status_code == 200

    data = json.loads(response.data)
    data["workout list"] == 1


def test_get_workouts(client):
    """
        test get all workouts request
    """
    #get all workouts
    response = client.get(RESOURCE_URL)
    assert response.status_code == 200
    data = json.loads(response.data)
    print(data)
    assert len(data['workout list']) == 5

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
    assert data["@error"]["@message"] == "Workout duration must be a number"
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
    assert resp.status_code == 500

    data = json.loads(resp.data)
    assert data["@error"]["@message"] == "Internal Server Error"

def test_put_workout(client):
    """
        test update workout request
    """
    valid = _get_workout_json()
    invalid_json = _get_invalid_workout_json()

    # test with wrong content type
    resp = client.put(f'{RESOURCE_URL}/3', data="notjson",
                       headers=Headers({"Content-Type": "text"}))
    assert resp.status_code in (400, 415)

    # test with wrong content type
    resp = client.put(f'{RESOURCE_URL}/3', json = {})
    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert data["@error"]["@message"] == "No input data provided"

    #test with wrong id
    resp = client.put(f'{RESOURCE_URL}/id', json=valid)
    assert resp.status_code == 404
    # test with not avaliable id
    resp = client.put(f'{RESOURCE_URL}/10000', json=valid)
    assert resp.status_code == 404
    # test with valid
    resp = client.put(f'{RESOURCE_URL}/3', json=valid)
    assert resp.status_code == 204
    data = json.loads(resp.data)
    assert data["message"] == "Workout updated successfully"
    # remove field
    valid.pop("workout_name")
    resp = client.put(f'{RESOURCE_URL}/3', json=valid)
    assert resp.status_code == 400

    #invalid intensity
    resp = client.put(f'{RESOURCE_URL}/3', json=invalid_json)
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

    resp = client.put(f'{RESOURCE_URL}/3', json=valid)
    assert resp.status_code == 400

    data = json.loads(resp.data)
    assert data["@error"]["@message"] == "Invalid input data"

def test_delete_workout(client):
    """
        test delete workout request
    """
    #delete workout with valid id
    resp = client.delete(f'{RESOURCE_URL}/2')
    assert resp.status_code == 204
    data = json.loads(resp.data)
    assert data["message"] == "Workout deleted successfully"

    #delete same data
    resp = client.delete(f'{RESOURCE_URL}/2')
    assert resp.status_code == 403

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

def _check_namespace(client, response):
    """
    Checks that the "custWorkoutPlaylistGen" namespace is found from the response body, and
    that its "name" attribute is a URL that can be accessed.
    """

    ns_href = response["@namespaces"]["custWorkoutPlaylistGen"]["name"]
    print(ns_href)
    resp = client.get(ns_href)
    assert resp.status_code == 200

def _check_control_get_method(ctrl, client, obj):
    """
    Checks a GET type control from a JSON object be it root document or an item
    in a collection. Also checks that the URL of the control can be accessed.
    """

    href = obj["@controls"][ctrl]["href"]
    resp = client.get(href)
    print(href)
    assert resp.status_code == 200

def _check_control_delete_method(ctrl, client, obj):
    """
    Checks a DELETE type control from a JSON object be it root document or an
    item in a collection. Checks the contrl's method in addition to its "href".
    Also checks that using the control results in the correct status code of 204.
    """

    href = obj["@controls"][ctrl]["href"]
    method = obj["@controls"][ctrl]["method"].lower()
    assert method == "delete"
    resp = client.delete(href)
    assert resp.status_code == 200

def _check_control_put_method(ctrl, client, obj):
    """
    Checks a PUT type control from a JSON object be it root document or an item
    in a collection. In addition to checking the "href" attribute, also checks
    that method, encoding and schema can be found from the control. Also
    validates a valid sensor against the schema of the control to ensure that
    they match. Finally checks that using the control results in the correct
    status code of 204.
    """

    ctrl_obj = obj["@controls"][ctrl]
    href = ctrl_obj["href"]
    method = ctrl_obj["method"].lower()
    encoding = ctrl_obj["encoding"].lower()
    schema = ctrl_obj["schema"]
    assert method == "put"
    assert encoding == "json"
    body = _get_workout_json()
    body["workout_name"] = obj["workout_name"]
    validate(body, schema)
    resp = client.put(href, json=body)
    assert resp.status_code == 200

def _check_control_post_method(ctrl, client, obj):
    """
    Checks a POST type control from a JSON object be it root document or an item
    in a collection. In addition to checking the "href" attribute, also checks
    that method, encoding and schema can be found from the control. Also
    validates a valid sensor against the schema of the control to ensure that
    they match. Finally checks that using the control results in the correct
    status code of 201.
    """

    ctrl_obj = obj["@controls"][ctrl]
    href = ctrl_obj["href"]
    method = ctrl_obj["method"].lower()
    encoding = ctrl_obj["encoding"].lower()
    schema = ctrl_obj["schema"]
    assert method == "post"
    assert encoding == "json"
    body = _get_workout_json()
    validate(body, schema)
    resp = client.post(href, json=body)
    assert resp.status_code == 201
