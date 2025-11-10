import time, random
from collections import deque
from flask_login import current_user
from flask_socketio import join_room, leave_room, emit
from models import db, User, SalaMultijugador

# Estado en memoria por sala (igual patrón que coinflip)
salas_blackjack = {}
# Estructura:
# {
#   'jugadores': { uid: {'username','balance','mano':[],'apuesta':0,'estado': 'espera|jugando|bust|plantado'} },
#   'dealer': [],
#   'mazo': deque([...]),
#   'orden_turnos': [uid,...],
#   'turno_idx': int|None,
#   'fase': 'esperando_apuestas|turnos|crupier|fin',
#   'deadline_ts': float|None,
#   'votos_revancha': set(uid),
#   '_timer_activo': bool
# }

def nueva_baraja():
    palos = ['♠','♥','♦','♣']
    valores = [(str(n), n) for n in range(2,11)] + [('J',10),('Q',10),('K',10),('A',11)]
    mazo = [(v,p,pts) for (v,pts) in valores for p in palos]
    random.shuffle(mazo)
    return deque(mazo)

def valor_mano(mano):
    total = sum(c[2] for c in mano)
    ases = sum(1 for c in mano if c[0]=='A')
    while total > 21 and ases:
        total -= 10; ases -= 1
    return total

def turno_vivo(st, uid):
    j = st['jugadores'][uid]
    return j['estado'] == 'jugando' and valor_mano(j['mano']) <= 21

def avanzar_turno(st):
    # próximo jugador en 'jugando'; si no hay, pasa a crupier
    n = len(st['orden_turnos'])
    if n == 0:
        st['turno_idx'] = None
        st['fase'] = 'crupier'
        return
    start = 0 if st['turno_idx'] is None else (st['turno_idx'] + 1)
    for k in range(n):
        idx = (start + k) % n
        uid = st['orden_turnos'][idx]
        if turno_vivo(st, uid):
            st['turno_idx'] = idx
            st['deadline_ts'] = time.time() + 15  # 15 s por historia #129
            return
    st['turno_idx'] = None
    st['fase'] = 'crupier'

def emitir_estado(sala_id):
    st = salas_blackjack[sala_id]
    room = f"blackjack_sala_{sala_id}"
    emit("estado_blackjack", {
        "jugadores": {
            str(uid): {
                "username": j["username"],
                "balance": j["balance"],
                "apuesta": j["apuesta"],
                "mano": j["mano"],
                "estado": j["estado"],
                "total": valor_mano(j["mano"])
            } for uid, j in st["jugadores"].items()
        },
        "dealer": st["dealer"],
        "dealer_total": valor_mano(st["dealer"]) if st["fase"] in ("crupier","fin") else None,
        "orden_turnos": st["orden_turnos"],
        "turno_actual": (st["orden_turnos"][st["turno_idx"]] if st["turno_idx"] is not None else None),
        "fase": st["fase"],
        "deadline_ts": st["deadline_ts"],
        "votos_revancha": list(st["votos_revancha"]),
    }, room=room)

def start_timer_if_needed(socketio, sala_id, app):
    st = salas_blackjack[sala_id]
    if st.get("_timer_activo") or st["fase"] != "turnos":
        return
    st["_timer_activo"] = True
    def _loop():
        with app.app_context():
            while True:
                if sala_id not in salas_blackjack: break
                st = salas_blackjack[sala_id]
                if st["fase"] != "turnos" or st["turno_idx"] is None:
                    st["_timer_activo"] = False
                    break
                if st["deadline_ts"] and time.time() >= st["deadline_ts"]:
                    uid = st["orden_turnos"][st["turno_idx"]]
                    st["jugadores"][uid]["estado"] = "plantado"  # auto-plantar a los 15 s
                    avanzar_turno(st)
                    if st["fase"] == "crupier":
                        ejecutar_crupier_y_resolver(sala_id)
                emitir_estado(sala_id)
                socketio.sleep(0.5)
    socketio.start_background_task(_loop)

def ejecutar_crupier_y_resolver(sala_id):
    st = salas_blackjack[sala_id]
    st["fase"] = "crupier"
    # Roba hasta 17
    while valor_mano(st["dealer"]) < 17:
        st["dealer"].append(st["mazo"].popleft())
    dealer_val = valor_mano(st["dealer"])

    # Liquidación 1:1 (MVP)
    for uid, j in st["jugadores"].items():
        if j["apuesta"] <= 0: continue
        pj = valor_mano(j["mano"])
        pago = 0
        if pj > 21:
            pago = 0
        elif dealer_val > 21 or pj > dealer_val:
            pago = j["apuesta"] * 2
        elif pj == dealer_val:
            pago = j["apuesta"]
        user = User.query.get(uid)
        if user:
            user.balance += pago
            db.session.add(user)
        j["apuesta"] = 0
    db.session.commit()

    st["fase"] = "fin"
    st["turno_idx"] = None
    st["deadline_ts"] = None
    st["votos_revancha"] = set()

def reset_para_nueva_ronda(st):
    st["dealer"] = []
    if len(st["mazo"]) < 20:
        st["mazo"] = nueva_baraja()
    for j in st["jugadores"].values():
        j["mano"] = []
        j["estado"] = "espera"
        j["apuesta"] = 0
    st["fase"] = "esperando_apuestas"
    st["turno_idx"] = None
    st["deadline_ts"] = None
    st["votos_revancha"] = set()

def register_blackjack_handlers(socketio, app):
    @socketio.on("join_sala_blackjack")
    def join_sala(data):
        sala_id = int(data["sala_id"])
        sala = SalaMultijugador.query.get(sala_id)
        if not sala or sala.juego != "blackjack": return
        room = f"blackjack_sala_{sala_id}"
        join_room(room)

        st = salas_blackjack.setdefault(sala_id, {
            "jugadores": {},
            "dealer": [],
            "mazo": nueva_baraja(),
            "orden_turnos": [],
            "turno_idx": None,
            "fase": "esperando_apuestas",
            "deadline_ts": None,
            "votos_revancha": set(),
            "_timer_activo": False
        })
        # max 4 jugadores (#127)
        if current_user.id not in st["jugadores"]:
            if len(st["jugadores"]) >= 4:
                emit("error_blackjack", {"msg":"Sala llena (máximo 4)."})
                return
            st["jugadores"][current_user.id] = {
                "username": current_user.username,
                "balance": current_user.balance,
                "mano": [], "apuesta": 0, "estado": "espera"
            }
            st["orden_turnos"].append(current_user.id)
        emitir_estado(sala_id)

    @socketio.on("leave_sala_blackjack")
    def leave_sala(data):
        sala_id = int(data["sala_id"])
        leave_room(f"blackjack_sala_{sala_id}")
        st = salas_blackjack.get(sala_id)
        if not st: return
        uid = current_user.id
        if uid in st["jugadores"]:
            del st["jugadores"][uid]
        if uid in st["orden_turnos"]:
            st["orden_turnos"].remove(uid)
        if not st["jugadores"]:
            salas_blackjack.pop(sala_id, None)
        else:
            emitir_estado(sala_id)

    @socketio.on("apostar_blackjack")
    def apostar(data):
        sala_id = int(data["sala_id"])
        cantidad = float(data["cantidad"])
        st = salas_blackjack.get(sala_id)
        if not st or st["fase"] != "esperando_apuestas": return
        j = st["jugadores"].get(current_user.id)
        if not j or cantidad <= 0 or cantidad > j["balance"]: return
        j["apuesta"] = cantidad
        j["balance"] -= cantidad
        j["estado"] = "jugando"
        emitir_estado(sala_id)

    @socketio.on("iniciar_ronda_blackjack")
    def iniciar(data):
        sala_id = int(data["sala_id"])
        st = salas_blackjack.get(sala_id)
        if not st or st["fase"] != "esperando_apuestas": return
        # mínimo 2 jugadores con apuesta (#128, #127)
        if sum(1 for j in st["jugadores"].values() if j["apuesta"] > 0) < 2:
            emit("error_blackjack", {"msg": "Se necesitan al menos 2 jugadores con apuesta."},
                 to=f"blackjack_sala_{sala_id}")
            return
        st["dealer"] = [st["mazo"].popleft(), st["mazo"].popleft()]
        for j in st["jugadores"].values():
            if j["apuesta"] > 0:
                j["mano"] = [st["mazo"].popleft(), st["mazo"].popleft()]
                j["estado"] = "jugando"
            else:
                j["mano"] = []; j["estado"] = "espera"
        st["fase"] = "turnos"
        st["turno_idx"] = None
        avanzar_turno(st)
        emitir_estado(sala_id)
        start_timer_if_needed(socketio, sala_id, app)

    @socketio.on("hit_blackjack")
    def hit(data):
        sala_id = int(data["sala_id"])
        st = salas_blackjack.get(sala_id)
        if not st or st["fase"] != "turnos" or st["turno_idx"] is None: return
        uid_turno = st["orden_turnos"][st["turno_idx"]]
        if current_user.id != uid_turno: return
        st["jugadores"][uid_turno]["mano"].append(st["mazo"].popleft())
        if valor_mano(st["jugadores"][uid_turno]["mano"]) > 21:
            st["jugadores"][uid_turno]["estado"] = "bust"
            avanzar_turno(st)
            if st["fase"] == "crupier":
                ejecutar_crupier_y_resolver(sala_id)
        else:
            st["deadline_ts"] = time.time() + 15
        emitir_estado(sala_id)

    @socketio.on("stand_blackjack")
    def stand(data):
        sala_id = int(data["sala_id"])
        st = salas_blackjack.get(sala_id)
        if not st or st["fase"] != "turnos" or st["turno_idx"] is None: return
        uid_turno = st["orden_turnos"][st["turno_idx"]]
        if current_user.id != uid_turno: return
        st["jugadores"][uid_turno]["estado"] = "plantado"
        avanzar_turno(st)
        if st["fase"] == "crupier":
            ejecutar_crupier_y_resolver(sala_id)
        emitir_estado(sala_id)

    @socketio.on("voto_revancha")
    def voto_revancha(data):
        sala_id = int(data["sala_id"])
        st = salas_blackjack.get(sala_id)
        if not st or st["fase"] != "fin": return
        st["votos_revancha"].add(current_user.id)
        if len(st["votos_revancha"]) >= 2 and len(st["jugadores"]) >= 2:
            reset_para_nueva_ronda(st)
        emitir_estado(sala_id)

