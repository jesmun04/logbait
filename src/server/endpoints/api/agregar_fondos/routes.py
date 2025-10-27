from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Blueprint, render_template
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, Apuesta, Estadistica


bp = Blueprint('agregar_fondos', __name__, url_prefix='/api')

@bp.route('/agregar_fondos', methods=['POST'])
@login_required
def agregar_fondos():
    data = request.get_json()
    cantidad = float(data['cantidad'])
    
    if cantidad <= 0:
        return jsonify({'error': 'La cantidad debe ser mayor a 0'}), 400
    
    current_user.balance += cantidad
    db.session.commit()
    
    return jsonify({
        'nuevo_balance': current_user.balance,
        'mensaje': f'Se agregaron ${cantidad:.2f} a tu cuenta'
    })

@bp.route('/balance', methods=['GET'])
@login_required
def obtener_balance():
    return jsonify({'balance': current_user.balance})