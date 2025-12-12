# fix_templates.py
import os
import re
from pathlib import Path

def fix_template_file(file_path):
    """Arregla los problemas de compatibilidad en templates HTML"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 1. Reemplazar strftime() con formato de fecha JavaScript
        strftime_replacements = {
            r"strftime\('%d/%m/%Y %H:%M'\)": "new Date().toLocaleString('es-ES')",
            r"strftime\('%d/%m/%Y %H:%M:%S'\)": "new Date().toLocaleString('es-ES')",
            r"strftime\('%d/%m/%Y'\)": "new Date().toLocaleDateString('es-ES')",
            r"strftime\('%H:%M'\)": "new Date().toLocaleTimeString('es-ES', {hour: '2-digit', minute: '2-digit'})",
            r"strftime\('%H:%M:%S'\)": "new Date().toLocaleTimeString('es-ES')",
        }
        
        for pattern, replacement in strftime_replacements.items():
            content = re.sub(pattern, replacement, content)
        
        # 2. Reemplazar time() (probablemente error, debería ser strftime)
        time_replacements = {
            r"time\('%d/%m/%Y %H:%M'\)": "new Date().toLocaleString('es-ES')",
            r"time\('%d/%m/%Y %H:%M:%S'\)": "new Date().toLocaleString('es-ES')",
            r"time\('%d/%m/%Y'\)": "new Date().toLocaleDateString('es-ES')",
            r"time\('%H:%M'\)": "new Date().toLocaleTimeString('es-ES', {hour: '2-digit', minute: '2-digit'})",
            r"time\('%H:%M:%S'\)": "new Date().toLocaleTimeString('es-ES')",
        }
        
        for pattern, replacement in time_replacements.items():
            content = re.sub(pattern, replacement, content)
        
        # 3. Reemplazar random() por Math.random() (solo si no tiene Math.)
        content = re.sub(r'(?<![a-zA-Z.])\brandom\s*\(\s*\)', 'Math.random()', content)
        
        # Guardar solo si hubo cambios
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
        
    except Exception as e:
        print(f"❌ Error arreglando {file_path}: {e}")
        return False

def fix_all_templates():
    """Arregla todos los templates problemáticos"""
    problematic_files = [
        "src/templates/pages/casino/estadisticas/estadisticas.html",
        "src/templates/pages/casino/perfil/perfil.html",
        "src/templates/pages/casino/juegos/multiplayer/ruleta.html",
        "src/templates/pages/casino/juegos/singleplayer/blackjack.html",
        "src/templates/pages/casino/juegos/singleplayer/caballos.html",
        "src/templates/pages/casino/juegos/singleplayer/coinflip.html",
        "src/templates/pages/casino/juegos/singleplayer/poker.html",
        "src/templates/pages/casino/juegos/singleplayer/ruleta.html",
        "src/templates/pages/casino/juegos/singleplayer/tragaperras.html",
        "src/templates/pages/admin/apuestas/apuestas.html",
        "src/templates/pages/admin/estadisticas/estadisticas.html",
        "src/templates/pages/admin/inicio/index.html",
        "src/templates/pages/admin/usuarios/usuarios.html",
        "src/templates/pages/admin/usuarios/usuarios_detalle.html",
    ]
    
    print("🔧 Arreglando templates HTML...")
    fixed_count = 0
    
    for file_path in problematic_files:
        if os.path.exists(file_path):
            if fix_template_file(file_path):
                print(f"✅ Arreglado: {file_path}")
                fixed_count += 1
            else:
                print(f"ℹ️  Sin cambios: {file_path}")
        else:
            print(f"❌ No encontrado: {file_path}")
    
    print(f"\n📊 Resumen: {fixed_count} archivos arreglados")

if __name__ == "__main__":
    fix_all_templates()