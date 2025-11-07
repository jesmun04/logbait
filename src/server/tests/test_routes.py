def test_index_route(client):
    """Test that the index route returns a 200 status code"""
    response = client.get('/')
    assert response.status_code == 200

def test_login_route(client):
    """Test that the login route returns a 200 status code"""
    response = client.get('/login')
    assert response.status_code == 200

def test_register_route(client):
    """Test that the register route returns a 200 status code"""
    response = client.get('/register')
    assert response.status_code == 200