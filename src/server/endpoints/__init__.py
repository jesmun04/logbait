import importlib
import pkgutil

def register_blueprints(app):
    package = __package__  # "endpoints"
    
    # Recorre recursivamente los subpaquetes dentro de "endpoints"
    for finder, name, ispkg in pkgutil.walk_packages(__path__, package + "."):
        try:
            module = importlib.import_module(f"{name}.routes")
            if hasattr(module, 'bp'):
                app.register_blueprint(module.bp)
                print(f"✅ Registrado blueprint: {name}")
        except ModuleNotFoundError:
            # No todos los subpaquetes tendrán un routes.py
            continue