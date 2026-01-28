# 🌀 SpectraVortex: A Language and Platform for Photonic Computing

**SpectraVortex** is a declarative programming language and full compiler stack for designing and simulating photonic systems. Instead of describing low-level optical component geometry, you describe *what* you want to compute with light, and SpectraVortex figures out *how* to implement it.

It's a high-level language for photonics enhanced with intelligent analysis tools for creating more resilient designs.

## ✨ Key Features

* **Declarative, Wave-Optics Syntax**: Write programs using intuitive concepts: photons, beams, interference (`+`), and optical elements.
* **Physical Correctness by Design**: The built-in type system enforces physical invariants (e.g., Orbital Angular Momentum, coherence).
* **Multi-Target Compilation**: The same high-level program can be:
  * **Simulated** using the built-in Python/NumPy simulator for verification.
  * **Compiled to hardware layouts** (e.g., GDSII for photonic chip fabrication).
* **Intelligent Solver System (Phase 3)**: Advanced algorithms for analyzing and optimizing photonic circuit designs.

## 🧩 Phase 3: Intelligent Design System (IMPLEMENTED ✅)

SpectraVortex is now more than a compiler—it's a platform for **resilient photonic design** with built-in analysis tools:

### 3.1 🧵 Stitching Solver
**Combines** partial optical circuit solutions into complete topologies through boundary analysis.

### 3.2 🌀 Recursive Solver
**Decomposes** complex problems using recursive, self-similar patterns for efficient solving.

### 3.3 ⚡ Resilience Manager
**Analyzes and improves** the robustness of photonic designs:
* 🛡️ **Risk Assessment**: Tests circuits against 7 types of photonic failures (waveguide defects, resonator drift, etc.).
* 🔄 **Topology Comparison**: For OAM systems, generates and compares 4 alternative implementation variants.
* 🧠 **Design Recommendations**: Suggests strategies for increasing reliability and potential reconfiguration paths.

> **Note**: This is not an autonomous AI, but an **advanced analysis system** that provides engineers with data-driven insights to create more failure-tolerant photonic systems.

```python
# Example: Using the Resilience Analyzer
from simulator.resilience.resilience_manager import ResilienceManager

resilience_mgr = ResilienceManager()
report = resilience_mgr.analyze_resilience(oam_problem)

print(f"Recommended topology: {report.best_alternative_id}")
print(f"Expected resilience improvement: {report.resilience_improvement:.1%}")...
🚀 Quick Start
Get SpectraVortex running in under a minute.

Clone and enter the repository:
git clone https://github.com/Dimius0/spectravortex.git
cd spectravortex
Install dependencies:
pip install numpy
(For a reproducible development environment, see CONTRIBUTING.md).

Run a simple example:
python main.py --compile examples/hello_photon.svx
