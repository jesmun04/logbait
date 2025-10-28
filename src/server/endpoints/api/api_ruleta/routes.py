from flask import request, jsonify, Blueprint, render_template
from flask_login import login_required, current_user
from models import db, Apuesta,EstadisticaRuleta

# Blueprint para las rutas de la ruleta
bp = Blueprint('api_ruleta', __name__, url_prefix='/api/ruleta')

@bp.route('/api/ruleta/state', methods=['GET'])
@login_required
def get_state():
    """Obtiene el estado actual de la ruleta del usuario"""
    try:
        # Obtener estadísticas del usuario para ruleta
        stats = EstadisticaRuleta.query.filter_by(user_id=current_user.id).first()
        
        if not stats:
            stats = EstadisticaRuleta(
                user_id=current_user.id,
                spins=0,
                bet_cents=0,
                win_cents=0,
                returned_cents=0,
                net_cents=0
            )
            db.session.add(stats)
            db.session.commit()
        
        return jsonify({
            'balance': int(current_user.balance * 100),  # Convertir a céntimos
            'stats': {
                'spins': stats.spins,
                'bet_cents': stats.bet_cents,
                'win_cents': stats.win_cents,
                'returned_cents': stats.returned_cents,
                'net_cents': stats.net_cents
            },
            'ok': True
        })
        
    except Exception as e:
        return jsonify({'error': f'Error obteniendo estado: {str(e)}'}), 400

@bp.route('/api/ruleta/place', methods=['POST'])
@login_required
def place_bets():
    """Coloca las apuestas y reserva el dinero"""
    try:
        data = request.get_json()
        bets = data.get('bets', [])
        min_cell = data.get('min_cell', 20)
        
        # Validar datos
        if not bets:
            return jsonify({'error': 'No hay apuestas para procesar'}), 400
        
        # Calcular total apostado en céntimos
        total_bet_cents = sum(bet['amount'] for bet in bets)
        total_bet_euros = total_bet_cents / 100
        
        # Verificar apuesta mínima por celda
        for bet in bets:
            if bet['amount'] < min_cell:
                return jsonify({'error': f'Apuesta mínima por celda: {min_cell}¢'}), 400
        
        # Verificar fondos suficientes
        if total_bet_euros > current_user.balance:
            return jsonify({'error': 'Fondos insuficientes'}), 400
        
        # Reservar el dinero (restar del balance)
        current_user.balance -= total_bet_euros
        
        # Crear registro de apuesta (pendiente de resultado)
        apuesta = Apuesta(
            user_id=current_user.id,
            juego='ruleta',
            cantidad=total_bet_euros,
            ganancia=0,  # Pendiente del resultado
            resultado='PENDIENTE',
            detalles={'bets': bets, 'estado': 'apostado'}
        )
        db.session.add(apuesta)
        db.session.commit()
        
        return jsonify({
            'balance': int(current_user.balance * 100),  # En céntimos
            'total_bet': total_bet_cents,
            'apuesta_id': apuesta.id,
            'mensaje': f'Apuestas colocadas: {total_bet_euros:.2f}€'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error colocando apuestas: {str(e)}'}), 400

@bp.route('/api/ruleta/spin', methods=['POST'])
@login_required
def spin_ruleta():
    """Realiza un giro de ruleta y liquida las apuestas"""
    try:
        data = request.get_json()
        bets = data.get('bets', [])
        result_number = data.get('result', 0)  # Número ganador (0-36)
        
        if not bets:
            return jsonify({'error': 'No hay apuestas para liquidar'}), 400
        
        # Pagos por tipo de apuesta
        PAYOUT = {
            'straight': 35,  # Pleno
            'split': 17,     # Caballo
            'street': 11,    # Calle
            'corner': 8,     # Esquina
            'line': 5,       # Seisena
            'dozen': 2,      # Docena
            'column': 2,     # Columna
            'even': 1        # Apuestas simples
        }
        
        # Números rojos en ruleta europea
        REDS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
        
        total_win_cents = 0
        total_returned_cents = 0
        total_bet_cents = sum(bet['amount'] for bet in bets)
        
        # Liquidar cada apuesta
        for bet in bets:
            bet_type = bet['type']
            bet_amount = bet['amount']
            covered_numbers = set(bet['set'])
            
            # Verificar si la apuesta gana
            if result_number in covered_numbers:
                # Para apuestas "even" (rojo/negro, par/impar, etc.)
                if bet_type == 'even':
                    # Validar condiciones específicas para apuestas even
                    bet_wins = False
                    label = bet.get('label', '').lower()
                    
                    if 'rojo' in label and result_number in REDS:
                        bet_wins = True
                    elif 'negro' in label and result_number not in REDS and result_number != 0:
                        bet_wins = True
                    elif 'par' in label and result_number % 2 == 0 and result_number != 0:
                        bet_wins = True
                    elif 'impar' in label and result_number % 2 == 1:
                        bet_wins = True
                    elif '1-18' in label and 1 <= result_number <= 18:
                        bet_wins = True
                    elif '19-36' in label and 19 <= result_number <= 36:
                        bet_wins = True
                    
                    if bet_wins:
                        total_win_cents += bet_amount * PAYOUT[bet_type]
                        total_returned_cents += bet_amount
                
                # Para otras apuestas (straight, split, street, etc.)
                else:
                    total_win_cents += bet_amount * PAYOUT.get(bet_type, 0)
                    total_returned_cents += bet_amount
        
        # Convertir a euros
        total_win_euros = total_win_cents / 100
        total_returned_euros = total_returned_cents / 100
        total_net_euros = total_win_euros + total_returned_euros - (total_bet_cents / 100)
        
        # Actualizar balance del usuario
        current_user.balance += total_net_euros
        
        # Actualizar estadísticas de ruleta
        stats = EstadisticaRuleta.query.filter_by(user_id=current_user.id).first()
        if not stats:
            stats = EstadisticaRuleta(user_id=current_user.id)
            db.session.add(stats)
        
        stats.spins += 1
        stats.bet_cents += total_bet_cents
        stats.win_cents += total_win_cents
        stats.returned_cents += total_returned_cents
        stats.net_cents += int(total_net_euros * 100)
        
        # Actualizar última apuesta
        apuesta = Apuesta.query.filter_by(
            user_id=current_user.id, 
            juego='ruleta', 
            resultado='PENDIENTE'
        ).order_by(Apuesta.id.desc()).first()
        
        if apuesta:
            apuesta.ganancia = total_win_euros
            apuesta.resultado = f'Número {result_number} - Ganancia: {total_win_euros:.2f}€'
            apuesta.detalles = {
                'bets': bets,
                'result_number': result_number,
                'win_cents': total_win_cents,
                'returned_cents': total_returned_cents
            }
        
        db.session.commit()
        
        return jsonify({
            'balance': int(current_user.balance * 100),  # En céntimos
            'stats': {
                'spins': stats.spins,
                'bet_cents': stats.bet_cents,
                'win_cents': stats.win_cents,
                'returned_cents': stats.returned_cents,
                'net_cents': stats.net_cents
            },
            'result': result_number,
            'win_cents': total_win_cents,
            'returned_cents': total_returned_cents,
            'mensaje': f'¡Sale el número {result_number}! Ganancia: {total_win_euros:.2f}€'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error en el giro: {str(e)}'}), 400

@bp.route('/api/account/state', methods=['GET'])
@login_required
def account_state():
    """Estado global de la cuenta (para el poll del frontend)"""
    try:
        stats = EstadisticaRuleta.query.filter_by(user_id=current_user.id).first()
        
        return jsonify({
            'ok': True,
            'balance': int(current_user.balance * 100),  # En céntimos
            'balance_float': float(current_user.balance),  # En euros
            'ruleta_stats': {
                'spins': stats.spins if stats else 0,
                'bet_cents': stats.bet_cents if stats else 0,
                'win_cents': stats.win_cents if stats else 0,
                'returned_cents': stats.returned_cents if stats else 0,
                'net_cents': stats.net_cents if stats else 0
            } if stats else None
        })
        
    except Exception as e:
        return jsonify({'error': f'Error obteniendo estado de cuenta: {str(e)}'}), 400