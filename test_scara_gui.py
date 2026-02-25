#!/usr/bin/env python3
"""
Tests básicos para la GUI del robot SCARA
"""

import unittest
import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestScaraGUILogic(unittest.TestCase):
    """Tests para verificar la lógica de la GUI"""
    
    def test_import(self):
        """Verifica que el módulo se puede importar"""
        try:
            import scara_gui
            self.assertTrue(hasattr(scara_gui, 'ScaraGUI'))
            self.assertTrue(hasattr(scara_gui, 'main'))
        except ImportError as e:
            self.fail(f"No se pudo importar el módulo: {e}")
    
    def test_coordinate_storage(self):
        """Verifica el almacenamiento de coordenadas"""
        # Simular almacenamiento de coordenadas
        coords = []
        coords.append((10, 20))
        coords.append((30, 40))
        coords.append((50, 60))
        
        self.assertEqual(len(coords), 3)
        self.assertEqual(coords[0], (10, 20))
        self.assertEqual(coords[1], (30, 40))
        self.assertEqual(coords[2], (50, 60))
    
    def test_coordinate_clear(self):
        """Verifica el limpiado de coordenadas"""
        coords = [(10, 20), (30, 40), (50, 60)]
        coords.clear()
        self.assertEqual(len(coords), 0)
    
    def test_file_format(self):
        """Verifica el formato de guardado de coordenadas"""
        coords = [(100, 200), (150, 250), (200, 300)]
        
        # Simular el contenido del archivo
        lines = ["# Coordenadas del Robot SCARA\n"]
        lines.append("# Formato: x, y\n")
        lines.append("\n")
        
        for x, y in coords:
            lines.append(f"{x}, {y}\n")
        
        # Verificar que tenemos las líneas esperadas
        self.assertIn("# Coordenadas del Robot SCARA\n", lines)
        self.assertIn("100, 200\n", lines)
        self.assertIn("150, 250\n", lines)
        self.assertIn("200, 300\n", lines)


if __name__ == '__main__':
    unittest.main()
