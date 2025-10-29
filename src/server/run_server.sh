#!/bin/bash

# Ejecución del servidor
# ----------------------

# Detener el script si ocurre algún error
set -e

# Rutas y archivos
VENV_DIR=".venv"
REQUIREMENTS_FILE="requirements.txt"

# Crear entorno virtual si no existe
if [ ! -d "$VENV_DIR" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv "$VENV_DIR"
else
    echo "El entorno virtual ya existe."
fi

# Activar entorno virtual
echo "Activando entorno virtual..."
source "$VENV_DIR/bin/activate"

# Instalar dependencias si es necesario
if [ -f $REQUIREMENTS_FILE ]; then
    echo "Instalando dependencias (en caso de que falten)..."
    pip install -r "$REQUIREMENTS_FILE"
else
    echo "ERROR: No se ha encontrado el archivo $REQUIREMENTS_FILE"
fi

# Ejecutar servidor
echo "Ejecutando servidor. Para detener el servidor, presiona Ctrl+C. Para salir del entorno virtual, introduce el comando 'deactivate'."
python app.py