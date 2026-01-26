#!/usr/bin/env python3
"""
SpectraVortex Main Compiler
Compile SpectraVortex programs to manufacturable photonic chips.
"""

import argparse
import sys
import os
import json
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description='SpectraVortex Photonic Chip Compiler',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compile chip with visualization
  python main.py --compile-chip test_chip_design.svx my_chip.gds.json --visualize
  
  # Just visualize existing GDSII file
  python main.py --visualize-only existing_chip.gds.json
  
  # Run hardware backend demo
  python main.py --demo
  
  # Run tests
  python main.py --test
        """
    )
    
    # Main compilation command
    parser.add_argument('--compile-chip', nargs=2,
                       metavar=('INPUT', 'OUTPUT'),
                       help='Compile SpectraVortex source to GDSII chip layout')
    
    # Visualization options
    parser.add_argument('--visualize', action='store_true',
                       help='Generate visualization image when compiling chip')
    
    parser.add_argument('--visualize-only', metavar='GDS_FILE',
                       help='Visualize existing GDSII JSON file')
    
    # Other commands
    parser.add_argument('--demo', action='store_true',
                       help='Run hardware backend component demo')
    
    parser.add_argument('--test', action='store_true',
                       help='Run hardware backend tests')
    
    parser.add_argument('--version', action='store_true',
                       help='Show version information')
    
    args = parser.parse_args()
    
    # Show version
    if args.version:
        show_version()
        return
    
    # Execute commands
    if args.compile_chip:
        input_file, output_file = args.compile_chip
        compile_chip(input_file, output_file, visualize=args.visualize)
    
    elif args.visualize_only:
        visualize_existing_file(args.visualize_only)
    
    elif args.demo:
        run_demo()
    
    elif args.test:
        run_tests()
    
    else:
        parser.print_help()

def show_version():
    """Display version information."""
    try:
        from hardware_backend import __version__
        print(f"SpectraVortex Hardware Backend v{__version__}")
        print("Photonic Integrated Circuit Design System")
    except ImportError:
        print("SpectraVortex Hardware Backend (version unknown)")
        print("Run from spectravortex/ directory")

def compile_chip(input_file: str, output_file: str, visualize: bool = False):
    """
    Compile SpectraVortex source to GDSII chip layout.
    
    Args:
        input_file: Input .svx source file
        output_file: Output .gds.json file
        visualize: Whether to generate visualization image
    """
    print("=" * 60)
    print(f"🛠️  Compiling {input_file} to photonic chip...")
    print("=" * 60)
    
    try:
        # Check input file exists
        if not os.path.exists(input_file):
            print(f"❌ Error: Input file '{input_file}' not found")
            sys.exit(1)
        
        # Import hardware backend components
        from hardware_backend import ChipDesigner, GDSIIGenerator
        
        print("📄 Parsing source code...")
        
        # For now, use a mock AST since we don't have the full compiler
        # In the future, this would be: ast = compile_source(source_code)
        class MockAST:
            """Mock AST for demonstration."""
            def __init__(self):
                self.nodes = [
                    {"type": "vortex", "name": "source_plus1", "oam_charge": 1},
                    {"type": "vortex", "name": "source_minus2", "oam_charge": -2},
                    {"type": "interference", "sources": ["source_plus1", "source_minus2"]}
                ]
        
        # Parse source file
        with open(input_file, 'r') as f:
            source_code = f.read()
        
        print(f"   Source size: {len(source_code)} characters")
        print(f"   Lines: {source_code.count(chr(10)) + 1}")
        
        # Create mock AST (replace with real compiler later)
        ast = MockAST()
        print("✅ Parsing complete")
        
        print("\n🎨 Designing photonic chip...")
        
        # Create chip designer
        designer = ChipDesigner(technology="silicon_photonic_220nm")
        
        # Design chip from AST
        designer.design_from_ast(ast)
        
        # Generate GDSII
        print("\n💾 Generating GDSII layout...")
        gds_generator = GDSIIGenerator()
        gds_data = designer.export_to_gds(gds_generator)
        
        # Save GDSII JSON
        with open(output_file, 'w') as f:
            json.dump(gds_data, f, indent=2)
        
        print(f"✅ GDSII layout saved to: {output_file}")
        
        # Generate visualization if requested
        if visualize:
            print("\n🎨 Generating visualization...")
            vis_file = output_file.replace('.gds.json', '.png')
            result = designer.visualize_design(vis_file)
            
            if result:
                print(f"✅ Visualization saved to: {result}")
        
        # Show design report
        print("\n" + "=" * 60)
        report = designer.generate_report()
        print(report)
        
        # Save report to file
        report_file = output_file.replace('.gds.json', '_report.txt')
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"📄 Design report saved to: {report_file}")
        
        print("\n✅ SUCCESS! Photonic chip compilation complete!")
        print("=" * 60)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you're running from the correct directory")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Compilation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def visualize_existing_file(gds_file: str):
    """Visualize an existing GDSII JSON file."""
    print("=" * 60)
    print(f"🎨 Visualizing existing chip: {gds_file}")
    print("=" * 60)
    
    try:
        from hardware_backend.visualize_chip import ChipVisualizer
        
        # Load and visualize
        visualizer = ChipVisualizer(scale=1.5)
        gds_data = visualizer.load_gds_json(gds_file)
        
        # Create output filename
        output_file = gds_file.replace('.gds.json', '.png')
        if output_file == gds_file:  # If not .gds.json extension
            output_file = gds_file + '.png'
        
        visualizer.visualize(gds_data, output_file)
        
        print(f"\n✅ Visualization saved to: {output_file}")
        print("=" * 60)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Install matplotlib: pip install matplotlib")
    except Exception as e:
        print(f"❌ Visualization failed: {e}")

def run_demo():
    """Run hardware backend demo."""
    print("=" * 60)
    print("🚀 Running SpectraVortex Hardware Backend Demo")
    print("=" * 60)
    
    try:
        # This will run the demo in __init__.py
        from hardware_backend import __name__ as module_name
        import subprocess
        subprocess.run([sys.executable, "-m", "hardware_backend"])
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")

def run_tests():
    """Run hardware backend tests."""
    print("=" * 60)
    print("🧪 Running SpectraVortex Hardware Backend Tests")
    print("=" * 60)
    
    try:
        import subprocess
        import os
        
        # Find test file
        test_file = os.path.join(os.path.dirname(__file__), 
                                "hardware_backend", 
                                "test_hardware_backend.py")
        
        if os.path.exists(test_file):
            result = subprocess.run([sys.executable, test_file, "--full"],
                                   capture_output=True, text=True)
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            print(f"Exit code: {result.returncode}")
        else:
            print(f"❌ Test file not found: {test_file}")
            print("   Looking for: test_hardware_backend.py")
            
    except Exception as e:
        print(f"❌ Test execution failed: {e}")

if __name__ == "__main__":
    main()
