"""
    This is module is to test functionalities of User resource
"""
import json
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
    assert data["message"] == "Email already exists"

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
    assert data["error"] == "Failed to register user"

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
    assert data["message"] == "No such user in the system"

    # send incorrect password
    resp = client.post(resource_url, json=inavlis_pwd)
    assert resp.status_code == 401
    data = json.loads(resp.data)
    assert data["message"] == "Invalid password"

    # remove email field for 400
    valid.pop("email")
    resp = client.post(resource_url, json=valid)
    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert data["message"] == "Invalid input data for user login"

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
    assert data["message"] == "No input data provided"

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
    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert data["message"] == "Mocked exception"

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
