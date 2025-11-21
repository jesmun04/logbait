# check_database.py
from app import app, db, User

with app.app_context():
    print("🔍 Verificando base de datos PostgreSQL...")
    
    # Contar usuarios
    user_count = User.query.count()
    print(f"👥 Usuarios en BD: {user_count}")
    
    # Listar usuarios
    users = User.query.all()
    for user in users:
        print(f" - {user.username} ({user.email})")
    
    # Verificar tablas
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"📊 Tablas: {tables}")