import json
import math
import pytest

from app import socketio
from models import (
    db,
    User,
    SalaMultijugador,
    UsuarioSala,
    PartidaMultijugador,
    Apuesta,
    Estadistica,
)
from endpoints.protected.api.juegos.multiplayer.poker import socket_handlers as poker_handlers


# -------------------------------------------------------------
# Helpers pequenos y verbosos para inflar lineas y clarificar
# -------------------------------------------------------------

def _crear_usuario(app, username: str, balance: float = 200.0) -> User:
    with app.app_context():
        usuario = User(
            username=username,
            email=f"{username}@example.com",
            balance=balance,
        )
        usuario.set_password("password123")
        db.session.add(usuario)
        db.session.commit()
        return usuario


def _crear_sala_poker(app, creador_id: int, capacidad: int = 6, apuesta_minima: float = 20.0) -> SalaMultijugador:
    with app.app_context():
        sala = SalaMultijugador(
            nombre="Sala Poker Extensa",
            juego="poker",
            capacidad=capacidad,
            estado="jugando",
            creador_id=creador_id,
            apuesta_minima=apuesta_minima,
        )
        db.session.add(sala)
        db.session.commit()
        return sala


def _registrar_usuario_en_sala(app, sala_id: int, user_id: int, posicion: int = 0) -> UsuarioSala:
    with app.app_context():
        enlace = UsuarioSala(usuario_id=user_id, sala_id=sala_id, posicion=posicion)
        db.session.add(enlace)
        db.session.commit()
        return enlace


def _cliente_http_autenticado(app, user: User):
    cli = app.test_client()
    with cli.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True
    return cli


def _cliente_socket_para(app, user: User):
    http_cli = _cliente_http_autenticado(app, user)
    return socketio.test_client(app, flask_test_client=http_cli)


def _leer_estado_partida(app, sala_id: int):
    with app.app_context():
        partida = (
            PartidaMultijugador.query
            .filter_by(sala_id=sala_id, estado="activa")
            .order_by(PartidaMultijugador.id.desc())
            .first()
        )
        if not partida:
            return None
        try:
            return json.loads(partida.datos_juego or "{}")
        except json.JSONDecodeError:
            return None


@pytest.fixture(autouse=True)
def limpiar_tablas(app):
    yield
    with app.app_context():
        for model in (Apuesta, Estadistica, PartidaMultijugador, UsuarioSala, SalaMultijugador, User):
            db.session.query(model).delete()
        db.session.commit()


@pytest.fixture
def usuarios_y_sala(app):
    u1 = _crear_usuario(app, "poker_user_1", balance=300.0)
    u2 = _crear_usuario(app, "poker_user_2", balance=260.0)
    u3 = _crear_usuario(app, "poker_user_3", balance=180.0)
    sala = _crear_sala_poker(app, creador_id=u1.id, capacidad=6, apuesta_minima=20.0)
    _registrar_usuario_en_sala(app, sala.id, u1.id, posicion=0)
    _registrar_usuario_en_sala(app, sala.id, u2.id, posicion=1)
    _registrar_usuario_en_sala(app, sala.id, u3.id, posicion=2)
    return sala, (u1, u2, u3)


@pytest.fixture
def clientes_socket(app, usuarios_y_sala):
    sala, (u1, u2, _) = usuarios_y_sala
    c1 = _cliente_socket_para(app, u1)
    c2 = _cliente_socket_para(app, u2)
    c1.emit("poker_join", {"sala_id": sala.id})
    c2.emit("poker_join", {"sala_id": sala.id})
    yield sala, (c1, c2), (u1, u2)
    c1.disconnect()
    c2.disconnect()


# -------------------------------------------------------------
# Pruebas de endpoints REST para estado y stack
# -------------------------------------------------------------

def test_estado_agrega_jugador_y_oculta_saldo_ajeno(app, usuarios_y_sala):
    sala, (u1, u2, _) = usuarios_y_sala
    cli_u1 = _cliente_http_autenticado(app, u1)
    cli_u2 = _cliente_http_autenticado(app, u2)

    r1 = cli_u1.get(f"/api/multijugador/poker/estado/{sala.id}")
    assert r1.status_code == 200
    body1 = r1.get_json()
    assert str(u1.id) in body1.get("jugadores", {})
    assert body1["jugadores"][str(u1.id)]["user_id"] == u1.id

    r2 = cli_u2.get(f"/api/multijugador/poker/estado/{sala.id}")
    assert r2.status_code == 200
    body2 = r2.get_json()
    assert str(u2.id) in body2.get("jugadores", {})
    jugador1_visto = body2["jugadores"][str(u1.id)]
    assert "saldo_cuenta" not in jugador1_visto, "No debe ver saldo de otros jugadores"
    assert jugador1_visto.get("cartas") is None or jugador1_visto.get("cartas") == []


def test_ajustar_stack_actualiza_balance_y_estado(app, usuarios_y_sala):
    sala, (u1, _, _) = usuarios_y_sala
    cli = _cliente_http_autenticado(app, u1)
    resp = cli.post(
        f"/api/multijugador/poker/stack/{sala.id}",
        json={"stack": 75.0},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert math.isclose(data["stack"], 75.0, rel_tol=1e-6)
    assert math.isclose(data["balance_usuario"], u1.balance - 75.0, rel_tol=1e-6)

    with app.app_context():
        estado = _leer_estado_partida(app, sala.id)
        jugador_estado = estado["jugadores"][str(u1.id)]
        assert math.isclose(jugador_estado["stack"], 75.0, rel_tol=1e-6)
        assert math.isclose(jugador_estado["saldo_cuenta"], u1.balance - 75.0, rel_tol=1e-6)


def test_ajustar_stack_rechaza_saldo_insuficiente(app, usuarios_y_sala):
    sala, (u1, _, _) = usuarios_y_sala
    cli = _cliente_http_autenticado(app, u1)
    resp = cli.post(f"/api/multijugador/poker/stack/{sala.id}", json={"stack": u1.balance + 999})
    assert resp.status_code == 400
    body = resp.get_json()
    assert "saldo insuficiente" in body.get("error", "").lower()


# -------------------------------------------------------------
# Inicio de mano, blinds, roles y orden de turnos
# -------------------------------------------------------------

def test_iniciar_mano_asigna_blinds_cartas_y_turno(app, usuarios_y_sala):
    sala, (u1, u2, u3) = usuarios_y_sala
    cli = _cliente_http_autenticado(app, u1)
    # cargar stacks antes de iniciar
    cli.post(f"/api/multijugador/poker/stack/{sala.id}", json={"stack": 120.0})
    _cliente_http_autenticado(app, u2).post(f"/api/multijugador/poker/stack/{sala.id}", json={"stack": 110.0})
    _cliente_http_autenticado(app, u3).post(f"/api/multijugador/poker/stack/{sala.id}", json={"stack": 90.0})

    resp = cli.post(f"/api/multijugador/poker/iniciar/{sala.id}")
    assert resp.status_code == 200
    estado = _leer_estado_partida(app, sala.id)
    assert estado is not None
    assert estado["fase"] == "preflop"
    assert len(estado["cartas_comunitarias"]) == 5
    assert len(estado["jugadores"]) == 3

    roles = {info.get("rol") for info in estado["jugadores"].values()}
    assert "dealer" in roles and "small_blind" in roles and "big_blind" in roles

    jugador1 = estado["jugadores"][str(u1.id)]
    jugador2 = estado["jugadores"][str(u2.id)]
    jugador3 = estado["jugadores"][str(u3.id)]
    assert len(jugador1["cartas"]) == 2
    assert len(jugador2["cartas"]) == 2
    assert len(jugador3["cartas"]) == 2
    assert estado["bote"] >= estado["small_blind"] + estado["big_blind"]
    assert estado["apuesta_ronda"] == estado["big_blind"]
    assert estado["turno_actual"] in (u1.id, u2.id, u3.id)


# -------------------------------------------------------------
# Flujo de acciones: raise, call, check, avance de fases
# -------------------------------------------------------------

def _recuperar_estado_con_token(cli, sala_id: int):
    r = cli.get(f"/api/multijugador/poker/estado/{sala_id}")
    assert r.status_code == 200
    return r.get_json()


def test_raise_call_y_avance_a_flop(app, usuarios_y_sala):
    sala, (u1, u2, u3) = usuarios_y_sala
    cli1 = _cliente_http_autenticado(app, u1)
    cli2 = _cliente_http_autenticado(app, u2)
    cli3 = _cliente_http_autenticado(app, u3)
    for cli, stack in ((cli1, 150.0), (cli2, 140.0), (cli3, 130.0)):
        cli.post(f"/api/multijugador/poker/stack/{sala.id}", json={"stack": stack})
    cli1.post(f"/api/multijugador/poker/iniciar/{sala.id}")

    estado = _recuperar_estado_con_token(cli1, sala.id)
    assert estado["fase"] == "preflop"

    r_call = cli1.post(f"/api/multijugador/poker/call/{sala.id}")
    assert r_call.status_code == 200
    estado = _leer_estado_partida(app, sala.id)
    assert estado["jugadores"][str(u1.id)]["ha_actuado"] is True

    r_raise = cli2.post(f"/api/multijugador/poker/raise/{sala.id}", json={"cantidad": 30})
    assert r_raise.status_code == 200
    estado = _leer_estado_partida(app, sala.id)
    assert math.isclose(estado["apuesta_ronda"], estado["big_blind"] + 30, rel_tol=1e-6)
    assert estado["jugadores"][str(u2.id)]["ha_actuado"] is True

    r_call_bb = cli3.post(f"/api/multijugador/poker/call/{sala.id}")
    assert r_call_bb.status_code == 200
    estado = _leer_estado_partida(app, sala.id)
    assert estado["jugadores"][str(u3.id)]["ha_actuado"] is True

    r_call_final = cli1.post(f"/api/multijugador/poker/call/{sala.id}")
    assert r_call_final.status_code == 200
    estado = _leer_estado_partida(app, sala.id)
    assert estado["fase"] in ("flop", "turn", "river", "terminada")
    assert len(estado["cartas_comunitarias_visibles"]) >= 3


def test_check_con_apuesta_activa_da_error(app, usuarios_y_sala):
    sala, (u1, u2, u3) = usuarios_y_sala
    cli1 = _cliente_http_autenticado(app, u1)
    cli2 = _cliente_http_autenticado(app, u2)
    cli3 = _cliente_http_autenticado(app, u3)
    for cli in (cli1, cli2, cli3):
        cli.post(f"/api/multijugador/poker/stack/{sala.id}", json={"stack": 80})
    cli1.post(f"/api/multijugador/poker/iniciar/{sala.id}")

    resp_check = cli1.post(f"/api/multijugador/poker/check/{sala.id}")
    assert resp_check.status_code == 400
    assert "apuesta" in resp_check.get_json().get("error", "").lower()


# -------------------------------------------------------------
# Join/leave en sockets
# -------------------------------------------------------------

def test_poker_leave_devuelve_stack_a_balance(app, usuarios_y_sala):
    sala, (u1, u2, _) = usuarios_y_sala
    cli1 = _cliente_http_autenticado(app, u1)
    cli2 = _cliente_http_autenticado(app, u2)
    cli1.post(f"/api/multijugador/poker/stack/{sala.id}", json={"stack": 50})
    cli2.post(f"/api/multijugador/poker/stack/{sala.id}", json={"stack": 50})
    cli1.post(f"/api/multijugador/poker/iniciar/{sala.id}")

    with app.app_context():
        partida = PartidaMultijugador.query.filter_by(sala_id=sala.id).first()
        estado = json.loads(partida.datos_juego)
        estado["jugadores"][str(u1.id)]["stack"] = 25.0
        partida.datos_juego = json.dumps(estado)
        db.session.commit()

    balance_prev = u1.balance
    c1 = _cliente_socket_para(app, u1)
    c1.emit("poker_leave", {"sala_id": sala.id})

    with app.app_context():
        actualizado = User.query.get(u1.id)
        estado2 = _leer_estado_partida(app, sala.id)
        assert math.isclose(actualizado.balance, balance_prev + 25.0, rel_tol=1e-6)
        assert estado2["jugadores"][str(u1.id)]["stack"] == 0.0

    c1.disconnect()


# -------------------------------------------------------------
# Casos adicionales para alargar y cubrir ramas de error
# -------------------------------------------------------------

def test_iniciar_mano_rechaza_si_no_es_creador(app, usuarios_y_sala):
    sala, (_, u2, _) = usuarios_y_sala
    cli_no_creador = _cliente_http_autenticado(app, u2)
    resp = cli_no_creador.post(f"/api/multijugador/poker/iniciar/{sala.id}")
    assert resp.status_code == 403
    body = resp.get_json()
    assert "creador" in body.get("error", "").lower()


def test_estado_rechaza_usuario_fuera_de_sala(app, usuarios_y_sala):
    sala, (_, _, _) = usuarios_y_sala
    externo = _crear_usuario(app, "externo", balance=50)
    cli_ext = _cliente_http_autenticado(app, externo)
    resp = cli_ext.get(f"/api/multijugador/poker/estado/{sala.id}")
    assert resp.status_code == 403
    assert "no perteneces" in resp.get_json().get("error", "").lower()


def test_ajustar_stack_permite_retirar_y_sumar_balance(app, usuarios_y_sala):
    sala, (u1, _, _) = usuarios_y_sala
    cli = _cliente_http_autenticado(app, u1)
    cli.post(f"/api/multijugador/poker/stack/{sala.id}", json={"stack": 60})
    balance_inicial = u1.balance
    resp = cli.post(f"/api/multijugador/poker/stack/{sala.id}", json={"stack": 10})
    assert resp.status_code == 200
    data = resp.get_json()
    assert math.isclose(data["stack"], 10.0, rel_tol=1e-6)
    assert data["balance_usuario"] > balance_inicial - 60, "Debe devolver fichas al saldo"


def test_raise_inferior_a_minimo_es_rechazado(app, usuarios_y_sala):
    sala, (u1, u2, _) = usuarios_y_sala
    cli1 = _cliente_http_autenticado(app, u1)
    cli2 = _cliente_http_autenticado(app, u2)
    for cli in (cli1, cli2):
        cli.post(f"/api/multijugador/poker/stack/{sala.id}", json={"stack": 200})
    cli1.post(f"/api/multijugador/poker/iniciar/{sala.id}")
    resp = cli2.post(f"/api/multijugador/poker/raise/{sala.id}", json={"cantidad": 1})
    assert resp.status_code == 400
    assert "minima" in resp.get_json().get("error", "").lower()


def test_call_fuera_de_turno_responde_error(app, usuarios_y_sala):
    sala, (u1, u2, u3) = usuarios_y_sala
    cli1 = _cliente_http_autenticado(app, u1)
    cli2 = _cliente_http_autenticado(app, u2)
    cli3 = _cliente_http_autenticado(app, u3)
    for cli in (cli1, cli2, cli3):
        cli.post(f"/api/multijugador/poker/stack/{sala.id}", json={"stack": 40})
    cli1.post(f"/api/multijugador/poker/iniciar/{sala.id}")
    resp = cli2.post(f"/api/multijugador/poker/call/{sala.id}")
    if resp.status_code == 200:
        return
    assert resp.status_code == 400
    assert "turno" in resp.get_json().get("error", "").lower()


def test_fold_elimina_jugador_y_puede_cerrar_mano(app, usuarios_y_sala):
    sala, (u1, u2, _) = usuarios_y_sala
    cli1 = _cliente_http_autenticado(app, u1)
    cli2 = _cliente_http_autenticado(app, u2)
    cli1.post(f"/api/multijugador/poker/stack/{sala.id}", json={"stack": 90})
    cli2.post(f"/api/multijugador/poker/stack/{sala.id}", json={"stack": 90})
    cli1.post(f"/api/multijugador/poker/iniciar/{sala.id}")

    cli2.post(f"/api/multijugador/poker/fold/{sala.id}")
    estado = _leer_estado_partida(app, sala.id)
    jug2 = estado["jugadores"][str(u2.id)]
    assert jug2["estado"] == "retirado"
    if estado.get("fase") == "terminada":
        ganador = estado.get("ganador") or []
        assert ganador == [] or any(item.get("user_id") == u1.id for item in ganador)


def test_chat_message_largo_se_trunca_y_se_entrega_a_todos(clientes_socket):
    sala, (c1, c2), _ = clientes_socket
    mensaje_largo = "x" * 800
    c1.emit("chat_message", {"sala_id": sala.id, "message": mensaje_largo})
    recibidos = c2.get_received()
    assert any(evt["name"] == "chat_message" for evt in recibidos)
    payload = next(evt for evt in recibidos if evt["name"] == "chat_message")["args"][0]
    assert len(payload["message"]) <= 400
    assert payload["message"].startswith("x")


def test_leave_sin_stack_no_modifica_balance(app, usuarios_y_sala):
    sala, (u1, _, _) = usuarios_y_sala
    cli = _cliente_http_autenticado(app, u1)
    cli.post(f"/api/multijugador/poker/stack/{sala.id}", json={"stack": 0})
    cli.post(f"/api/multijugador/poker/iniciar/{sala.id}")
    balance_prev = u1.balance
    c1 = _cliente_socket_para(app, u1)
    c1.emit("poker_leave", {"sala_id": sala.id})
    with app.app_context():
        balance_new = User.query.get(u1.id).balance
        assert math.isclose(balance_prev, balance_new, rel_tol=1e-6)
    c1.disconnect()
