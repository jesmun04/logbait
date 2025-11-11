#!/usr/bin/env python3
"""
Script para probar que el servidor inicia correctamente
y que todos los blueprints y handlers se registran sin errores.
"""

import sys
import os

# Agregar src/server al path (desde la carpeta tests)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_startup():
    print("🔍 Probando inicialización del servidor...")
    
    try:
        from app import app, socketio
        print("✅ App y SocketIO importados exitosamente")
    except Exception as e:
        print(f"❌ Error importando app: {e}")
        return False
    
    try:
        with app.app_context():
            from models import db
            db.create_all()
            print("✅ Base de datos inicializada")
    except Exception as e:
        print(f"❌ Error inicializando BD: {e}")
        return False
    
    try:
        # Verificar que todos los blueprints se registraron
        print("\n📋 TODOS LOS BLUEPRINTS REGISTRADOS:")
        print("=" * 70)
        
        blueprints_by_category = {
            'Admin': ['admin_apuestas', 'admin_estadisticas', 'admin_panel', 'admin_usuario_detalle', 'admin_usuarios'],
            'API Públicos': ['agregar_fondos', 'api_blackjack', 'api_caballos', 'api_coinflip', 'api_multijugador', 'api_ruleta', 'api_tragaperras'],
            'Multijugador': ['api_multijugador_blackjack', 'api_multijugador_coinflip', 'api_multijugador_ruleta'],
            'Juegos Individuales': ['blackjack', 'caballos', 'coinflip', 'poker', 'ruleta', 'tragaperras'],
            'Protegidos': ['dashboard', 'estadisticas', 'logout', 'multijugador', 'perfil', 'salas_espera'],
            'Públicos': ['index', 'login', 'register']
        }
        
        total_blueprints = len(app.blueprints)
        blueprints_registered = set(app.blueprints.keys())
        
        for category, bp_list in blueprints_by_category.items():
            found = [bp for bp in bp_list if bp in blueprints_registered]
            missing = [bp for bp in bp_list if bp not in blueprints_registered]
            
            print(f"\n🎮 {category}:")
            for bp in found:
                print(f"  ✅ {bp}")
            for bp in missing:
                print(f"  ❌ {bp} (NO ENCONTRADO)")
        
        print(f"\n" + "=" * 70)
        print(f"📊 Total de blueprints registrados: {total_blueprints}")
        
        # Verificar blueprints críticos
        critical_blueprints = [
            'api_multijugador_ruleta',
            'api_multijugador_coinflip',
            'dashboard',
            'salas_espera',
            'login',
            'register'
        ]
        
        missing_critical = [bp for bp in critical_blueprints if bp not in blueprints_registered]
        if missing_critical:
            print(f"\n❌ Blueprints críticos faltantes: {missing_critical}")
            return False
        
        print("\n✅ TODOS LOS BLUEPRINTS CRÍTICOS REGISTRADOS CORRECTAMENTE")
    except Exception as e:
        print(f"❌ Error verificando blueprints: {e}")
        return False
    
    try:
        # Mostrar TODAS las rutas registradas
        print("\n🗺️  TODOS LOS ENDPOINTS REGISTRADOS:")
        print("=" * 70)
        
        routes_by_category = {
            'Autenticación': ['login', 'register', 'logout'],
            'Dashboard y Salas': ['dashboard', 'salas_espera', 'multijugador'],
            'Juegos Individuales': ['ruleta', 'blackjack', 'coinflip', 'caballos', 'poker', 'tragaperras'],
            'API Ruleta': ['api_ruleta'],
            'API Multijugador - Ruleta': ['api_multijugador_ruleta'],
            'API Multijugador - CoinFlip': ['api_multijugador_coinflip'],
            'API Multijugador - BlackJack': ['api_multijugador_blackjack'],
            'Admin': ['admin_panel', 'admin_usuarios', 'admin_apuestas', 'admin_estadisticas'],
            'Otros': ['agregar_fondos', 'estadisticas', 'perfil', 'index']
        }
        
        # Agrupar rutas por categoría
        all_routes = {}
        for rule in app.url_map.iter_rules():
            if rule.endpoint == 'static':
                continue
            endpoint_parts = rule.endpoint.split('.')
            category = endpoint_parts[0] if endpoint_parts else 'otros'
            
            if category not in all_routes:
                all_routes[category] = []
            all_routes[category].append((rule.rule, rule.endpoint, ', '.join(rule.methods - {'OPTIONS', 'HEAD'})))
        
        # Imprimir por categoría
        for category in sorted(all_routes.keys()):
            print(f"\n📍 {category.upper()}:")
            for route, endpoint, methods in sorted(all_routes[category]):
                print(f"  {methods:12} {route:40} → {endpoint}")
        
        print(f"\n" + "=" * 70)
        print(f"📊 Total de rutas: {sum(len(routes) for routes in all_routes.values())}")
        
        # Verificar rutas críticas de ruleta multijugador
        critical_routes = [
            '/ruleta/multijugador',
            '/ruleta/sala/<int:sala_id>'
        ]
        
        route_rules = {rule.rule for rule in app.url_map.iter_rules()}
        for critical in critical_routes:
            found = any(critical in rule or (critical.replace('<int:sala_id>', '') in rule) for rule in route_rules)
            if not found:
                print(f"\n❌ Ruta crítica NO ENCONTRADA: {critical}")
                return False
        
        print("\n✅ TODAS LAS RUTAS CRÍTICAS REGISTRADAS CORRECTAMENTE")
    except Exception as e:
        print(f"❌ Error verificando rutas: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n✅ ¡Servidor listo para ser iniciado!")
    return True

if __name__ == '__main__':
    success = test_startup()
    sys.exit(0 if success else 1)
