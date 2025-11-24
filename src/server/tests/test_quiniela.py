import json
import pytest

from endpoints.protected.api.juegos.singleplayer.quiniela import routes as quiniela_routes
from models import Apuesta, Estadistica


def login(client):
    """Helper to authenticate the test user through the login form."""
    return client.post(
        "/login",
        data={"username": "test_user", "password": "password123"},
        follow_redirects=True,
    )


def test_ligas_devuelve_lista_completa(client, test_user):
    """Ensure the ligas endpoint lists all configured leagues with metadata."""
    with client:
        login(client)
        response = client.get("/api/quiniela/ligas")

    assert response.status_code == 200
    data = json.loads(response.data)
    ligas = data.get("ligas")

    assert isinstance(ligas, list)
    assert len(ligas) == len(quiniela_routes.LIGAS_EQUIPOS)
    ids = {liga["id"] for liga in ligas}
    assert ids == set(quiniela_routes.LIGAS_EQUIPOS.keys())
    assert all("nombre" in liga and "equipos_count" in liga for liga in ligas)
    assert all(liga["equipos_count"] > 0 for liga in ligas)


def test_generar_partidos_respeta_cantidad_y_equipo_distinto(client, test_user, monkeypatch):
    """Generated matches should honor the requested count and never pair a team with itself."""
    # Keep team order stable so the assertions are deterministic
    monkeypatch.setattr(quiniela_routes.random, "shuffle", lambda seq: None)

    with client:
        login(client)
        response = client.post(
            "/api/quiniela/generar-partidos", json={"liga": "bundesliga", "partidos": 8}
        )

    assert response.status_code == 200
    data = json.loads(response.data)
    partidos = data["partidos"]

    assert len(partidos) == 8
    assert data["total_partidos"] == 8
    assert all("local" in p and "visitante" in p for p in partidos)
    assert all(p["local"] != p["visitante"] for p in partidos)
    assert data["liga"] == quiniela_routes.LIGAS_EQUIPOS["bundesliga"]["nombre"]


def test_generar_partidos_liga_invalida(client, test_user):
    """Requesting matches for an unknown league should return a 400."""
    with client:
        login(client)
        response = client.post(
            "/api/quiniela/generar-partidos", json={"liga": "liga_inexistente", "partidos": 3}
        )

    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data


def test_generar_partidos_anade_partidos_extra_si_faltan_equipos(client, test_user, monkeypatch):
    """When the requested match count exceeds the natural pairing count, filler matches are generated."""
    # Avoid shuffling for reproducibility
    monkeypatch.setattr(quiniela_routes.random, "shuffle", lambda seq: None)
    # Force random.choice to cycle deterministically to avoid flaky pairings
    teams = quiniela_routes.LIGAS_EQUIPOS["serie_a"]["equipos"]
    iterator = iter(teams * 2)
    monkeypatch.setattr(quiniela_routes.random, "choice", lambda seq: next(iterator))

    requested = 15
    with client:
        login(client)
        response = client.post(
            "/api/quiniela/generar-partidos", json={"liga": "serie_a", "partidos": requested}
        )

    assert response.status_code == 200
    data = json.loads(response.data)
    partidos = data["partidos"]

    assert len(partidos) == requested
    assert all(p["local"] != p["visitante"] for p in partidos)
    assert data["total_partidos"] == requested
    # Also check that at least one filler match used the deterministic choice path
    assert any(p["local"] == teams[0] or p["visitante"] == teams[0] for p in partidos)


def test_generar_partidos_por_defecto_usa_laliga(client, test_user, monkeypatch):
    """If no league or count provided, defaults should generate 15 matches for espana."""
    monkeypatch.setattr(quiniela_routes.random, "shuffle", lambda seq: None)
    with client:
        login(client)
        response = client.post("/api/quiniela/generar-partidos", json={})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["liga"] == quiniela_routes.LIGAS_EQUIPOS["espana"]["nombre"]
    assert len(data["partidos"]) == 15
    assert data["total_partidos"] == 15


def test_apostar_actualiza_balance_y_estadisticas(client, app, test_user, monkeypatch):
    """Successful quiniela bet should adjust balance, persist bet, and update stats."""
    pronosticos = ["1", "1", "1", "1"]
    partidos = [{"local": f"L{i}", "visitante": f"V{i}"} for i in range(len(pronosticos))]

    # Force deterministic outcomes and payout
    monkeypatch.setattr(quiniela_routes, "generar_resultados_reales", lambda n: pronosticos)
    monkeypatch.setattr(quiniela_routes, "calcular_ganancia", lambda a, t, c: 250.0)

    with client:
        login(client)
        response = client.post(
            "/api/quiniela/apostar",
            json={"cantidad": 100.0, "pronosticos": pronosticos, "partidos": partidos},
        )

    assert response.status_code == 200
    data = json.loads(response.data)

    assert data["aciertos"] == len(pronosticos)
    assert data["total_partidos"] == len(pronosticos)
    assert data["ganancia"] == 250.0
    assert data["nuevo_balance"] == pytest.approx(1150.0)
    assert data["mensaje"].startswith("Quiniela:")

    with app.app_context():
        apuestas = Apuesta.query.filter_by(user_id=test_user.id, juego="quiniela").all()
        assert len(apuestas) == 1
        assert apuestas[0].cantidad == 100.0
        assert "aciertos" in apuestas[0].resultado

        stats = Estadistica.query.filter_by(user_id=test_user.id, juego="quiniela").first()
        assert stats is not None
        assert stats.partidas_jugadas == 1
        assert stats.partidas_ganadas == 1
        assert stats.apuesta_total == pytest.approx(100.0)
        assert stats.ganancia_total == pytest.approx(250.0)


def test_apostar_perdida_actualiza_estadisticas_sin_ganada(client, app, test_user, monkeypatch):
    """Losing a quiniela should reduce balance, record the bet, and not count as win."""
    pronosticos = ["1", "1", "1"]
    resultados = ["2", "2", "2"]
    partidos = [{"local": f"L{i}", "visitante": f"V{i}"} for i in range(len(pronosticos))]

    monkeypatch.setattr(quiniela_routes, "generar_resultados_reales", lambda n: resultados)
    monkeypatch.setattr(quiniela_routes, "calcular_ganancia", lambda a, t, c: 0.0)

    with client:
        login(client)
        response = client.post(
            "/api/quiniela/apostar",
            json={"cantidad": 50.0, "pronosticos": pronosticos, "partidos": partidos},
        )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["aciertos"] == 0
    assert data["ganancia"] == 0.0
    assert data["nuevo_balance"] == pytest.approx(950.0)

    with app.app_context():
        stats = Estadistica.query.filter_by(user_id=test_user.id, juego="quiniela").first()
        assert stats.partidas_jugadas >= 1
        assert stats.partidas_ganadas <= stats.partidas_jugadas
        assert stats.apuesta_total >= 50.0
        assert stats.ganancia_total >= 0.0


def test_apostar_rechaza_sin_fondos(client, test_user):
    """Betting more than the available balance should fail gracefully."""
    with client:
        login(client)
        response = client.post(
            "/api/quiniela/apostar",
            json={
                "cantidad": test_user.balance + 500,
                "pronosticos": ["1", "X"],
                "partidos": [{"local": "A", "visitante": "B"}, {"local": "C", "visitante": "D"}],
            },
        )

    assert response.status_code == 400
    data = json.loads(response.data)
    assert "Fondos insuficientes" in data.get("error", "")


def test_apostar_con_datos_incompletos(client, test_user):
    """Missing JSON payload should trigger a 400 with an error message."""
    with client:
        login(client)
        response = client.post("/api/quiniela/apostar")

    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data


def test_generar_resultados_reales_cubre_los_tres_resultados(monkeypatch):
    """Force deterministic random values to validate each result bucket."""
    values = iter([0.1, 0.6, 0.9, 0.2, 0.79, 0.81])
    monkeypatch.setattr(quiniela_routes.random, "random", lambda: next(values))

    resultados = quiniela_routes.generar_resultados_reales(6)
    assert resultados == ["1", "X", "2", "1", "X", "2"]
    assert len(resultados) == 6
    assert resultados.count("1") == 2
    assert resultados.count("X") == 2
    assert resultados.count("2") == 2


@pytest.mark.parametrize(
    "aciertos,total,apuesta,esperada",
    [
        (5, 5, 10, 500),   # Pleno
        (4, 5, 10, 200),   # 1 fallo
        (3, 5, 10, 100),   # 2 fallos
        (2, 5, 10, 50),    # 3 fallos
        (1, 5, 10, 30),    # 4 fallos
        (0, 5, 10, 20),    # 5 fallos (segun escala actual)
        (6, 7, 5, 250),    # Pleno en 7
        (5, 10, 8, 0),     # Mas de 5 fallos no paga
        (7, 7, 20, 1000),  # Pleno extendido
        (6, 7, 20, 400),   # 1 fallo
        (5, 7, 20, 200),   # 2 fallos
        (4, 7, 20, 100),   # 3 fallos
        (3, 7, 20, 60),    # 4 fallos
        (2, 7, 20, 40),    # 5 fallos
        (1, 7, 20, 0),     # 6 fallos
    ],
)
def test_calcular_ganancia_por_tramos(aciertos, total, apuesta, esperada):
    """Validate each payout tier of calcular_ganancia."""
    assert quiniela_routes.calcular_ganancia(aciertos, total, apuesta) == esperada


def test_calcular_aciertos_compara_pronosticos_y_resultados():
    """Ensure calcular_aciertos counts only matching predictions."""
    pronosticos = ["1", "X", "2", "1", "X"]
    resultados = ["1", "1", "2", "2", "X"]
    assert quiniela_routes.calcular_aciertos(pronosticos, resultados) == 3
    assert quiniela_routes.calcular_aciertos([], []) == 0


def test_calcular_aciertos_ignora_resultados_extra():
    """Extra resultados beyond pronosticos should be ignored by zip length."""
    pronosticos = ["1", "X"]
    resultados = ["1", "X", "2", "1"]
    assert quiniela_routes.calcular_aciertos(pronosticos, resultados) == 2


def test_apostar_acumula_varias_apuestas(client, app, test_user, monkeypatch):
    """Two sequential bets should accumulate stats and balance correctly."""
    pronosticos = ["1", "X", "2"]
    partidos = [{"local": f"L{i}", "visitante": f"V{i}"} for i in range(len(pronosticos))]

    resultados_win = ["1", "X", "2"]
    resultados_loss = ["2", "2", "2"]

    with client:
        login(client)

        monkeypatch.setattr(quiniela_routes, "generar_resultados_reales", lambda n: resultados_win)
        monkeypatch.setattr(quiniela_routes, "calcular_ganancia", lambda a, t, c: 150.0)
        res1 = client.post(
            "/api/quiniela/apostar",
            json={"cantidad": 60.0, "pronosticos": pronosticos, "partidos": partidos},
        )
        assert res1.status_code == 200
        data1 = json.loads(res1.data)
        assert data1["ganancia"] == 150.0
        assert data1["nuevo_balance"] == pytest.approx(1090.0)

        monkeypatch.setattr(quiniela_routes, "generar_resultados_reales", lambda n: resultados_loss)
        monkeypatch.setattr(quiniela_routes, "calcular_ganancia", lambda a, t, c: 0.0)
        res2 = client.post(
            "/api/quiniela/apostar",
            json={"cantidad": 40.0, "pronosticos": pronosticos, "partidos": partidos},
        )
        assert res2.status_code == 200
        data2 = json.loads(res2.data)
        assert data2["ganancia"] == 0.0
        assert data2["nuevo_balance"] == pytest.approx(1050.0)

    with app.app_context():
        stats = Estadistica.query.filter_by(user_id=test_user.id, juego="quiniela").first()
        assert stats.partidas_jugadas >= 2
        assert stats.apuesta_total >= 100.0
        assert stats.ganancia_total >= 150.0
