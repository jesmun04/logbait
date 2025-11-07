from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, SalaMultijugador, UsuarioSala, User

bp = Blueprint('api_multijugador', __name__)

@bp.route('/api/multijugador/salas')
@login_required
def obtener_salas():
    """Obtener lista de salas disponibles"""
    salas = SalaMultijugador.query.filter_by(estado='esperando').all()
    return jsonify([{
        'id': sala.id,
        'nombre': sala.nombre,
        'juego': sala.juego,
        'capacidad': sala.capacidad,
        'jugadores_actuales': sala.jugadores_actuales,
        'apuesta_minima': sala.apuesta_minima,
        'creador': sala.propietario.username
    } for sala in salas])

@bp.route('/api/multijugador/estado-sala/<int:sala_id>')
@login_required
def estado_sala(sala_id):
    """Obtener estado actual de una sala"""
    sala = SalaMultijugador.query.get_or_404(sala_id)
    jugadores = UsuarioSala.query.filter_by(sala_id=sala_id).join(User).all()
    
    return jsonify({
        'sala': {
            'id': sala.id,
            'nombre': sala.nombre,
            'estado': sala.estado,
            'jugadores_actuales': sala.jugadores_actuales,
            'capacidad': sala.capacidad,
            'juego': sala.juego,
            'creador_id': sala.creador_id
        },
        'jugadores': [{
            'id': us.jugador.id,
            'username': us.jugador.username,
            'posicion': us.posicion,
            'es_creador': (us.jugador.id == sala.creador_id)
        } for us in jugadores]
    })

@bp.route('/api/multijugador/iniciar-partida/<int:sala_id>', methods=['POST'])
@login_required
def iniciar_partida(sala_id):
    """Iniciar una partida multijugador"""
    sala = SalaMultijugador.query.get_or_404(sala_id)
    
    # Verificar que el usuario es el creador
    if sala.creador_id != current_user.id:
        return jsonify({'error': 'Solo el creador puede iniciar la partida'}), 403
    
    # Verificar que hay al menos 2 jugadores
    if sala.jugadores_actuales < 2:
        return jsonify({'error': 'Se necesitan al menos 2 jugadores'}), 400
    
    # Cambiar estado de la sala
    sala.estado = 'jugando'
    db.session.commit()
    
    return jsonify({
        'success': True,
        'mensaje': 'Partida iniciada'
    })