# Este es un script para crear los archivos que faltan
# Ejecuta este script en la raíz de tu proyecto

import os
from pathlib import Path

# Crear directorios si no existen
directories = [
    "core",
    "nodes", 
    "nodes/base",
    "nodes/primitives",
    "utils",
    "utils/geometry",
    "ui"
]

for directory in directories:
    Path(directory).mkdir(parents=True, exist_ok=True)
    print(f"✅ Directorio creado/verificado: {directory}")

# Crear archivos __init__.py
init_files = [
    "core/__init__.py",
    "nodes/__init__.py",
    "nodes/base/__init__.py", 
    "nodes/primitives/__init__.py",
    "utils/__init__.py",
    "utils/geometry/__init__.py"
]

for init_file in init_files:
    with open(init_file, 'w', encoding='utf-8') as f:
        f.write('"""Módulo de GoboFlow"""\n')
    print(f"✅ Archivo creado: {init_file}")

print("\n🎉 Todos los directorios y archivos __init__.py han sido creados!")
print("\nAhora copia el contenido de los artifacts a estos archivos:")
print("1. core/socket_types.py")
print("2. nodes/base/base_node.py") 
print("3. utils/geometry/base_geometry.py")
print("4. nodes/primitives/circle_node.py")
print("5. config.py (en la raíz)")
print("6. ui/main_window.py")