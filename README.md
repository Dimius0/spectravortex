markdown
# 🌀 SpectraVortex: A High-Level Language for Photonic Computing

**SpectraVortex** is a declarative programming language and compiler stack for designing and simulating photonic systems. Instead of describing low-level optical component geometries, you describe *what* you want to compute with light, and SpectraVortex figures out *how* to implement it as an optical circuit or simulation.

Think of it as a high-level language (like Python or C++) for the world of photonics, bridging the gap between abstract optical algorithms and physical implementations.

## ✨ Key Features

*   **Declarative, Wave-Optics Syntax**: Write programs using intuitive concepts like photons, beams, interference (`+`), and optical elements.
*   **Physical Correctness by Design**: The built-in type system enforces physical invariants (e.g., OAM charge, coherence).
*   **Multi-Target Compilation**: The same high-level program can be:
    *   **Simulated** using the built-in Python/NumPy simulator for verification.
    *   **Compiled to hardware layouts** (e.g., GDSII for photonic chip fabrication).
*   **Modern Toolchain**: Designed with a modern compiler architecture (lexer, parser, IR, optimizations, backends) for extensibility.

## 🚀 Quick Start

Get SpectraVortex running in under a minute.

1.  **Clone and enter the repository**:
    ```bash
    git clone https://github.com/Dimius0/spectravortex.git
    cd spectravortex
    ```

2.  **Install dependencies**:
    ```bash
    pip install numpy
    ```
    *(For a reproducible development environment, see `CONTRIBUTING.md`).*

3.  **Run a simple example**:
    ```bash
    python main.py --compile examples/hello_photon.svx
    ```

## 📖 A Taste of the Language

Here's a simple program that creates a photon and prints a message:

```spectravortex
// examples/hello_photon.svx
photon source = {
    frequency: 193.414e12, // 1550 nm telecom wavelength
    amplitude: 0.8,
    phase: 0.0,
    oam: 0,
    polarization: "linear"
}

program hello_photon() {
    print("Hello from the photonic realm!")
}
Want to see more? Check out the examples/ directory for demonstrations of interference, optical elements, and simple photonic algorithms.

🛠️ Project Structure
text
spectravortex/
├── compiler/          # Core compiler (lexer, parser, IR, type checker)
├── simulator/         # Optical field and component simulator
├── examples/          # Example SpectraVortex programs (.svx)
├── main.py            # Main CLI entry point
├── README.md          # This file
└── LICENSE            # MIT License
🧪 Testing & Development
Run the built-in test suite to verify everything works:

bash
python main.py --test
For an interactive session to experiment with optical states:

bash
python main.py --interactive
🧭 What's Next & Roadmap
SpectraVortex is under active development. The immediate next steps are:

v0.2 - Core Stabilization: Complete the type system, enhance error reporting, and add more standard library optical elements.

v0.5 - Performance & Usability: Integrate performance optimizations, improve the simulator's physical models, and create better documentation.

v1.0 - Hardware Integration: Stable release with robust backends for practical photonic hardware simulation and layout generation.

🤝 How to Contribute
Contributions are welcome and essential! Whether you're interested in compiler design, optical physics, or documentation, there's a place for you.

Please read our Contributing Guide for details on setting up your development environment, running tests, and submitting pull requests.

The easiest way to start is to look for issues tagged with good first issue.

📄 License
SpectraVortex is open-source software released under the MIT License. See the LICENSE file for full details.

🙏 Acknowledgments
This project explores the exciting intersection of programming language theory, compiler engineering, and wave optics. It draws inspiration from advances in photonic computing, quantum programming languages, and domain-specific compiler research.
