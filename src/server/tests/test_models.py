import pytest
from models import User, db

def test_user_creation(test_user):
    """Test user model creation and password hashing"""
    assert test_user.username == "test_user"
    assert test_user.email == "test@test.com"
    assert test_user.check_password("password123")
    assert not test_user.check_password("wrongpassword")

def test_user_balance(test_user):
    """Test user balance operations"""
    initial_balance = test_user.balance
    test_user.add_funds(1000)
    assert test_user.balance == initial_balance + 1000
    
    test_user.subtract_funds(500)
    assert test_user.balance == initial_balance + 500

def test_user_stats(test_user):
    """Test user statistics tracking"""
    initial_games = test_user.games_played
    initial_wins = test_user.games_won
    
    test_user.add_game_played()
    assert test_user.games_played == initial_games + 1
    
    test_user.add_game_won()
    assert test_user.games_won == initial_wins + 1