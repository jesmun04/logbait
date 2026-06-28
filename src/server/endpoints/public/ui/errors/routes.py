from flask import Blueprint, render_template

bp = Blueprint('errors', __name__)

ERROR_CODES = [400, 401, 403, 404, 405, 500, 502, 503, 504]

def handle_error(e):
    # Werkzeug pasa el objeto de error. 
    # .code contiene el número (ej. 404) y .name el nombre oficial (ej. "Not Found")
    error_code = getattr(e, 'code', 500)
    error_name = getattr(e, 'name', 'Internal Server Error')
    
    # Pasamos el código y el nombre directamente a una única plantilla genérica
    return render_template('pages/errors/error.html', error_code=error_code, error_name=error_name), error_code

# Registramos la función dinámicamente para cada código de la lista
for code in ERROR_CODES:
    bp.app_errorhandler(code)(handle_error)