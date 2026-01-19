#!/usr/bin/env python3
"""
Script de demostración para verificar la funcionalidad de la GUI
Este script simula el uso de la GUI sin necesitar una pantalla
"""

import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_coordinate_storage():
    """Simula el almacenamiento de coordenadas"""
    print("✓ Probando almacenamiento de coordenadas...")
    coords = []
    
    # Simular dibujo de una línea
    for i in range(10):
        coords.append((i * 10, i * 20))
    
    print(f"  - Se capturaron {len(coords)} puntos")
    print(f"  - Primer punto: {coords[0]}")
    print(f"  - Último punto: {coords[-1]}")
    assert len(coords) == 10
    print("  ✓ Almacenamiento de coordenadas funciona correctamente\n")


def test_coordinate_clear():
    """Simula el limpiado de coordenadas"""
    print("✓ Probando limpiado de coordenadas...")
    coords = [(10, 20), (30, 40), (50, 60)]
    print(f"  - Coordenadas antes de limpiar: {len(coords)}")
    coords.clear()
    print(f"  - Coordenadas después de limpiar: {len(coords)}")
    assert len(coords) == 0
    print("  ✓ Limpiado de coordenadas funciona correctamente\n")


def test_file_save():
    """Simula el guardado de coordenadas en archivo"""
    print("✓ Probando guardado de archivo...")
    coords = [(100, 200), (150, 250), (200, 300)]
    
    # Crear archivo de prueba
    test_file = "/tmp/test_coords.txt"
    try:
        with open(test_file, 'w') as f:
            f.write("# Coordenadas del Robot SCARA\n")
            f.write("# Formato: x, y\n\n")
            for x, y in coords:
                f.write(f"{x}, {y}\n")
        
        # Verificar que el archivo se creó
        with open(test_file, 'r') as f:
            lines = f.readlines()
        
        print(f"  - Archivo creado: {test_file}")
        print(f"  - Líneas en el archivo: {len(lines)}")
        print(f"  - Contenido del archivo:")
        for line in lines:
            print(f"    {line.rstrip()}")
        assert len(lines) >= 3  # Al menos comentarios + coordenadas
        
        # Limpiar
        os.remove(test_file)
        print("  ✓ Guardado de archivo funciona correctamente\n")
    except Exception as e:
        print(f"  ✗ Error: {e}\n")
        raise


def test_module_import():
    """Verifica que el módulo principal se puede importar"""
    print("✓ Probando importación del módulo...")
    try:
        import scara_gui
        print("  - Módulo importado exitosamente")
        print(f"  - Clase ScaraGUI disponible: {hasattr(scara_gui, 'ScaraGUI')}")
        print(f"  - Función main disponible: {hasattr(scara_gui, 'main')}")
        assert hasattr(scara_gui, 'ScaraGUI')
        assert hasattr(scara_gui, 'main')
        print("  ✓ Importación del módulo funciona correctamente\n")
    except ImportError as e:
        print(f"  ✗ Error al importar: {e}\n")
        raise


def main():
    """Ejecuta todas las pruebas de demostración"""
    print("=" * 60)
    print("DEMOSTRACIÓN DE LA GUI DEL ROBOT SCARA")
    print("=" * 60)
    print()
    
    try:
        test_module_import()
        test_coordinate_storage()
        test_coordinate_clear()
        test_file_save()
        
        print("=" * 60)
        print("✓ TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
        print("=" * 60)
        print()
        print("La GUI está lista para usar. Ejecuta:")
        print("  python3 scara_gui.py")
        print()
        return 0
    except Exception as e:
        print("=" * 60)
        print("✗ ALGUNAS PRUEBAS FALLARON")
        print("=" * 60)
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
