# Ejecución del servidor
# ----------------------

$VenvDir = ".venv"
$RequirementsFile = "requirements.txt"

# Crear entorno virtual si no existe
if (-not (Test-Path $VenvDir)) {
    Write-Host "Creando entorno virtual..."
    python -m venv $VenvDir
} else {
    Write-Host "El entorno virtual ya existe."
}

# Activar entorno virtual
Write-Host "Activando entorno virtual..."
& "$VenvDir\Scripts\Activate.ps1"

# Instalar dependencias
if (Test-Path "$RequirementsFile") {
    Write-Host "Instalando dependencias (en caso de que falten)..."
    pip install -r $RequirementsFile
} else {
    Write-Host "ERROR: No se ha encontrado el archivo $RequirementsFile"
}

# Ejecutar servidor
Write-Host "Ejecutando servidor. Para detener el servidor, presiona Ctrl+C. Para salir del entorno virtual, introduce el comando 'deactivate'."
python app.py
