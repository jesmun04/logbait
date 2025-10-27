from flask import request, jsonify, Blueprint
from flask_login import login_required, current_user
from models import db

bp = Blueprint('blackjack_api', __name__, url_prefix='/api/blackjack')

@bp.route('/apostar', methods=['POST'])
@login_required
def apostar():
    try:
        data = request.get_json()
        cantidad = float(data.get('cantidad', 0))
        ganancia = float(data.get('ganancia', 0))
        resultado = data.get('resultado', '')
        
        # Calcular el cambio neto en el balance
        cambio_neto = ganancia - cantidad
        
        # Actualizar el balance del usuario
        current_user.balance += cambio_neto
        db.session.commit()
        
        return jsonify({
            'nuevo_balance': current_user.balance,
            'cambio_neto': cambio_neto,
            'mensaje': f'Apuesta de blackjack procesada: {resultado}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error procesando apuesta: {str(e)}'}), 400