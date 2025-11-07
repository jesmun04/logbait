import json
import pytest
from flask_login import login_user

def test_slots_spin(client, test_user):
    """Test spinning the slot machine"""
    login_user(test_user)
    initial_balance = test_user.balance
    
    response = client.post('/api/tragaperras/apostar', json={
        'cantidad': 100,
        'ganancia': 50,
        'resultado': 'GIRO'
    })
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'nuevo_balance' in data

def test_slots_invalid_bet(client, test_user):
    """Test invalid bet amount in slots"""
    login_user(test_user)
    
    response = client.post('/api/tragaperras/apostar', json={
        'cantidad': -100,
        'ganancia': 0,
        'resultado': 'GIRO'
    })
    
    assert response.status_code == 400

def test_slots_insufficient_funds(client, test_user):
    """Test betting with insufficient funds"""
    login_user(test_user)
    huge_amount = test_user.balance + 1000
    
    response = client.post('/api/tragaperras/apostar', json={
        'cantidad': huge_amount,
        'ganancia': 0,
        'resultado': 'GIRO'
    })
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data