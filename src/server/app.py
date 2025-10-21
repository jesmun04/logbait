from flask import Flask
from flask_login import LoginManager
from models import db, User
from endpoints import register_blueprints  # importamos función que registrará todo automáticamente

app = Flask(__name__,
            template_folder='../templates',
            static_folder='../static')

# Configuración básica
app.config['SECRET_KEY'] = 'clave-secreta-casino-educativo-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///casino.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar extensiones
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Registrar todos los blueprints del paquete endpoints
register_blueprints(app)

# Inicializar DB
with app.app_context():
    db.create_all()
    print("✅ Base de datos inicializada")

if __name__ == '__main__':
    app.run(debug=True)
