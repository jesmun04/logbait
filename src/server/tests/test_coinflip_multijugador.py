import json
import math
import pytest
from unittest.mock import patch

from app import socketio
from models import (
    db,
    User,
    SalaMultijugador,
    UsuarioSala,
    Apuesta,
    Estadistica,
)

# Importar diccionario interno y handlers
from endpoints.protected.api.juegos.multiplayer.coinflip.socket_handlers import salas_coinflip


# -------------------------------------------------------------
# Helpers
# -------------------------------------------------------------

def _crear_usuario(app, username: str, balance: float = 200.0):
    with app.app_context():
        u = User(
            username=username,
            email=f"{username}@example.com",
            balance=balance
        )
        u.set_password("test123")
        db.session.add(u)
        db.session.commit()
        return u


def _crear_sala_coinflip(app, creador_id: int):
    with app.app_context():
        sala = SalaMultijugador(
            nombre="Sala Coinflip Test",
            juego="coinflip",
            capacidad=2,
            estado="jugando",
            creador_id=creador_id
        )
        db.session.add(sala)
        db.session.commit()
        return sala


def _registrar_usuario_sala(app, sala_id, user_id):
    with app.app_context():
        r = UsuarioSala(usuario_id=user_id, sala_id=sala_id, posicion=0)
        db.session.add(r)
        db.session.commit()
        return r


def _cliente_http(app, user):
    cli = app.test_client()
    with cli.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True
    return cli


def _cli_socket(app, user):
    http = _cliente_http(app, user)
    return socketio.test_client(app, flask_test_client=http)


# -------------------------------------------------------------
# Clean DB + clean salas_coinflip
# -------------------------------------------------------------

@pytest.fixture(autouse=True)
def limpiar(app):
    yield
    with app.app_context():
        for m in (Apuesta, Estadistica, UsuarioSala, SalaMultijugador, User):
            db.session.query(m).delete()
        db.session.commit()
    salas_coinflip.clear()


@pytest.fixture
def usuarios_sala(app):
    u1 = _crear_usuario(app, "coin_user1", balance=300)
    u2 = _crear_usuario(app, "coin_user2", balance=250)
    sala = _crear_sala_coinflip(app, u1.id)
    _registrar_usuario_sala(app, sala.id, u1.id)
    _registrar_usuario_sala(app, sala.id, u2.id)
    return sala, (u1, u2)


@pytest.fixture
def clientes_socket(app, usuarios_sala):
    sala, (u1, u2) = usuarios_sala
    c1 = _cli_socket(app, u1)
    c2 = _cli_socket(app, u2)
    # join
    c1.emit("join_coinflip_room", {"sala_id": sala.id})
    c2.emit("join_coinflip_room", {"sala_id": sala.id})
    yield sala, (c1, c2), (u1, u2)
    c1.disconnect()
    c2.disconnect()


# -------------------------------------------------------------
# PRUEBAS DE JOIN / LEAVE
# -------------------------------------------------------------

def test_join_coinflip_crea_sala_y_agrega_jugadores(clientes_socket):
    sala, (c1, c2), (u1, u2) = clientes_socket

    assert sala.id in salas_coinflip
    assert len(salas_coinflip[sala.id]["jugadores"]) == 2

    j_ids = {j["id"] for j in salas_coinflip[sala.id]["jugadores"]}
    assert u1.id in j_ids
    assert u2.id in j_ids


def test_leave_coinflip_remueve_jugador(clientes_socket):
    sala, (c1, c2), (u1, u2) = clientes_socket

    c1.emit("leave_coinflip_room", {"sala_id": sala.id})

    assert sala.id in salas_coinflip
    ids = {j["id"] for j in salas_coinflip[sala.id]["jugadores"]}
    assert u1.id not in ids
    assert u2.id in ids


# -------------------------------------------------------------
# PRUEBAS DE APUESTAS
# -------------------------------------------------------------

def test_coinflip_apostar_resta_balance_y_registra_apuesta(app, clientes_socket):
    sala, (c1, c2), (u1, u2) = clientes_socket

    cantidad = 50
    c1.emit("coinflip_apostar", {
        "sala_id": sala.id,
        "cantidad": cantidad,
        "eleccion": "cara"
    })

    with app.app_context():
        u1_db = User.query.get(u1.id)
        assert math.isclose(u1_db.balance, u1.balance - cantidad, rel_tol=1e-6)

    apuestas = salas_coinflip[sala.id]["apuestas"]
    assert len(apuestas) == 1
    assert apuestas[0]["usuario_id"] == u1.id
    assert apuestas[0]["eleccion"] == "cara"


def test_coinflip_apostar_fondos_insuficientes(clientes_socket, app):
    sala, (c1, c2), (u1, _) = clientes_socket

    # Dejar al jugador sin fondos
    with app.app_context():
        u1.balance = 10
        db.session.commit()

    c1.emit("coinflip_apostar", {
        "sala_id": sala.id,
        "cantidad": 9999,
        "eleccion": "cruz"
    })

    recibidos = c1.get_received()
    assert any(evt["name"] == "error_apuesta" for evt in recibidos)


def test_coinflip_apostar_actualiza_apuesta_existente(clientes_socket, app):
    sala, (c1, _), (u1, _) = clientes_socket

    c1.emit("coinflip_apostar", {"sala_id": sala.id, "cantidad": 40, "eleccion": "cara"})
    c1.emit("coinflip_apostar", {"sala_id": sala.id, "cantidad": 60, "eleccion": "cruz"})

    apuestas = salas_coinflip[sala.id]["apuestas"]
    assert len(apuestas) == 1
    assert apuestas[0]["cantidad"] == 60
    assert apuestas[0]["eleccion"] == "cruz"


# -------------------------------------------------------------
# PRUEBA LANZAMIENTO
# -------------------------------------------------------------

def test_coinflip_lanzar_rechaza_no_creador(clientes_socket):
    sala, (c1, c2), (u1, u2) = clientes_socket

    c2.emit("coinflip_lanzar", {"sala_id": sala.id})  # u2 no es creador
    recibidos = c2.get_received()
    assert any(evt["name"] == "error_lanzamiento" for evt in recibidos)


def test_coinflip_lanzar_error_si_no_hay_apuestas(clientes_socket):
    sala, (c1, _), (u1, _) = clientes_socket

    c1.emit("coinflip_lanzar", {"sala_id": sala.id})
    recibidos = c1.get_received()
    assert any(evt["name"] == "error_lanzamiento" for evt in recibidos)


@pytest.mark.usefixtures("clientes_socket")
def test_coinflip_lanzar_procesa_resultados_correctamente(app, usuarios_sala):
    sala, (u1, u2) = usuarios_sala

    c1 = _cli_socket(app, u1)
    c2 = _cli_socket(app, u2)
    c1.emit("join_coinflip_room", {"sala_id": sala.id})
    c2.emit("join_coinflip_room", {"sala_id": sala.id})

    # Apuestas
    c1.emit("coinflip_apostar", {"sala_id": sala.id, "cantidad": 50, "eleccion": "cara"})
    c2.emit("coinflip_apostar", {"sala_id": sala.id, "cantidad": 30, "eleccion": "cruz"})

    # Mock del resultado
    with patch("random.choice", return_value="cara"):
        with patch("time.sleep", return_value=None):  # Evita esperar 3s
            c1.emit("coinflip_lanzar", {"sala_id": sala.id})

    # Recibir eventos
    recibidos = c1.get_received() + c2.get_received()

    assert any(evt["name"] == "moneda_lanzada" for evt in recibidos)
    assert any(evt["name"] == "resultados_finales_coinflip" for evt in recibidos)

    # Validar BD
    with app.app_context():
        apuestas_db = Apuesta.query.all()
        assert len(apuestas_db) == 2

        # u1 gana 100, u2 pierde
        u1_db = User.query.get(u1.id)
        u2_db = User.query.get(u2.id)
        assert math.isclose(u1_db.balance, u1.balance - 50 + 100, rel_tol=1e-6)
        assert math.isclose(u2_db.balance, u2.balance - 30, rel_tol=1e-6)

        # Estadísticas registradas
        stats1 = Estadistica.query.filter_by(user_id=u1.id).first()
        stats2 = Estadistica.query.filter_by(user_id=u2.id).first()
        assert stats1.partidas_jugadas == 1
        assert stats1.partidas_ganadas == 1
        assert stats2.partidas_jugadas == 1


# -------------------------------------------------------------
# PRUEBAS DE ESTADO
# -------------------------------------------------------------

def test_estado_sala_actualizado_se_emite_en_join(clientes_socket):
    sala, (c1, c2), _ = clientes_socket
    recibidos = c1.get_received()
    assert any(evt["name"] == "estado_sala_actualizado" for evt in recibidos)
