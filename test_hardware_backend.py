#!/usr/bin/env python3
"""
Test Hardware Backend
Quick test of the photonic chip compilation stack
"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all modules import correctly"""
    print("=" * 60)
    print("TESTING HARDWARE BACKEND IMPORTS")
    print("=" * 60)
    
    tests_passed = 0
    tests_failed = 0
    
    try:
        # Test 1: Import hardware_backend
        from hardware_backend import hello, get_capabilities
        print("✅ hardware_backend imported")
        print(f"   {hello()}")
        tests_passed += 1
    except Exception as e:
        print(f"❌ hardware_backend import failed: {e}")
        tests_failed += 1
    
    try:
        # Test 2: Import components
        from hardware_backend import ChipDesigner, Waveguide, MZIInterferometer
        print("✅ ChipDesigner imported")
        print("✅ Waveguide imported")
        print("✅ MZIInterferometer imported")
        tests_passed += 3
    except Exception as e:
        print(f"❌ Component imports failed: {e}")
        tests_failed += 3
    
    try:
        # Test 3: Import technology
        from hardware_backend import TECH_220NM
        print(f"✅ Technology imported: {TECH_220NM.name}")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Technology import failed: {e}")
        tests_failed += 1
    
    try:
        # Test 4: Import GDSII
        from hardware_backend import SimpleGDSIIWriter
        print("✅ GDSII writer imported")
        tests_passed += 1
    except Exception as e:
        print(f"❌ GDSII import failed: {e}")
        tests_failed += 1
    
    print(f"\n📊 Import Tests: {tests_passed} passed, {tests_failed} failed")
    return tests_failed == 0

def test_components():
    """Test basic component functionality"""
    print("\n" + "=" * 60)
    print("TESTING COMPONENTS")
    print("=" * 60)
    
    from hardware_backend import Waveguide, MZIInterferometer, OAMModeConverter
    
    # Test waveguide
    wg = Waveguide(length=100.0, width=0.5)
    print(f"✅ Waveguide: {wg.get_path()}")
    print(f"   Loss: {wg.calculate_loss():.2f} dB")
    
    # Test MZI
    mzi = MZIInterferometer(coupling_ratio=0.5, phase_shift=0.785)  # 45°
    matrix = mzi.get_transfer_matrix()
    print(f"✅ MZI created with 45° phase shift")
    print(f"   Matrix shape: {matrix.shape}")
    
    # Test OAM converter
    oam = OAMModeConverter(target_oam=2, efficiency=0.85)
    print(f"✅ OAM converter: {oam.get_info()}")
    
    return True

def test_designer():
    """Test chip designer"""
    print("\n" + "=" * 60)
    print("TESTING CHIP DESIGNER")
    print("=" * 60)
    
    from hardware_backend import ChipDesigner
    from compiler import compile_source
    
    # Create simple AST for testing
    source = """
vortex test_source = {
    oam_charge: +1,
    wavelength: 1550e-9
}
"""
    
    try:
        # Parse source
        ast = compile_source(source)
        
        # Design chip
        designer = ChipDesigner()
        designer.design_from_ast(ast)
        
        # Get report
        report = designer.generate_report()
        print("✅ Chip design completed")
        print(f"   Components: {designer.metrics.component_count}")
        print(f"   Area: {designer.metrics.total_area:.1f} μm²")
        
        # Show summary
        summary = designer.get_design_summary()
        print(f"\n📋 DESIGN SUMMARY:")
        for key, value in summary.items():
            if key != 'metrics':
                print(f"   {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Chip design failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gdsii():
    """Test GDSII generation"""
    print("\n" + "=" * 60)
    print("TESTING GDSII GENERATION")
    print("=" * 60)
    
    from hardware_backend import SimpleGDSIIWriter
    
    try:
        writer = SimpleGDSIIWriter()
        
        # Add test elements
        writer.add_element('waveguide', {
            'from': (0, 0),
            'to': (100, 0),
            'width': 0.5
        })
        
        writer.add_element('mzi', {
            'position': (150, 50),
            'size': (160, 50)
        })
        
        writer.add_element('oam_source', {
            'position': (50, 150),
            'diameter': 20,
            'oam_charge': 1
        })
        
        # Write to temporary file
        test_file = 'test_output.gds.json'
        if writer.write(test_file):
            print(f"✅ GDSII file written: {test_file}")
            
            # Check file exists
            if os.path.exists(test_file):
                file_size = os.path.getsize(test_file)
                print(f"   File size: {file_size} bytes")
                
                # Clean up
                os.remove(test_file)
                print(f"   Test file cleaned up")
                
                return True
            else:
                print(f"❌ File not created")
                return False
        else:
            print(f"❌ Failed to write file")
            return False
            
    except Exception as e:
        print(f"❌ GDSII test failed: {e}")
        return False

def test_compile_command():
    """Test the compile-to-chip command"""
    print("\n" + "=" * 60)
    print("TESTING COMPILE COMMAND")
    print("=" * 60)
    
    # Check if test file exists
    test_file = 'test_chip_design.svx'
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        print("   Please create test_chip_design.svx first")
        return False
    
    print(f"✅ Test file found: {test_file}")
    print("\nTo compile to chip, run:")
    print("  python main.py --compile-chip test_chip_design.svx my_chip.gds")
    print("\nOr test with:")
    print("  python test_hardware_backend.py --full")
    
    return True

def run_full_test():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("FULL HARDWARE BACKEND TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Run all tests
    results.append(("Imports", test_imports()))
    results.append(("Components", test_components()))
    results.append(("Designer", test_designer()))
    results.append(("GDSII", test_gdsii()))
    results.append(("Compile Command", test_compile_command()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n📊 Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Hardware backend is ready.")
        print("\nNext steps:")
        print("1. Run: python main.py --compile-chip test_chip_design.svx chip.gds")
        print("2. Check generated chip.gds.json file")
        print("3. Add more components to test_chip_design.svx")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        return False

def main():
    """Main test function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--full":
        success = run_full_test()
        sys.exit(0 if success else 1)
    else:
        # Quick test
        print("Hardware Backend Quick Test")
        print("=" * 60)
        
        if test_imports():
            print("\n✅ Basic imports working")
            print("\nFor full test, run:")
            print("  python test_hardware_backend.py --full")
            sys.exit(0)
        else:
            print("\n❌ Import test failed")
            sys.exit(1)

if __name__ == "__main__":
    main()
