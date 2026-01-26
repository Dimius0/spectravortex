#!/usr/bin/env python3
"""
Test full auto-routing pipeline.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hardware_backend import ChipDesigner, ChipVisualizer, GDSIIGenerator

def test_auto_route():
    """Test the complete auto-routing pipeline."""
    print("=" * 60)
    print("🚀 Testing SpectraVortex Auto-Routing Pipeline")
    print("=" * 60)
    
    # 1. Create chip designer
    print("\n1. Creating ChipDesigner...")
    designer = ChipDesigner(technology="silicon_photonic_220nm")
    
    # 2. Design chip (using mock AST)
    print("\n2. Designing chip from AST...")
    designer.design_from_ast(None)
    
    # 3. Run auto-routing
    print("\n3. Running auto-routing...")
    waveguides = designer.auto_route()
    
    if not waveguides:
        print("❌ Auto-routing failed!")
        return False
    
    print(f"   Created {len(waveguides)} waveguides")
    
    # 4. Generate GDSII
    print("\n4. Generating GDSII layout...")
    gds_generator = GDSIIGenerator()
    gds_data = designer.export_to_gds(gds_generator)
    
    # 5. Create visualization
    print("\n5. Creating visualization...")
    try:
        visualizer = ChipVisualizer(scale=1.5)
        visualizer.visualize(gds_data, "test_auto_route.png")
        print("   ✅ Visualization saved: test_auto_route.png")
    except Exception as e:
        print(f"   ⚠️  Visualization skipped: {e}")
    
    # 6. Generate report
    print("\n6. Generating design report...")
    report = designer.generate_report()
    print(report)
    
    # 7. Save report
    with open("test_auto_route_report.txt", "w") as f:
        f.write(report)
    print("   ✅ Report saved: test_auto_route_report.txt")
    
    # 8. Summary
    print("\n" + "=" * 60)
    print("📊 AUTO-ROUTING TEST SUMMARY")
    print("=" * 60)
    
    summary = designer.get_design_summary()
    print(f"Total components: {summary['component_count']}")
    print(f"Waveguides created: {len(waveguides)}")
    print(f"Total waveguide length: {summary['waveguide_length']:.1f} μm")
    print(f"Design violations: {len(summary['violations'])}")
    
    if summary['violations']:
        print("\n⚠️  Design violations found:")
        for violation in summary['violations']:
            print(f"   - {violation}")
    
    print("\n✅ Auto-routing pipeline test COMPLETED!")
    print("=" * 60)
    
    return True

def quick_test():
    """Quick test for basic functionality."""
    print("⚡ Quick test: ChipDesigner.auto_route()")
    
    designer = ChipDesigner()
    designer.design_from_ast(None)
    
    print("   Before auto_route:")
    print(f"   - Components: {designer.metrics.component_count}")
    
    waveguides = designer.auto_route()
    
    print("   After auto_route:")
    print(f"   - Components: {designer.metrics.component_count}")
    print(f"   - Waveguides created: {len(waveguides)}")
    
    if waveguides:
        for i, wg in enumerate(waveguides, 1):
            print(f"   - Waveguide {i}: {wg.name}, length: {wg.length:.1f}μm")
    
    return len(waveguides) > 0

if __name__ == "__main__":
    # Run quick test first
    print("🔧 Running quick test...")
    if quick_test():
        print("\n✅ Quick test passed! Running full pipeline...")
        test_auto_route()
    else:
        print("\n❌ Quick test failed. Check auto_router implementation.")
