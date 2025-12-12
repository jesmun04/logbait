# full_compatibility_check.py
import os
import re
from pathlib import Path

def check_sql_compatibility(file_path):
    """Revisa TODOS los problemas de compatibilidad SQLite -> PostgreSQL"""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        # 1. FUNCIONES DE FECHA/HORA SQLite
        date_patterns = [
            (r"datetime\s*\(\s*['\"][^'\"]*['\"]\s*\)", "datetime() function"),
            (r"date\s*\(\s*['\"][^'\"]*['\"]\s*\)", "date() function"),
            (r"strftime\s*\([^)]+\)", "strftime() function"),
            (r"time\s*\(\s*['\"][^'\"]*['\"]\s*\)", "time() function"),
        ]
        
        for pattern, description in date_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                issues.append(f"SQLite {description}: {match.group()}")
        
        # 2. PALABRAS CLAVE INCOMPATIBLES
        keywords = [
            "AUTOINCREMENT",
            "WITHOUT ROWID",
            "INTEGER PRIMARY KEY AUTOINCREMENT",
            "sqlite_sequence",
        ]
        
        for keyword in keywords:
            if keyword in content:
                issues.append(f"Keyword incompatible: {keyword}")
        
        # 3. SQL DIRECTO CON SINTAXIS SQLite
        sqlite_specific = [
            (r"INSERT OR IGNORE", "INSERT OR IGNORE"),
            (r"INSERT OR REPLACE", "INSERT OR REPLACE"), 
            (r"REPLACE INTO", "REPLACE INTO"),
            (r"ATTACH DATABASE", "ATTACH DATABASE"),
            (r"DETACH DATABASE", "DETACH DATABASE"),
        ]
        
        for pattern, description in sqlite_specific:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(f"SQLite {description}")
        
        # 4. TIPOS DE DATOS ESPECÍFICOS (solo si son definiciones de tabla)
        data_types = [
            "BLOB",
            "CLOB", 
        ]
        
        for data_type in data_types:
            if data_type in content and "db.Column" in content:
                lines_with_type = [i+1 for i, line in enumerate(lines) if data_type in line and "db.Column" in line]
                if lines_with_type:
                    issues.append(f"Data type: {data_type} en líneas {lines_with_type}")
        
        # 5. FUNCIONES DE CADENA SQLite en SQL directo
        string_functions = [
            (r"substr\s*\(", "substr()"),
            (r"glob\s*\([^)]*\)", "glob() function"),
        ]
        
        for pattern, func_name in string_functions:
            if re.search(pattern, content, re.IGNORECASE) and "db.session.execute" in content:
                issues.append(f"SQLite function: {func_name}")
        
        # 6. db.session.execute CON SQL DIRECTO problemático
        execute_matches = re.finditer(r"db\.session\.execute\s*\(\s*['\"`]([^'\"`]{30,})", content)
        for match in execute_matches:
            sql_snippet = match.group(1)
            # Verificar si tiene funciones SQLite específicas
            if any(func in sql_snippet.lower() for func in ['datetime(', 'date(', 'strftime(', 'julianday(']):
                issues.append(f"SQL directo con funciones SQLite: {sql_snippet[:80]}...")
        
        # 7. BÚSQUEDAS CASE-SENSITIVE en SQL directo
        if "LIKE" in content and "db.session.execute" in content and "ILIKE" not in content:
            issues.append("LIKE case-sensitive - considerar ILIKE para PostgreSQL")
        
        # 8. random() en JavaScript (no en Python)
        if "random()" in content and "Math.random()" not in content and file_path.suffix == '.html':
            issues.append("random() en JavaScript - usar Math.random()")
                
    except Exception as e:
        issues.append(f"Error leyendo archivo: {e}")
    
    return issues

def scan_full_project():
    """Escanea todo el proyecto profundamente"""
    project_root = Path(".")
    
    # Archivos a escanear
    target_extensions = ['.py', '.html']
    files_to_scan = []
    
    for ext in target_extensions:
        files_to_scan.extend(project_root.rglob(f"*{ext}"))
    
    print("🔍 ESCÁNER COMPLETO de compatibilidad PostgreSQL")
    print("📁 Proyecto: proyectois1-thatwasepic-main")
    print("📁 Buscando TODOS los tipos de problemas...\n")
    
    total_issues = 0
    files_with_issues = 0
    issue_categories = {}
    
    for file_path in files_to_scan:
        # Filtrar archivos grandes y de entorno virtual
        if (file_path.stat().st_size > 500000 or 
            "venv" in str(file_path) or 
            "__pycache__" in str(file_path) or
            ".git" in str(file_path) or
            "node_modules" in str(file_path)):
            continue
            
        issues = check_sql_compatibility(file_path)
        
        if issues:
            files_with_issues += 1
            total_issues += len(issues)
            
            print(f"🚨 {file_path}")
            for issue in issues:
                # Categorizar issues
                category = issue.split(':')[0] if ':' in issue else 'Otros'
                issue_categories[category] = issue_categories.get(category, 0) + 1
                
                print(f"   ⚠️  {issue}")
            print()
    
    # Resumen detallado
    print("📊 RESUMEN DETALLADO:")
    print(f"   Archivos revisados: {len(files_to_scan)}")
    print(f"   Archivos con problemas: {files_with_issues}")
    print(f"   Total de problemas: {total_issues}")
    
    if issue_categories:
        print(f"   Categorías de problemas:")
        for category, count in sorted(issue_categories.items()):
            print(f"     - {category}: {count} problemas")
    
    # Recomendaciones basadas en findings
    if total_issues > 0:
        print("\n🔧 RECOMENDACIONES:")
        if any("SQLite datetime" in cat for cat in issue_categories):
            print("   • Reemplazar datetime() con func.now() de SQLAlchemy")
        if any("SQLite date" in cat for cat in issue_categories):
            print("   • Reemplazar date() con func.current_date()")
        if "AUTOINCREMENT" in issue_categories:
            print("   • AUTOINCREMENT se maneja automáticamente en PostgreSQL")
        if any("SQL directo" in cat for cat in issue_categories):
            print("   • Revisar db.session.execute() con SQL directo")
        if any("random()" in cat for cat in issue_categories):
            print("   • En templates HTML, cambiar random() por Math.random()")
        if any("strftime" in cat for cat in issue_categories):
            print("   • En templates HTML, usar new Date().toLocaleString()")
    else:
        print("🎉 ¡No se encontraron problemas de compatibilidad!")
    
    return total_issues

if __name__ == "__main__":
    scan_full_project()