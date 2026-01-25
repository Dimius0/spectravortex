#!/usr/bin/env python3
"""
SpectraVortex Main Entry Point
Photonic Computing Language with OAM Support
"""

import sys
import os
from typing import Optional

def add_project_to_path():
    """Add project directories to Python path"""
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)

def run_file(filename: str):
    """Run a SpectraVortex file"""
    try:
        from compiler import compile_source
        from simulator import Interpreter
        
        with open(filename, 'r') as f:
            source = f.read()
        
        print(f"Running {filename}...")
        print("=" * 60)
        
        # Compile
        ast = compile_source(source)
        
        # Execute
        interpreter = Interpreter()
        interpreter.run(ast)
        
        return True
        
    except FileNotFoundError:
        print(f"Error: File not found: {filename}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_oam_demo():
    """Run OAM vortex light demo"""
    from compiler import compile_source
    from simulator import Interpreter
    
    demo_source = """
// Quick OAM demo
vortex photon_plus3 = {
    oam_charge: +3,
    wavelength: 1550e-9,
    waist: 2.0,
    profile: "laguerre_gaussian"
}

vortex_beam lg_plus1 = laguerre_gaussian(
    oam_charge: +1,
    radial_order: 0,
    waist: 1.5
)

program quick_oam_demo() {
    print("=== Quick OAM Demo ===");
    print("Testing OAM charge +3 and LG beam +1");
    print();
    
    // Create interference
    interference = interfere(photon_plus3, lg_plus1);
    print("Interference created");
    print("Visibility:", interference.visibility);
    print();
    
    print("Demo completed!");
}
"""
    
    print("Running OAM demo...")
    print("=" * 60)
    
    ast = compile_source(demo_source)
    interpreter = Interpreter()
    interpreter.run(ast)
    
    print("=" * 60)
    print("OAM demo completed successfully!")
    return True

def run_matrix_demo():
    """Run matrix multiplication demo"""
    from compiler import compile_source
    from simulator import Interpreter
    
    demo_source = """
// Matrix multiplication demo
matrix_a = { 
    rows: 2, 
    cols: 2, 
    value: [
        [1.0, 2.0],
        [3.0, 4.0]
    ] 
}

matrix_b = { 
    rows: 2, 
    cols: 2, 
    value: [
        [0.5, 1.0],
        [1.5, 2.0]
    ] 
}

program matrix_demo() {
    print("=== Matrix Multiplication Demo ===");
    print("Matrix A:", matrix_a);
    print("Matrix B:", matrix_b);
    
    // Encode matrices
    encoded_a = encode_matrix(matrix_a);
    encoded_b = encode_matrix(matrix_b);
    
    // Optical multiplication
    result = optical_matmul(encoded_a, encoded_b);
    print("Result:", result);
    
    print("Demo completed!");
}
"""
    
    print("Running Matrix demo...")
    print("=" * 60)
    
    ast = compile_source(demo_source)
    interpreter = Interpreter()
    interpreter.run(ast)
    
    print("=" * 60)
    print("Matrix demo completed successfully!")
    return True

def run_interactive():
    """Run interactive REPL session"""
    from compiler import compile_source
    from simulator import Interpreter
    
    print("SpectraVortex Interactive REPL")
    print("Type 'exit' to quit, 'help' for commands")
    print("=" * 60)
    
    interpreter = Interpreter()
    line_buffer = []
    
    while True:
        try:
            if line_buffer:
                prompt = "... "
            else:
                prompt = "svx> "
            
            line = input(prompt).strip()
            
            if line.lower() == 'exit':
                print("Goodbye!")
                break
            elif line.lower() == 'help':
                print("Commands: exit, help, clear, run <file>")
                print("OAM examples:")
                print("  vortex v = { oam_charge: +1, wavelength: 1550e-9 }")
                print("  interfere(v, v)")
                continue
            elif line.lower() == 'clear':
                line_buffer = []
                print("[Buffer cleared]")
                continue
            elif line.startswith('run '):
                filename = line[4:].strip()
                run_file(filename)
                continue
            
            # Add to buffer
            line_buffer.append(line)
            
            # Check if we have a complete statement
            source = "\n".join(line_buffer)
            
            # Simple check for completeness
            if ';' in line or line.endswith('}') or not line:
                try:
                    ast = compile_source(source)
                    interpreter.run(ast)
                    line_buffer = []
                except SyntaxError as e:
                    print(f"Syntax error: {e}")
                    line_buffer = []
                except Exception as e:
                    print(f"Error: {e}")
                    line_buffer = []
        
        except EOFError:
            print("\nGoodbye!")
            break
        except KeyboardInterrupt:
            print("\nInterrupted. Type 'exit' to quit.")
            line_buffer = []

def show_version():
    """Show version information"""
    from compiler import get_version as get_compiler_version
    from simulator import get_version as get_simulator_version
    
    print(f"SpectraVortex Compiler v{get_compiler_version()}")
    print(f"SpectraVortex Simulator v{get_simulator_version()}")
    print("With OAM (Orbital Angular Momentum) support")
    print("MIT License")

def show_help():
    """Show help information"""
    print("SpectraVortex - Photonic Computing Language")
    print()
    print("Usage: python main.py [OPTION] [FILE]")
    print()
    print("Options:")
    print("  --run FILE         Run a SpectraVortex file (.svx)")
    print("  --oam-demo         Run OAM vortex light demo")
    print("  --matrix-demo      Run matrix multiplication demo")
    print("  --interactive      Start interactive REPL session")
    print("  --version          Show version information")
    print("  --help             Show this help message")
    print()
    print("Examples:")
    print("  python main.py --run examples/optical_matrix_multiplier.svx")
    print("  python main.py --oam-demo")
    print("  python main.py --interactive")
    print()
    print("Features:")
    print("  • Matrix operations for optical computing")
    print("  • OAM (vortex light) with physical validation")
    print("  • Type checking for physical correctness")
    print("  • Photon and beam definitions")

def main():
    """Main entry point"""
    add_project_to_path()
    
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "--run":
        if len(sys.argv) < 3:
            print("Error: Please specify a file to run")
            print("Usage: python main.py --run <filename.svx>")
            sys.exit(1)
        
        filename = sys.argv[2]
        if not filename.endswith('.svx'):
            print(f"Warning: Expected .svx file, got {filename}")
        
        success = run_file(filename)
        sys.exit(0 if success else 1)
    
    elif command == "--oam-demo":
        success = run_oam_demo()
        sys.exit(0 if success else 1)
    
    elif command == "--matrix-demo":
        success = run_matrix_demo()
        sys.exit(0 if success else 1)
    
    elif command == "--interactive":
        run_interactive()
        sys.exit(0)
    
    elif command == "--version":
        show_version()
        sys.exit(0)
    
    elif command == "--help":
        show_help()
        sys.exit(0)
    
    else:
        print(f"Error: Unknown command '{command}'")
        show_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
