# SpectraVortex Hardware Backend
## From Photonic Code to Physical Chips

**Status: Active Development (Working Prototype)**
> Transform SpectraVortex photonic programs into manufacturable Photonic Integrated Circuit (PIC) layouts.

This module completes the SpectraVortex development cycle by converting abstract descriptions of optical vortices and interference into concrete physical layouts, ready for export in the standard GDSII format.

## 🎨 New: Chip Visualization!
**Now with automatic visualizations!** Generate beautiful 2D layouts of your photonic chips with a single flag.

## Quick Start in 5 Minutes

### Prerequisites
- **Python 3.8+**
- Installed `spectravortex` package (or being in the project root directory)
- **For visualization:** `pip install matplotlib`
- Basic understanding of photonic integrated circuits

### Step 1: Verify Installation & Run Demo
Run the built-in demo to see all backend components in action:
```bash
cd spectravortex
python main.py --demo
Expected Output:

text
============================================================
🚀 Running SpectraVortex Hardware Backend Demo
============================================================
1. Testing Waveguide component...
   Created: Straight waveguide: length=100.0μm, width=0.5μm
   Loss: 0.15 dB
2. Testing MZI Interferometer...
   Transfer matrix shape: (2, 2)
   Coupling ratio: 0.50
... (other components) ...
6. Testing Chip Visualizer...
   Visualizer initialized successfully
   Created demo with 2 layers
✅ All components initialized successfully!
============================================================
Step 2: Compile Your First Chip (With Visualization!)
Compile a SpectraVortex program to GDSII with automatic visualization:

bash
python main.py --compile-chip test_chip_design.svx my_first_chip.gds.json --visualize
Output includes:

✅ GDSII JSON file (my_first_chip.gds.json)

✅ PNG visualization (my_first_chip.png)

✅ Design report (my_first_chip_report.txt)

Step 3: Visualize Existing GDSII Files
Already have a GDSII JSON file? Visualize it:

bash
python main.py --visualize-only existing_chip.gds.json
Step 4: Run Tests
Ensure everything works correctly:

bash
python main.py --test
🖼️ Example Visualization Output
When you compile with --visualize, you get a professional chip layout image:

https://demo_chip.png

Features shown:

Blue lines: Optical waveguides

Red rectangles: MZI interferometers

Purple circles: OAM mode converters

Layer differentiation: Different colors for different process layers

Automatic scaling and labels

Complete Compilation Pipeline
From Code to Chip Visualization:
bash
# 1. Write your SpectraVortex program
nano my_design.svx

# 2. Compile to GDSII with visualization
python main.py --compile-chip my_design.svx output.gds.json --visualize

# 3. Check the results
ls -la output.*
# output.gds.json     # GDSII layout (JSON format)
# output.png          # Chip visualization
# output_report.txt   # Design metrics report
Example Chip Design (test_chip_design.svx)
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
New API Features
1. ChipVisualizer Class
python
from hardware_backend import ChipVisualizer

# Load and visualize GDSII file
visualizer = ChipVisualizer(scale=1.5)
gds_data = visualizer.load_gds_json("chip.gds.json")
visualizer.visualize(gds_data, "chip_layout.png")

# Create demo visualization
demo_data = visualizer.create_simple_demo()
visualizer.visualize(demo_data, "demo.png")
2. Automatic Visualization in ChipDesigner
python
from hardware_backend import ChipDesigner

# Design a chip
designer = ChipDesigner(technology="silicon_photonic_220nm")
designer.design_from_ast(ast)

# Generate visualization automatically
image_path = designer.visualize_design("my_chip_layout.png")
print(f"Visualization saved to: {image_path}")
3. Command Line Interface
bash
# Show help
python main.py --help

# Show version
python main.py --version

# Just visualize existing file
python main.py --visualize-only chip.gds.json

# Run component demo
python main.py --demo
Project Structure
text
spectravortex/
├── main.py                      # Main compiler with visualization
├── hardware_backend/
│   ├── __init__.py             # Main module exports
│   ├── visualize_chip.py       # NEW: Chip visualization module
│   ├── chip_designer.py        # Enhanced with visualize_design()
│   ├── component_library.py    # Photonic components
│   ├── gdsii_generator.py      # GDSII file generation
│   ├── test_hardware_backend.py # Test suite
│   └── technology_kits/
│       └── silicon_photonic_220nm.py
└── test_chip_design.svx        # Example chip design
Installation & Dependencies
Basic Installation:
bash
# Clone repository
git clone <repository-url>
cd spectravortex

# Install core dependencies
pip install -e .
For Visualization Features:
bash
# Install matplotlib for visualization
pip install matplotlib
Testing:
bash
# Run all tests
python main.py --test

# Or directly
python hardware_backend/test_hardware_backend.py --full
Design Metrics & Validation
The backend automatically calculates key metrics and generates reports:

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
Troubleshooting
Common Issues:
Problem	Solution
"ModuleNotFoundError: No module named 'matplotlib'"	Install: pip install matplotlib
Visualization shows blank image	Check GDSII file contains valid geometry
"ImportError" when running main.py	Run from spectravortex/ directory
Tests fail in CI/CD	GitHub Actions installs matplotlib automatically
Getting Help:
Run the demo: python main.py --demo

Check tests: python main.py --test

Examine generated .gds.json files

Use --visualize-only to debug existing files

Roadmap & Future Features
✅ Completed This Week:
Chip Visualization Module (visualize_chip.py)

Integrated visualization into ChipDesigner

Command line interface with --visualize flag

CI/CD compatibility (headless matplotlib)

Planned for Next Week:
Automatic Waveguide Routing

Interactive Web Visualizer (HTML/JavaScript)

More component types (grating couplers, splitters)

3D Visualization option

Long-Term Goals:
Full Binary GDSII Support (Industry standard)

Thermal Analysis for heaters and crosstalk

DRC Validation (Design Rule Checking)

PDK Support for commercial processes

Next Steps After Setup
Try the full pipeline:

bash
python main.py --compile-chip test_chip_design.svx my_chip.gds.json --visualize
Create your own design:

Edit test_chip_design.svx or create new .svx files

Experiment with different components

Extend the visualizer:

Add more component types

Customize color schemes

Add measurement annotations

Integrate with your workflow:

Use ChipDesigner in your Python scripts

Automate with CI/CD pipelines

Generate documentation with visualizations

License
MIT License. See the LICENSE file in the project root.

Questions and contributions are welcome! Try the new visualization features and share your feedback!
