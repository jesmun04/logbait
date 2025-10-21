from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Blueprint, render_template
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

bp = Blueprint('dashboard', __name__)

@bp.route('/dashboard')
@login_required
def home():
    return render_template('dashboard.html', user=current_user)