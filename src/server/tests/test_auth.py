import json
import pytest
from flask import session
from flask_login import login_user, current_user

def test_user_registration(client, app):
    """Test user registration process"""
    response = client.post('/register', data=dict(
        username='newuser',
        email='newuser@test.com',
        password='password123',
        confirm_password='password123'
    ), follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Registro exitoso' in response.data

def test_user_login(client, test_user):
    """Test user login process"""
    with client:
        response = client.post('/login', data=dict(
            username='test_user',
            password='password123'
        ), follow_redirects=True)
        
        assert response.status_code == 200
        assert session.get('_user_id') is not None
        assert current_user.is_authenticated

def test_user_logout(client, test_user):
    """Test user logout process"""
    with client:
        # Login first
        client.post('/login', data=dict(
            username='test_user',
            password='password123'
        ), follow_redirects=True)
        
        # Then logout
        response = client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        assert current_user.is_anonymous

def test_invalid_login(client):
    """Test login with invalid credentials"""
    response = client.post('/login', data=dict(
        username='nonexistent',
        password='wrongpassword'
    ), follow_redirects=True)
    
    assert response.status_code == 200
    assert current_user.is_anonymous
    # The application flashes messages in Spanish
    assert b'Usuario o contrase\xc3\xb1a incorrectos' in response.data

def test_protected_route_access(client, test_user):
    """Test access to protected routes"""
    # Without login should redirect to login
    response = client.get('/dashboard', follow_redirects=True)
    assert b'Please log in' in response.data
    
    # With login should show dashboard
    with client:
        client.post('/login', data=dict(
            username='test_user',
            password='password123'
        ))
    response = client.get('/dashboard')
    assert response.status_code == 200
    # Dashboard contains a welcome header
    assert b'BIENVENIDO' in response.data