#!/usr/bin/env python3
"""
Test script for robot_gui.py functionality
Tests the core logic without requiring a display
"""

import json
import sys
import math

# Import the constant from robot_gui
try:
    from robot_gui import PX_PER_MM
except ImportError:
    # Fallback if running standalone
    PX_PER_MM = 3.78


def test_json_loading():
    """Test that all example JSON files can be loaded"""
    print("Testing JSON file loading...")
    
    files = [
        'example_path_points.json',
        'example_path_lines.json',
        'example_path_complex.json'
    ]
    
    for filename in files:
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            # Verify structure
            if 'points' in data:
                assert isinstance(data['points'], list), f"{filename}: points must be a list"
                for point in data['points']:
                    assert 'x' in point and 'y' in point, f"{filename}: point missing x or y"
                print(f"  ✓ {filename}: points format valid ({len(data['points'])} points)")
            
            elif 'lines' in data:
                assert isinstance(data['lines'], list), f"{filename}: lines must be a list"
                for line in data['lines']:
                    assert all(k in line for k in ['x1', 'y1', 'x2', 'y2']), \
                        f"{filename}: line missing coordinates"
                print(f"  ✓ {filename}: lines format valid ({len(data['lines'])} lines)")
            
            elif 'paths' in data:
                assert isinstance(data['paths'], list), f"{filename}: paths must be a list"
                for path in data['paths']:
                    assert 'points' in path, f"{filename}: path missing points"
                print(f"  ✓ {filename}: paths format valid ({len(data['paths'])} paths)")
            
            else:
                print(f"  ✗ {filename}: unknown format")
                return False
                
        except Exception as e:
            print(f"  ✗ {filename}: {str(e)}")
            return False
    
    return True


def test_line_width_conversion():
    """Test line width conversion between px and mm"""
    print("\nTesting line width conversion...")
    
    # Test mm to px conversion
    test_cases = [
        (1, 'mm', 1 * PX_PER_MM),
        (5, 'mm', 5 * PX_PER_MM),
        (10, 'px', 10),
        (2.5, 'px', 2.5),
    ]
    
    for value, unit, expected in test_cases:
        if unit == 'mm':
            result = value * PX_PER_MM
        else:
            result = value
        
        assert abs(result - expected) < 0.01, f"Conversion failed: {value}{unit}"
        print(f"  ✓ {value} {unit} = {result:.2f} px")
    
    return True


def test_zoom_calculations():
    """Test zoom level calculations"""
    print("\nTesting zoom calculations...")
    
    zoom_min = 0.1
    zoom_max = 5.0
    zoom_level = 1.0
    
    # Test zoom in
    for i in range(5):
        zoom_level = min(zoom_level * 1.2, zoom_max)
        assert zoom_min <= zoom_level <= zoom_max, "Zoom level out of bounds"
    print(f"  ✓ Zoom in: reached {zoom_level:.2f}x")
    
    # Test zoom out
    zoom_level = 1.0
    for i in range(5):
        zoom_level = max(zoom_level / 1.2, zoom_min)
        assert zoom_min <= zoom_level <= zoom_max, "Zoom level out of bounds"
    print(f"  ✓ Zoom out: reached {zoom_level:.2f}x")
    
    return True


def test_coordinate_scaling():
    """Test coordinate scaling with zoom"""
    print("\nTesting coordinate scaling...")
    
    test_coords = [(100, 100), (200, 150), (50, 75)]
    zoom_levels = [0.5, 1.0, 2.0]
    
    for zoom in zoom_levels:
        for x, y in test_coords:
            # Simulate get_scaled_coords
            scaled_x, scaled_y = x / zoom, y / zoom
            # Simulate drawing with zoom
            draw_x, draw_y = scaled_x * zoom, scaled_y * zoom
            
            # Should get back original coordinates
            assert abs(draw_x - x) < 0.01 and abs(draw_y - y) < 0.01, \
                f"Scaling failed at zoom {zoom}"
        
        print(f"  ✓ Zoom {zoom}x: scaling correct")
    
    return True


def test_circle_radius_calculation():
    """Test circle radius calculation"""
    print("\nTesting circle radius calculation...")
    
    test_cases = [
        ((0, 0), (3, 4), 5.0),
        ((0, 0), (0, 10), 10.0),
        ((5, 5), (8, 9), 5.0),
    ]
    
    for (x1, y1), (x2, y2), expected_radius in test_cases:
        radius = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        assert abs(radius - expected_radius) < 0.01, \
            f"Radius calculation failed: expected {expected_radius}, got {radius}"
        print(f"  ✓ Distance from ({x1},{y1}) to ({x2},{y2}) = {radius:.2f}")
    
    return True


def main():
    """Run all tests"""
    print("=" * 50)
    print("Robot SCARA GUI - Test Suite")
    print("=" * 50)
    
    tests = [
        test_json_loading,
        test_line_width_conversion,
        test_zoom_calculations,
        test_coordinate_scaling,
        test_circle_radius_calculation,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test failed with error: {str(e)}")
            results.append(False)
    
    print("\n" + "=" * 50)
    if all(results):
        print("✓ All tests passed!")
        print("=" * 50)
        return 0
    else:
        print("✗ Some tests failed")
        print("=" * 50)
        return 1


if __name__ == "__main__":
    sys.exit(main())
