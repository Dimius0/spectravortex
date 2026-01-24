#!/usr/bin/env python3
"""
SpectraVortex - Main entry point
Photonic Programming Language
"""

import sys
import argparse
from compiler.lexer import Lexer
from compiler.parser import Parser
from simulator.field import OpticalField, PhotonState, Polarization, test_field
from simulator.elements import test_elements

def compile_file(filename: str):
    """Compile a SpectraVortex file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            source = f.read()
        
        print(f"=== Compiling {filename} ===")
        
        # Lexical analysis
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        print(f"Tokens: {len(tokens)}")
        if len(tokens) < 10:
            for token in tokens:
                print(f"  {token}")
        
        # Syntax analysis
        parser = Parser(tokens)
        ast = parser.parse()
        
        print(f"AST: {len(ast.statements)} statements")
        for i, stmt in enumerate(ast.statements):
            print(f"  {i}: {stmt.__class__.__name__}")
        
        return ast
        
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def run_simulation():
    """Run a simple simulation"""
    print("\n=== Running Simulation ===")
    
    # Create photons
    photon1 = PhotonState(
        frequency=193.414e12,  # 1550 nm
        amplitude=0.7,
        phase=0.0,
        oam_charge=0,
        polarization=Polarization.LINEAR,
        duration=100e-12
    )
    
    photon2 = PhotonState(
        frequency=193.414e12,
        amplitude=0.5,
        phase=3.14159,  # π phase difference
        oam_charge=0,
        polarization=Polarization.LINEAR,
        duration=100e-12
    )
    
    # Create fields
    field1 = OpticalField([photon1])
    field2 = OpticalField([photon2])
    
    # Interfere
    result = field1.interfere(field2)
    
    print(f"Field 1 intensity: {field1.total_intensity():.3f}")
    print(f"Field 2 intensity: {field2.total_intensity():.3f}")
    print(f"Interference result: {result.total_intensity():.3f}")
    
    # OAM spectrum
    spectrum = result.oam_spectrum()
    if spectrum:
        print("OAM Spectrum:")
        for charge, intensity in spectrum.items():
            print(f"  ℓ={charge}: {intensity:.3f}")
    
    return result

def interactive_mode():
    """Interactive mode"""
    print("\n" + "="*50)
    print("🌀 SpectraVortex Interactive Mode")
    print("="*50)
    print("Commands:")
    print("  compile <file>  - Compile SpectraVortex file")
    print("  simulate        - Run simulation")
    print("  test            - Run tests")
    print("  exit            - Exit")
    print()
    
    while True:
        try:
            command = input("svx> ").strip().lower()
            
            if not command:
                continue
                
            if command == "exit" or command == "quit":
                print("Goodbye!")
                break
                
            elif command.startswith("compile "):
                filename = command[8:].strip()
                compile_file(filename)
                
            elif command == "simulate":
                run_simulation()
                
            elif command == "test":
                print("\n=== Running Tests ===")
                test_field()
                print()
                test_elements()
                
            elif command == "help":
                print("Commands: compile, simulate, test, exit")
                
            else:
                print(f"Unknown command: {command}")
                print("Type 'help' for commands")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="SpectraVortex - Photonic Programming Language",
        epilog="Example: python main.py --compile example.svx"
    )
    
    parser.add_argument(
        "--compile", "-c",
        help="Compile a SpectraVortex file"
    )
    
    parser.add_argument(
        "--simulate", "-s",
        action="store_true",
        help="Run simulation"
    )
    
    parser.add_argument(
        "--test", "-t",
        action="store_true",
        help="Run tests"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Interactive mode"
    )
    
    parser.add_argument(
        "--version", "-v",
        action="store_true",
        help="Show version"
    )
    
    args = parser.parse_args()
    
    # Show banner
    print("="*50)
    print("🌀 SpectraVortex v0.1.0")
    print("Photonic Programming Language")
    print("="*50)
    
    if args.version:
        print("Version: 0.1.0")
        print("License: MIT")
        return
    
    if args.compile:
        compile_file(args.compile)
        
    if args.simulate:
        run_simulation()
        
    if args.test:
        print("\n=== Running Tests ===")
        test_field()
        print()
        test_elements()
    
    if args.interactive:
        interactive_mode()
    
    # If no arguments, show help
    if not any([args.compile, args.simulate, args.test, args.interactive, args.version]):
        parser.print_help()
        print("\nTry: python main.py --interactive")

if __name__ == "__main__":
    main()
# В main.py добавьте:
elif args.compile and "interference" in args.compile:
    print("Compiling interference example...")
    # Здесь будет вызов компилятора для interference.svx
    run_example("interference")
