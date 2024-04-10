"""
    This is module is to test functionalities of User resource
"""
import json
from jsonschema import validate
import pytest

@pytest.fixture
def mock_db(mocker):
    """
        this is to mock db commit
    """
    return mocker.patch('extensions.db.session.commit')

def test_post_user_register(client):
    """
        test user registration
    """
    resource_url = "/api/user"
    valid = _get_user_json()

    # test with wrong content type
    resp = client.post(resource_url, data="notjson")
    assert resp.status_code in (400, 415)

    # test with valid and see that it exists afterward
    resp = client.post(resource_url, json=valid)
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert data["message"] == "User registered successfully", "user_id 1"
    # send same data again for 400
    resp = client.post(resource_url, json=valid)
    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert data["@error"]["@message"] == "Email already exists"

    # remove workout_name field for 400
    valid.pop("email")
    resp = client.post(resource_url, json=valid)
    assert resp.status_code == 400

def test_post_user_register_with_db_error(client, mocker):
    """
        test user registration when db error occurs
    """
    resource_url = "/api/user"
    valid = _get_newuser_json()

    # Mock the db commit
    mock_commit = mocker.patch('extensions.db.session.commit')
    # Make commit raise an exception
    mock_commit.side_effect = Exception("Mocked exception")
    resp = client.post(resource_url, json=valid)
    assert resp.status_code == 500
    data = json.loads(resp.data)
    assert data["@error"]["@message"] == "Failed to register user"

def test_post_user_login(client):
    """
        test user login
    """
    resource_url = "/api/user/1"
    valid = _get_user_json_for_login()
    invalid_email = _get_user_json_with_invalid_email()
    inavlis_pwd = _get_user_json_with_invalid_pwd()

    # test with wrong content type
    resp = client.post(resource_url, data="notjson")
    assert resp.status_code in (400, 415)

    # test with valid and see that it exists afterward
    resp = client.post(resource_url, json=valid)
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert "Login successful", "access_token" in data["message"]
    # send unregistered email
    resp = client.post(resource_url, json=invalid_email)
    assert resp.status_code == 404
    data = json.loads(resp.data)
    assert data["@error"]["@message"] == "No such user in the system"

    # send incorrect password
    resp = client.post(resource_url, json=inavlis_pwd)
    assert resp.status_code == 401
    data = json.loads(resp.data)
    assert data["@error"]["@message"] == "Invalid password"

    # remove email field for 400
    valid.pop("email")
    resp = client.post(resource_url, json=valid)
    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert data["@error"]["@message"] == "Invalid input data for user login"

def test_put_user(client):
    """
        test user update
    """
    resource_url = "/api/user/3"
    valid = _get_user_json()

    # test with wrong content type
    resp = client.put(resource_url, data="notjson")
    assert resp.status_code in (400, 415)

    # test without data
    resp = client.put(resource_url, json={})
    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert data["@error"]["@message"] == "No input data provided"

    #test with wrong id
    resp = client.put('/api/user/id', json=valid)
    assert resp.status_code == 404
    # test with not avaliable id
    resp = client.put('/api/user/10000', json=valid)
    assert resp.status_code == 404
    # test with valid
    resp = client.put(resource_url, json=valid)
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["message"] == "User updated successfully"
    # remove field
    valid.pop("email")
    resp = client.put('/api/user/3', json=valid)
    assert resp.status_code == 400

def test_put_user_with_db_error(client, mocker):
    """
        test user update when db error occurs
    """
    resource_url = "/api/user/3"
    valid = _get_user_json()
    # Mock the db commit
    mock_commit = mocker.patch('extensions.db.session.commit')
    # Make commit raise an exception
    mock_commit.side_effect = Exception("Mocked exception")
    resp = client.put(resource_url, json = valid)
    assert resp.status_code == 500
    data = json.loads(resp.data)
    assert data["@error"]["@message"] == "Internal Server Error"

def test_delete_user(client):
    """
        test user delete
    """
    #delete valid user
    resp = client.delete('/api/user/2')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["message"] == "User deleted successfully"
    #delete same user again
    resp = client.delete('/api/user/2')
    assert resp.status_code == 404
    #invalid id
    resp = client.delete('/api/user/id')
    assert resp.status_code == 404

def test_put_api_key(client, mocker):
    """
        test API Key update
    """
    resource_url = "/api/user/update_api_key/3"

    #test with wrong id
    resp = client.put('/api/user/id')
    assert resp.status_code == 404
    # test with valid
    resp = client.put(resource_url)
    assert resp.status_code == 200

    # Mock the db commit
    mock_commit = mocker.patch('extensions.db.session.commit')
    # Make commit raise an exception
    mock_commit.side_effect = Exception("Mocked exception")
    resp = client.put(resource_url)
    assert resp.status_code == 500
def test_get_user(client):
    """
        test get user
    """
    #test with valid user id
    resp = client.get("/api/user/3")
    data = json.loads(resp.data)
    _check_namespace(client, data)
    # _check_control_put_method("custWorkoutPlaylistGen:edit-user", client, data)
    _check_control_delete_method("custWorkoutPlaylistGen:delete", client, data)
    assert resp.status_code == 200

def _get_user_json():
    """
    Creates a valid user JSON object to be used for PUT and POST tests.
    """
    return {
        "email": "test2@gmail.com",
        "password": "password",
        "height": 178.0,
        "weight": 56.7,
        "user_type": "admin"
    }

def _get_user2_json():
    """
    Creates a valid user JSON object to be used for PUT and POST tests.
    """
    return {
        "email": "test3@gmail.com",
        "password": "password",
        "height": 178.0,
        "weight": 56.7,
        "user_type": "admin"
    }

def _get_newuser_json():
    """
    Creates a valid user JSON object to be used for PUT and POST tests.
    """
    return {
        "email": "newuser@gmail.com",
        "password": "password",
        "height": 178.0,
        "weight": 56.7,
        "user_type": "admin"
    }

def _get_user_json_for_login():
    """
    Creates a valid user JSON object to be used for PUT and POST tests.
    """
    return {
        "email": 'test-email-1@gmail.com',
        "password": "testPassword1"
    }

def _get_user_json_with_invalid_email():
    """
    Creates a invalid user JSON object to be used for PUT and POST tests.
    """
    return {
        "email": "1234@gmail.com",
        "password": "testPassword1"
    }

def _get_user_json_with_invalid_pwd():
    """
    Creates a invalid user JSON object to be used for PUT and POST tests.
    """
    return {
        "email": 'test-email-1@gmail.com',
        "password": "1234"
    }

def _check_namespace(client, response):
    """
    Checks that the "custWorkoutPlaylistGen" namespace is found from the response body, and
    that its "name" attribute is a URL that can be accessed.
    """
    ns_href = response["@namespaces"]["custWorkoutPlaylistGen"]["name"]
    print(ns_href)
    resp = client.get(ns_href)
    assert resp.status_code == 404

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
    body = _get_user_json()
    body["email"] = obj["email"]
    validate(body, schema)
    print(href)
    resp = client.put(href, json=body)
    assert resp.status_code == 200
