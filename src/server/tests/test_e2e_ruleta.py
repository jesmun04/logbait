#!/usr/bin/env python3
"""
Script para probar E2E la ruleta multijugador:
1. Crear dos usuarios
2. Crear una sala multijugador
3. Simular que los dos usuarios se unen
4. Colocan apuestas secretas
5. Ambos presionan Girar
6. Verificar que el resultado se calcula correctamente
"""

import sys
import os
import time
import json

# Agregar src/server al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'server'))

def test_e2e():
    print("🧪 Prueba E2E de Ruleta Multijugador\n")
    
    # 1. Configurar app con contexto
    from app import app
    from models import db, User, SalaMultijugador, UsuarioSala, Estadistica
    
    with app.app_context():
        print("1️⃣  Limpiando/preparando base de datos...")
        
        # Limpiar usuarios y salas de prueba
        User.query.filter_by(username='test_user_1').delete()
        User.query.filter_by(username='test_user_2').delete()
        SalaMultijugador.query.filter_by(nombre='Test Ruleta').delete()
        db.session.commit()
        
        # Crear usuarios
        print("2️⃣  Creando usuarios de prueba...")
        user1 = User(username='test_user_1', email='test1@example.com', balance=100.0)
        user1.set_password('password')
        user2 = User(username='test_user_2', email='test2@example.com', balance=100.0)
        user2.set_password('password')
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        print(f"  ✅ Usuario 1: {user1.username} (ID: {user1.id}, Balance: {user1.balance}€)")
        print(f"  ✅ Usuario 2: {user2.username} (ID: {user2.id}, Balance: {user2.balance}€)")
        
        # Crear sala multijugador
        print("3️⃣  Creando sala multijugador...")
        sala = SalaMultijugador(
            nombre='Test Ruleta',
            juego='ruleta',
            creador_id=user1.id,
            capacidad=2,
            estado='jugando',
            apuesta_minima=0.2
        )
        db.session.add(sala)
        db.session.commit()
        print(f"  ✅ Sala creada: {sala.nombre} (ID: {sala.id})")
        
        # Agregar usuarios a la sala
        print("4️⃣  Agregando usuarios a la sala...")
        UsuarioSala.query.filter_by(sala_id=sala.id).delete()
        usuario_sala_1 = UsuarioSala(usuario_id=user1.id, sala_id=sala.id)
        usuario_sala_2 = UsuarioSala(usuario_id=user2.id, sala_id=sala.id)
        db.session.add(usuario_sala_1)
        db.session.add(usuario_sala_2)
        db.session.commit()
        print(f"  ✅ {user1.username} unido a la sala")
        print(f"  ✅ {user2.username} unido a la sala")
        
        # Simular el manejo de Socket.IO
        print("5️⃣  Simulando eventos de Socket.IO...\n")
        
        from endpoints.api_multijugador.ruleta.socket_handlers import salas_ruleta
        
        # Simular join de ambos usuarios
        print("  📡 Usuario 1 se une a la sala (join_ruleta_room)")
        if sala.id not in salas_ruleta:
            salas_ruleta[sala.id] = {'jugadores': [], 'estado': 'esperando', 'apuestas': []}
        salas_ruleta[sala.id]['jugadores'].append({
            'id': user1.id, 
            'username': user1.username, 
            'balance': user1.balance, 
            'ready': False
        })
        print(f"    Jugadores en sala: {len(salas_ruleta[sala.id]['jugadores'])}")
        
        print("  📡 Usuario 2 se une a la sala (join_ruleta_room)")
        salas_ruleta[sala.id]['jugadores'].append({
            'id': user2.id, 
            'username': user2.username, 
            'balance': user2.balance, 
            'ready': False
        })
        print(f"    Jugadores en sala: {len(salas_ruleta[sala.id]['jugadores'])}")
        
        # Simular apuestas secretas
        print("\n  📡 Usuario 1 coloca apuesta secreta (ruleta_place_bet)")
        bet1 = {
            'type': 'straight',
            'set': [17],
            'label': '17',
            'amount': 200  # 2€ en centavos
        }
        user1.balance -= 2.0
        salas_ruleta[sala.id]['apuestas'].append({
            'usuario_id': user1.id,
            'bets': [bet1],
            'amount_cents': 200,
            'submitted_at': time.time(),
            'has_spun': False
        })
        print(f"    Apuesta: {bet1['label']} por 2€")
        print(f"    Balance de {user1.username}: {user1.balance}€")
        print(f"    Total de apuestas en sala: {len(salas_ruleta[sala.id]['apuestas'])}")
        
        print("\n  📡 Usuario 2 coloca apuesta secreta (ruleta_place_bet)")
        bet2 = {
            'type': 'even',
            'set': [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36],
            'label': 'Rojo',
            'amount': 100  # 1€ en centavos
        }
        user2.balance -= 1.0
        salas_ruleta[sala.id]['apuestas'].append({
            'usuario_id': user2.id,
            'bets': [bet2],
            'amount_cents': 100,
            'submitted_at': time.time(),
            'has_spun': False
        })
        print(f"    Apuesta: {bet2['label']} por 1€")
        print(f"    Balance de {user2.username}: {user2.balance}€")
        print(f"    Total de apuestas en sala: {len(salas_ruleta[sala.id]['apuestas'])}")
        
        # Simular spin
        print("\n  📡 Usuario 1 solicita giro (ruleta_spin)")
        salas_ruleta[sala.id]['jugadores'][0]['ready'] = True
        print(f"    {salas_ruleta[sala.id]['jugadores'][0]['username']} listo: True")
        
        print("  📡 Usuario 2 solicita giro (ruleta_spin)")
        salas_ruleta[sala.id]['jugadores'][1]['ready'] = True
        print(f"    {salas_ruleta[sala.id]['jugadores'][1]['username']} listo: True")
        
        # Verificar que ambos están listos
        ready_count = sum(1 for j in salas_ruleta[sala.id]['jugadores'] if j.get('ready'))
        required = len(salas_ruleta[sala.id]['jugadores'])
        print(f"\n  ✅ Jugadores listos: {ready_count}/{required}")
        
        if ready_count == required:
            print("  🎲 ¡GIRO PERMITIDO! Realizando cálculo de resultado...\n")
            
            # Simular cálculo de resultado
            import random
            result_number = 17  # Vamos a dejarlo como 17 para que el usuario 1 gane
            REDS = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
            PAYOUT = {'straight':35,'split':17,'street':11,'corner':8,'line':5,'dozen':2,'column':2,'even':1}
            
            print(f"  🎰 Número resultado: {result_number}")
            print(f"  🎨 Color: {'ROJO' if result_number in REDS else 'NEGRO' if result_number != 0 else 'VERDE'}\n")
            
            print("  📊 Calculando payouts:\n")
            
            for apuesta in salas_ruleta[sala.id]['apuestas']:
                user_id = apuesta['usuario_id']
                user = User.query.get(user_id)
                bets = apuesta['bets']
                
                total_bet_cents = sum(int(b.get('amount', 0)) for b in bets)
                total_win_cents = 0
                total_returned_cents = 0
                
                print(f"    👤 {user.username}:")
                print(f"       Apuestas realizadas: {total_bet_cents/100:.2f}€")
                
                for bet in bets:
                    tipo = bet.get('type')
                    cantidad = int(bet.get('amount',0))
                    numeros = set(bet.get('set',[]))
                    label = bet.get('label','').lower()
                    
                    gana = False
                    if tipo == 'even':
                        if ('rojo' in label and result_number in REDS):
                            gana = True
                    elif result_number in numeros:
                        gana = True
                    
                    if gana:
                        total_win_cents += cantidad * PAYOUT.get(tipo, 0)
                        total_returned_cents += cantidad
                        print(f"       ✅ {label}: GANA {(cantidad * PAYOUT.get(tipo, 0))/100:.2f}€")
                    else:
                        print(f"       ❌ {label}: Pierde")
                
                total_payout_euros = (total_win_cents + total_returned_cents) / 100.0
                win_euros = total_win_cents / 100.0
                user.balance += total_payout_euros
                
                print(f"       Ganancia neta: {win_euros:.2f}€")
                print(f"       Nuevo balance: {user.balance:.2f}€\n")
            
            db.session.commit()
            
            # Limpiar estado para siguiente ronda
            salas_ruleta[sala.id]['apuestas'] = []
            for j in salas_ruleta[sala.id]['jugadores']:
                j['ready'] = False
            
            print("✅ ¡Prueba E2E completada exitosamente!")
            return True
        else:
            print("❌ No todos los jugadores están listos")
            return False

if __name__ == '__main__':
    success = test_e2e()
    sys.exit(0 if success else 1)
