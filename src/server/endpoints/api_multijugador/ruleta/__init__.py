from flask import Blueprint

bp = Blueprint('api_multijugador_ruleta', __name__)

from . import routes  # noqa
from . import socket_handlers  # noqa

# Registramos los handlers de socket.io al cargar el blueprint
def init_app(app, socketio):
    """Initialize the blueprint with Flask app and Socket.IO instance."""
    app.register_blueprint(bp, url_prefix='/api/multijugador/ruleta')
    socket_handlers.register_handlers(socketio)