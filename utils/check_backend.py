# check_backend.py
import os
import re
from pathlib import Path

def check_python_files():
    """Revisa archivos Python del backend para problemas de PostgreSQL"""
    print("🔍 Revisando backend Python para compatibilidad PostgreSQL...")
    
    issues_found = False
    
    # Archivos Python críticos a revisar
    python_files = list(Path("src/server").rglob("*.py"))
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            issues = []
            
            # Buscar SQL directo con funciones SQLite
            if "db.session.execute" in content:
                # Buscar patrones problemáticos en SQL directo
                problematic_patterns = [
                    r"datetime\s*\([^)]*\)",
                    r"date\s*\([^)]*\)", 
                    r"strftime\s*\([^)]*\)",
                    r"LIKE\s+'[^']*'",  # LIKE case-sensitive
                ]
                
                for pattern in problematic_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        issues.append(f"SQL directo con: {pattern}")
            
            # Buscar AUTOINCREMENT explícito
            if "AUTOINCREMENT" in content:
                issues.append("AUTOINCREMENT explícito")
                
            if issues:
                issues_found = True
                print(f"❌ {file_path}")
                for issue in issues:
                    print(f"   ⚠️  {issue}")
                print()
                    
        except Exception as e:
            print(f"Error leyendo {file_path}: {e}")
    
    if not issues_found:
        print("✅ No se encontraron problemas en el backend Python")
    
    return issues_found

if __name__ == "__main__":
    check_python_files()