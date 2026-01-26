markdown
# SpectraVortex Hardware Backend
## From Photonic Code to Physical Chips

**Status: ⚡ Active Development (Working Prototype)**
> Transform SpectraVortex photonic programs into manufacturable Photonic Integrated Circuit (PIC) layouts.

This module completes the SpectraVortex development cycle by converting abstract descriptions of optical vortices and interference into concrete physical layouts, ready for export in the standard GDSII format.

## 🚀 Quick Start in 5 Minutes

### Prerequisites
- **Python 3.8+**
- Installed `spectravortex` package (or being in the project root directory)
- Basic understanding of photonic integrated circuits

### Step 1: Verify Installation & Run Demo
Run the built-in demo to see all backend components in action:
```bash
python -m hardware_backend
Expected Output:

text
============================================================
SpectraVortex Hardware Backend Demo
============================================================
1. Testing Waveguide component...
   Created: Straight waveguide: length=100.0μm, width=0.5μm
   Loss: 0.15 dB
2. Testing MZI Interferometer...
   Transfer matrix shape: (2, 2)
   Coupling ratio: 0.50
... (other components) ...
============================================================
✅ All components initialized and tested successfully!
============================================================
Step 2: Run the Full Test Suite
Ensure all functionality works correctly:

bash
python test_hardware_backend.py --full
Step 3: Compile Your First Chip
Use the test design to generate a GDSII file:

bash
python main.py --compile-chip test_chip_design.svx my_first_chip.gds.json
Step 4: Inspect the Results
Console Report: Chip metrics appear immediately after compilation.

Layout File: Open my_first_chip.gds.json to inspect the geometry.

Visualization (Optional): Use the example view_chip.py script (see below).

🖥️ Real-World Output Examples
1. Chip Compiler Output
text
🛠️  Compiling test_chip_design.svx to photonic chip...
============================================================
📄 Parsing source code... Done
🎨 Designing photonic chip...
[ChipDesigner] Adding OAM source: source_plus1 (OAM=+1)
[ChipDesigner] Adding OAM source: source_minus2 (OAM=-2)
[ChipDesigner] Creating interference region
[ChipDesigner] Routing waveguides... Done
============================================================
CHIP DESIGN REPORT
============================================================
DESIGN METRICS:
  Total Area: 45000.0 μm²
  Total Loss: 0.04 dB
  Components: 3
  Waveguide Length: 200.0 μm
  Ports: 2
  Design Rule Violations: 0
TECHNOLOGY: silicon_photonic_220nm
✅ SUCCESS! Photonic chip saved to: my_first_chip.gds.json
2. Generated GDSII JSON Fragment
json
{
  "format": "GDSII_JSON",
  "version": "1.0",
  "scale": 1000,
  "units": "microns",
  "layers": {
    "1": [
      {
        "type": "waveguide",
        "points": [[0, 0], [100, 0]],
        "width": 0.5,
        "properties": {"component": "input_guide"}
      }
    ]
  },
  "structures": [
    {"name": "MAIN", "layer": 1, "placement": [0, 0]}
  ]
}
📁 Project Structure
text
spectravortex/hardware_backend/
├── __init__.py              # Main module & demo
├── chip_designer.py         # AST → Chip layout converter
├── component_library.py     # Photonic component library
├── gdsii_generator.py       # GDSII file generator (JSON)
├── test_hardware_backend.py # Full test suite
└── technology_kits/
    └── silicon_photonic_220nm.py  # Design rules for 220nm process
Key Files:

test_chip_design.svx – Example SpectraVortex chip description

main.py – Main compilation script

view_chip.py – Visualization script (to be created by user)

🔧 Working with Key Components
1. Waveguides
python
from hardware_backend import Waveguide

# Create straight and bent waveguides
wg_straight = Waveguide(length=100.0, width=0.5)
wg_bent = Waveguide.create_bend(radius=10.0, angle=90.0, width=0.5)

print(wg_straight.get_path())  # "Straight waveguide: length=100.0μm"
print(f"Loss: {wg_straight.calculate_loss():.2f} dB")
print(f"Bend loss: {wg_bent.calculate_bend_loss():.3f} dB")
2. Mach-Zehnder Interferometers (MZI)
python
from hardware_backend import MZIInterferometer

# Create MZI with specified coupling ratio and phase shift
mzi = MZIInterferometer(coupling_ratio=0.5, phase_shift=0.785)  # 45°
matrix = mzi.get_transfer_matrix()  # 2x2 unitary matrix
print(f"MZI matrix:\n{matrix}")
print(f"Through port efficiency: {mzi.get_through_port():.1%}")
3. OAM Mode Converters
python
from hardware_backend import OAMModeConverter

# Create converter to generate optical vortex
oam = OAMModeConverter(target_oam=2, efficiency=0.85)
pattern = oam.generate_phase_pattern()  # Spiral phase mask
print(f"Target OAM charge: +{oam.target_oam}")
print(f"Expected efficiency: {oam.efficiency:.1%}")
🎨 Chip Design: From Code to Silicon
Complete Design Pipeline
python
from compiler import compile_source  # SpectraVortex compiler
from hardware_backend import ChipDesigner, GDSIIGenerator

# 1. Parse SpectraVortex source code
source_code = """
vortex source_plus1 = { oam_charge: +1, wavelength: 1550e-9 }
vortex source_minus2 = { oam_charge: -2, wavelength: 1550e-9 }
program chip() { result = interfere(source_plus1, source_minus2); }
"""
ast = compile_source(source_code)

# 2. Create chip layout
designer = ChipDesigner(technology="silicon_photonic_220nm")
designer.design_from_ast(ast)

# 3. Generate report and GDSII
report = designer.generate_report()
print(report)

# 4. Export to GDSII JSON
gds_generator = GDSIIGenerator()
gds_data = designer.export_to_gds(gds_generator)
gds_generator.save("my_chip.gds.json")
Example Chip (test_chip_design.svx)
svx
// Define optical vortex sources
vortex source_plus1 = {
    oam_charge: +1,
    wavelength: 1550e-9,
    power_dbm: 0.0
}

vortex source_minus2 = {
    oam_charge: -2,
    wavelength: 1550e-9,
    power_dbm: -3.0
}

// Program describing their interference
program test_interference() {
    // Align two vortices
    aligned = align_phase(source_plus1, source_minus2);

    // Interfere in a multiplexer
    result = interfere(aligned.source1, aligned.source2);

    // Output results
    print("Interference visibility:", result.visibility);
    print("Output power:", result.power_dbm, "dBm");
}
📊 Design Metrics & Validation
The backend automatically calculates key metrics:

Metric	Description	Example Value
Total Area	Chip footprint in μm²	45000.0 μm²
Total Loss	Total optical propagation loss	0.04 dB
Component Count	Total photonic elements	3
Waveguide Length	Total routing length	200.0 μm
I/O Ports	Number of optical ports	2
Design Violations	Technology rule errors	0
Retrieving Metrics:

python
summary = designer.get_design_summary()
print(f"Chip area: {summary['total_area']} μm²")
print(f"Total loss: {summary['total_loss']} dB")
if summary['violations']:
    print(f"WARNING: {len(summary['violations'])} design rule violations!")
🏭 Supported Technology Processes
Silicon Photonic 220nm (SOI)
Standard Silicon-on-Insulator platform:

Waveguide core: 220 nm × 500 nm silicon

Cladding: SiO₂

Minimum feature size: 400 nm

Minimum bend radius: 5 μm

python
from hardware_backend import TECH_220NM, SiliconPhotonic220nm

# Using the global constant
print(TECH_220NM.name)  # "Silicon Photonic 220nm"
print(f"Min width: {TECH_220NM.rules['min_width']}μm")

# Creating an instance for validation
tech = SiliconPhotonic220nm()
errors = tech.validate_waveguide(width=0.3, radius=4.0)
if errors:
    print(f"Validation errors: {errors}")
💾 Output Formats
1. Simplified GDSII JSON (Implemented)
Human-readable JSON with full geometry description:

bash
python main.py --compile-chip design.svx output.gds.json
Advantages: Great for debugging, analysis, and conversion to other formats.

2. Full Binary GDSII (In Development)
Standard industrial format for foundry submission:

bash
python main.py --compile-chip design.svx --format gdsii output.gds
🧪 Testing & Debugging
Running Tests
bash
# Quick import check
python test_hardware_backend.py

# Full test suite with detailed output
python test_hardware_backend.py --full

# Test specific module
python -m pytest hardware_backend/component_library.py -v
Visualizing Results
Create a view_chip.py script to preview GDSII JSON:

python
import json
import matplotlib.pyplot as plt

def view_gds_json(filename):
    with open(filename) as f:
        data = json.load(f)
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    for layer_id, shapes in data['layers'].items():
        for shape in shapes:
            if shape['type'] == 'path':
                points = shape['points']
                xs, ys = zip(*points)
                ax.plot(xs, ys, label=f'Layer {layer_id}')
    
    ax.set_aspect('equal')
    ax.set_xlabel('X (μm)')
    ax.set_ylabel('Y (μm)')
    ax.set_title('Chip Layout Preview')
    ax.legend()
    plt.grid(True, alpha=0.3)
    plt.show()

if __name__ == "__main__":
    view_gds_json("my_first_chip.gds.json")
📚 API Reference (Summary)
ChipDesigner Class
python
class ChipDesigner:
    def __init__(self, technology="silicon_photonic_220nm")
    def design_from_ast(self, ast_node) -> 'ChipDesigner'
    def generate_report(self) -> str
    def get_design_summary(self) -> dict
    def export_to_gds(self, generator: GDSIIGenerator) -> dict
    def add_component(self, component: PhotonicComponent) -> None
    def validate_design(self) -> List[str]
Technology Rules
python
class SiliconPhotonic220nm:
    # Technology parameters
    name: str = "Silicon Photonic 220nm"
    waveguide_stack: dict = {"core": "Si", "cladding": "SiO2"}
    rules: dict = {"min_width": 0.4, "min_bend_radius": 5.0}
    
    # Methods
    def validate_waveguide(self, width: float, radius: float) -> List[str]
    def get_waveguide_properties(self, width: float) -> Dict
    def generate_tech_report(self) -> str
🔮 Roadmap & Future Features
Planned for Upcoming Releases:
Full Binary GDSII Support (Industry standard)

Automatic Waveguide Routing

Thermal Analysis for heaters and crosstalk

DRC Validation (Design Rule Checking)

Long-Term Goals:
Additional Technologies: SiN, LiNbO₃, polymers

3D Integration for multi-layer photonics

PDK Support for commercial processes

Simulator Integration (Lumerical, COMSOL)

🆘 Troubleshooting Common Issues
Problem	Likely Cause	Solution
ImportError	Incorrect Python path	Run from project root: cd spectravortex
FileNotFoundError	Missing design file	Check path: ls -la test_chip_design.svx
SyntaxError	Error in SpectraVortex code	Validate syntax: python main.py --run design.svx
Empty GDSII file	AST contains no components	Ensure code defines vortices (vortex)
Getting Help
Run the demo to verify setup: python -m hardware_backend

Study working examples in test_hardware_backend.py

Examine generated .gds.json files for geometry analysis

Use the --full flag for detailed test output

📄 License
MIT License. See the LICENSE file in the project root.

🎯 Next Steps After Setup
Verify Functionality: python -m hardware_backend

Compile the Example: python main.py --compile-chip test_chip_design.svx my_chip.gds.json

Extend the Test Design: Add your own components to test_chip_design.svx

Create a Visualizer: Implement view_chip.py to preview layouts

Integrate with Your Projects: Use ChipDesigner in your own scripts

Questions and contributions are welcome!
