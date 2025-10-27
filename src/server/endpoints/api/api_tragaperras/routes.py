from flask import request, jsonify, Blueprint
from flask_login import login_required, current_user
from models import db

bp_api_tragaperras = Blueprint('api_tragaperras', __name__, url_prefix='/api/tragaperras')

@bp_api_tragaperras.route('/apostar', methods=['POST'])
@login_required
def apostar():
    data = request.get_json()
    cantidad = float(data['cantidad'])
    ganancia = float(data['ganancia'])
    resultado = data['resultado']
    
    # Verificar fondos
    if cantidad > current_user.balance:
        return jsonify({'error': 'Fondos insuficientes'}), 400
    
    # Actualizar balance
    current_user.balance = current_user.balance - cantidad + ganancia
    
    # Registrar apuesta
    apuesta = Apuesta(
        user_id=current_user.id,
        juego='tragaperras',
        cantidad=cantidad,
        resultado=resultado,
        ganancia=ganancia
    )
    db.session.add(apuesta)
    
    # Actualizar estadísticas
    stats = Estadistica.query.filter_by(user_id=current_user.id, juego='tragaperras').first()
    if not stats:
        stats = Estadistica(user_id=current_user.id, juego='tragaperras')
        db.session.add(stats)
    
    stats.partidas_jugadas += 1
    stats.apuesta_total += cantidad
    stats.ganancia_total += (ganancia - cantidad)
    
    if ganancia > cantidad:
        stats.partidas_ganadas += 1
    
    db.session.commit()
    
    return jsonify({
        'nuevo_balance': current_user.balance,
        'mensaje': f'Apuesta de tragaperras procesada: {resultado}'
    })
