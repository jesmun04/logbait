import json
import random
from datetime import datetime

from flask_login import current_user
from flask_socketio import join_room, leave_room, emit

from models import db, SalaMultijugador, UsuarioSala, PartidaMultijugador


def register_poker_handlers(socketio, app):
    """
    Se llama desde routes.py en @bp.record_once.
    Aquí definimos todos los eventos Socket.IO para el póker multijugador.
    """

    # ===========================
    #   HELPERS INTERNOS
    # ===========================

    def _nombre_room_poker(sala_id: int) -> str:
        return f"poker_{sala_id}"

    def _crear_mazo():
        palos = ['♠', '♥', '♦', '♣']
        valores = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        return [{'valor': v, 'palo': p} for p in palos for v in valores]

    def _obtener_o_crear_partida(sala: SalaMultijugador) -> PartidaMultijugador:
        partida = (
            PartidaMultijugador.query
            .filter_by(sala_id=sala.id, estado='activa')
            .order_by(PartidaMultijugador.fecha_inicio.desc())
            .first()
        )

        if partida is None:
            partida = PartidaMultijugador(
                sala_id=sala.id,
                estado='activa',
                datos_juego=json.dumps({
                    'juego': 'poker',
                    'fase': 'esperando',
                    'cartas_comunitarias': [],
                    'jugadores': {},
                    'bote': 0.0,
                    'ganador': None,
                    'ultima_actualizacion': datetime.utcnow().isoformat()
                })
            )
            db.session.add(partida)
            db.session.commit()

        return partida

    def _cargar_estado(partida: PartidaMultijugador) -> dict:
        try:
            return json.loads(partida.datos_juego or '{}')
        except json.JSONDecodeError:
            return {
                'juego': 'poker',
                'fase': 'esperando',
                'cartas_comunitarias': [],
                'jugadores': {},
                'bote': 0.0,
                'ganador': None
            }

    def _guardar_estado(partida: PartidaMultijugador, estado: dict):
        estado['ultima_actualizacion'] = datetime.utcnow().isoformat()
        partida.datos_juego = json.dumps(estado)
        db.session.commit()

    def _es_miembro_de_sala(usuario_id: int, sala_id: int) -> bool:
        return UsuarioSala.query.filter_by(
            sala_id=sala_id,
            usuario_id=usuario_id
        ).first() is not None

    def _sanitizar_estado_para_usuario(estado: dict, user_id: int) -> dict:
        estado_copia = json.loads(json.dumps(estado))

        jugadores = estado_copia.get('jugadores', {})
        for uid, info in jugadores.items():
            if int(uid) != int(user_id):
                if estado_copia.get('fase') not in ('showdown', 'terminada'):
                    info.pop('cartas', None)
        return estado_copia

    def _resolver_si_todos_han_actuado(estado: dict):
        jugadores = estado.get('jugadores', {})
        activos = [j for j in jugadores.values() if j.get('estado') == 'activo']
        if not activos:
            return

        if not all(j.get('ha_actuado') for j in activos):
            return

        ganador = random.choice(activos)
        bote = estado.get('bote', 0.0) or 0.0

        ganador['stack'] = float(ganador.get('stack', 1000.0)) + float(bote)
        ganador['ultima_accion'] = 'ganador'

        for j in jugadores.values():
            j['cartas_visibles'] = j.get('cartas')

        estado['fase'] = 'terminada'
        estado['ganador'] = {
            'user_id': ganador['user_id'],
            'username': ganador['username'],
            'ganancia': bote
        }

    # ===========================
    #      EVENTOS SOCKET.IO
    # ===========================

    @socketio.on("poker_join")
    def handle_poker_join(data):
        if not current_user.is_authenticated:
            emit("poker_error", {"mensaje": "No autenticado"})
            return

        sala_id = data.get("sala_id")
        if sala_id is None:
            emit("poker_error", {"mensaje": "Falta sala_id"})
            return

        sala = SalaMultijugador.query.get(sala_id)
        if sala is None or sala.juego != 'poker':
            emit("poker_error", {"mensaje": "Sala de póker no encontrada"})
            return

        if not _es_miembro_de_sala(current_user.id, sala_id):
            emit("poker_error", {"mensaje": "No perteneces a esta sala"})
            return

        room = _nombre_room_poker(sala_id)
        join_room(room)

        partida = _obtener_o_crear_partida(sala)
        estado = _cargar_estado(partida)
        emit("poker_estado", _sanitizar_estado_para_usuario(estado, current_user.id))

    @socketio.on("poker_leave")
    def handle_poker_leave(data):
        if not current_user.is_authenticated:
            return

        sala_id = data.get("sala_id")
        if sala_id is None:
            return

        room = _nombre_room_poker(sala_id)
        leave_room(room)

    @socketio.on("poker_iniciar")
    def handle_poker_iniciar(data):
        if not current_user.is_authenticated:
            emit("poker_error", {"mensaje": "No autenticado"})
            return

        sala_id = data.get("sala_id")
        if sala_id is None:
            emit("poker_error", {"mensaje": "Falta sala_id"})
            return

        sala = SalaMultijugador.query.get(sala_id)
        if sala is None or sala.juego != 'poker':
            emit("poker_error", {"mensaje": "Sala de póker no encontrada"})
            return

        if sala.creador_id != current_user.id:
            emit("poker_error", {"mensaje": "Solo el creador de la sala puede iniciar la mano"})
            return

        if not _es_miembro_de_sala(current_user.id, sala_id):
            emit("poker_error", {"mensaje": "No perteneces a esta sala"})
            return

        # Crear nueva mano (similar a iniciar_mano() en routes.py)
        partida = _obtener_o_crear_partida(sala)

        mazo = _crear_mazo()
        random.shuffle(mazo)

        comunitarias = [mazo.pop() for _ in range(5)]

        jugadores_estado = {}
        jugadores_sala = UsuarioSala.query.filter_by(sala_id=sala.id).all()

        for us in jugadores_sala:
            cartas = [mazo.pop(), mazo.pop()]
            jugadores_estado[str(us.usuario_id)] = {
                'user_id': us.usuario_id,
                'username': (
                    us.player.username if hasattr(us, 'player') and us.player
                    else f'Usuario {us.usuario_id}'
                ),
                'stack': 1000.0,
                'apuesta_actual': 0.0,
                'estado': 'activo',
                'ultima_accion': '---',
                'ha_actuado': False,
                'cartas': cartas,
                'cartas_visibles': None
            }

        estado = {
            'juego': 'poker',
            'fase': 'apuestas',
            'cartas_comunitarias': comunitarias,
            'jugadores': jugadores_estado,
            'bote': 0.0,
            'ganador': None
        }

        _guardar_estado(partida, estado)

        room = _nombre_room_poker(sala_id)
        socketio.emit(
            "poker_estado",
            _sanitizar_estado_para_usuario(estado, current_user.id),
            room=room
        )

    @socketio.on("poker_accion")
    def handle_poker_accion(data):
        if not current_user.is_authenticated:
            emit("poker_error", {"mensaje": "No autenticado"})
            return

        sala_id = data.get("sala_id")
        accion = data.get("accion")
        cantidad = data.get("cantidad", 0)

        if sala_id is None:
            emit("poker_error", {"mensaje": "Falta sala_id"})
            return

        if accion not in ("apostar", "pasar", "retirarse"):
            emit("poker_error", {"mensaje": "Acción no válida"})
            return

        sala = SalaMultijugador.query.get(sala_id)
        if sala is None or sala.juego != 'poker':
            emit("poker_error", {"mensaje": "Sala de póker no encontrada"})
            return

        if not _es_miembro_de_sala(current_user.id, sala_id):
            emit("poker_error", {"mensaje": "No perteneces a esta sala"})
            return

        partida = _obtener_o_crear_partida(sala)
        estado = _cargar_estado(partida)

        if estado.get('fase') not in ('apuestas',):
            emit("poker_error", {"mensaje": "No se pueden realizar acciones en este momento"})
            return

        jugadores = estado.setdefault('jugadores', {})
        jugador = jugadores.get(str(current_user.id))
        if jugador is None:
            emit("poker_error", {"mensaje": "No estás registrado como jugador en esta mano"})
            return

        if jugador.get('estado') != 'activo':
            emit("poker_error", {"mensaje": "Ya no participas en esta mano"})
            return

        if accion == "apostar":
            try:
                cantidad = float(cantidad)
            except (ValueError, TypeError):
                emit("poker_error", {"mensaje": "Cantidad de apuesta no válida"})
                return

            if cantidad <= 0:
                emit("poker_error", {"mensaje": "La cantidad debe ser positiva"})
                return

            apuesta_minima = sala.apuesta_minima or 10.0
            if cantidad < apuesta_minima:
                emit("poker_error", {"mensaje": f"La apuesta mínima de la sala es {apuesta_minima}"})
                return

            jugador['apuesta_actual'] = float(jugador.get('apuesta_actual', 0.0)) + float(cantidad)
            estado['bote'] = float(estado.get('bote', 0.0)) + float(cantidad)
            jugador['ultima_accion'] = f'apuesta {cantidad:.2f}€'

        elif accion == "pasar":
            jugador['ultima_accion'] = 'pasa'

        elif accion == "retirarse":
            jugador['estado'] = 'retirado'
            jugador['ultima_accion'] = 'se retira'

        jugador['ha_actuado'] = True

        _resolver_si_todos_han_actuado(estado)
        _guardar_estado(partida, estado)

        room = _nombre_room_poker(sala_id)
        socketio.emit(
            "poker_estado",
            _sanitizar_estado_para_usuario(estado, current_user.id),
            room=room
        )
