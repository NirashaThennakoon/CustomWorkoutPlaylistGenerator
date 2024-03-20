import json
from werkzeug.datastructures import Headers


def test_post_user_register(client):
    RESOURCE_URL = "/api/user/register"
    valid = _get_user_json()

    # test with wrong content type
    resp = client.post(RESOURCE_URL, data="notjson")
    assert resp.status_code in (400, 415)

    # test with valid and see that it exists afterward
    resp = client.post(RESOURCE_URL, json=valid)
    print(resp.data)
    assert resp.status_code == 201
        
    # send same data again for 400
    resp = client.post(RESOURCE_URL, json=valid)
    assert resp.status_code == 400

    # remove workout_name field for 400
    valid.pop("email")
    resp = client.post(RESOURCE_URL, json=valid)
    assert resp.status_code == 400

def test_post_user_login(client):
    RESOURCE_URL = "/api/user/login"
    valid = _get_user_json_for_login()
    invalid_email = _get_user_json_with_invalid_email()
    inavlis_pwd = _get_user_json_with_invalid_pwd()

    # test with wrong content type
    resp = client.post(RESOURCE_URL, data="notjson")
    assert resp.status_code in (400, 415)

    # test with valid and see that it exists afterward
    resp = client.post(RESOURCE_URL, json=valid)
    assert resp.status_code == 200
        
    # send unregistered email
    resp = client.post(RESOURCE_URL, json=invalid_email)
    assert resp.status_code == 404

    # send incorrect password
    resp = client.post(RESOURCE_URL, json=inavlis_pwd)
    assert resp.status_code == 401

    # remove workout_name field for 400
    valid.pop("email")
    resp = client.post(RESOURCE_URL, json=valid)
    assert resp.status_code == 400

def test_put_user(client):
    RESOURCE_URL = "/api/user/3"
    valid = _get_user_json()

    # test with wrong content type
    resp = client.put(RESOURCE_URL, data="notjson")
    assert resp.status_code in (400, 415)

    #test with wrong id
    resp = client.put('/api/user/id', json=valid)
    assert resp.status_code == 404
        
    # test with not avaliable id
    resp = client.put('/api/user/10000', json=valid)
    assert resp.status_code == 404
        
    # test with valid
    resp = client.put(RESOURCE_URL, json=valid)
    assert resp.status_code == 200
        
    # remove field
    valid.pop("email")
    resp = client.put('/api/user/3', json=valid)
    assert resp.status_code == 200       
        

def test_delete_user(client):
    #delete valid user
    resp = client.delete('/api/user/2')
    assert resp.status_code == 200
    #delete same user again
    resp = client.delete('/api/user/2')
    assert resp.status_code == 404
    #invalid id
    resp = client.delete('/api/user/id')
    assert resp.status_code == 404

def test_put_api_key(client):
    RESOURCE_URL = "/api/user/update_api_key/3"

    #test with wrong id
    resp = client.put('/api/user/id')
    assert resp.status_code == 404
        
    # test with valid
    resp = client.put(RESOURCE_URL)
    assert resp.status_code == 200
    
def _get_user_json():
    """
    Creates a valid song JSON object to be used for PUT and POST tests.
    """
    return {
        "email": "test2@gmail.com",
        "password": "password",
        "height": 178.0,
        "weight": 56.7,
        "user_type": "admin"
    }

def _get_user_json_for_login():
    """
    Creates a valid song JSON object to be used for PUT and POST tests.
    """
    return {
        "email": 'test-email-1@gmail.com',
        "password": "testPassword1"
    }

def _get_user_json_with_invalid_email():
    """
    Creates a valid song JSON object to be used for PUT and POST tests.
    """
    return {
        "email": "1234@gmail.com",
        "password": "testPassword1"
    }

def _get_user_json_with_invalid_pwd():
    """
    Creates a valid song JSON object to be used for PUT and POST tests.
    """
    return {
        "email": 'test-email-1@gmail.com',
        "password": "1234"
    }
