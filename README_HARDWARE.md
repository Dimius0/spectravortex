# SpectraVortex Hardware Backend
## From Photonic Code to Physical Chips

**Status: Active Development (Working Prototype)**
> Transform SpectraVortex photonic programs into manufacturable Photonic Integrated Circuit (PIC) layouts.

This module completes the SpectraVortex development cycle by converting abstract descriptions of optical vortices and interference into concrete physical layouts, ready for export in the standard GDSII format.

## Quick Start in 5 Minutes

### Prerequisites
- Python 3.8+
- Installed spectravortex package (or being in the project root directory)
- Basic understanding of photonic integrated circuits

### Step 1: Verify Installation & Run Demo
Run the built-in demo to see all backend components in action:
python -m hardware_backend

text

Expected Output:
============================================================
SpectraVortex Hardware Backend Demo
============================================================

Testing Waveguide component...
Created: Straight waveguide: length=100.0μm, width=0.5μm
Loss: 0.15 dB

Testing MZI Interferometer...
Transfer matrix shape: (2, 2)
Coupling ratio: 0.50
... (other components) ...
============================================================
OK: All components initialized and tested successfully!
============================================================

text

### Step 2: Run the Full Test Suite
Ensure all functionality works correctly:
python test_hardware_backend.py --full

text

### Step 3: Compile Your First Chip
Use the test design to generate a GDSII file:
python main.py --compile-chip test_chip_design.svx my_first_chip.gds.json

text

### Step 4: Inspect the Results
1. Console Report: Chip metrics appear immediately after compilation.
2. Layout File: Open my_first_chip.gds.json to inspect the geometry.
3. Visualization (Optional): Use the example view_chip.py script.

## Project Structure
spectravortex/hardware_backend/
├── init.py
├── chip_designer.py
├── component_library.py
├── gdsii_generator.py
├── test_hardware_backend.py
└── technology_kits/
└── silicon_photonic_220nm.py

text

## Working with Key Components

### 1. Waveguides
```python
from hardware_backend import Waveguide

wg_straight = Waveguide(length=100.0, width=0.5)
print(wg_straight.get_path())
print(f"Loss: {wg_straight.calculate_loss():.2f} dB")
2. Mach-Zehnder Interferometers (MZI)
python
from hardware_backend import MZIInterferometer

mzi = MZIInterferometer(coupling_ratio=0.5, phase_shift=0.785)
matrix = mzi.get_transfer_matrix()
print(f"MZI matrix shape: {matrix.shape}")
3. OAM Mode Converters
python
from hardware_backend import OAMModeConverter

oam = OAMModeConverter(target_oam=2, efficiency=0.85)
pattern = oam.generate_phase_pattern()
print(f"Target OAM: {oam.target_oam}")
Chip Design Example
svx
vortex source_plus1 = {
    oam_charge: +1,
    wavelength: 1550e-9
}

program test_chip() {
    result = interfere(source_plus1, source_plus1);
    print("Result:", result.visibility);
}
Output Formats
Simplified GDSII JSON (Implemented):

text
python main.py --compile-chip design.svx output.gds.json
Full Binary GDSII (In Development):

text
python main.py --compile-chip design.svx --format gdsii output.gds
Testing
text
python test_hardware_backend.py --full
License
MIT License. See the LICENSE file in the project root.

Next Steps
Verify: python -m hardware_backend

Compile: python main.py --compile-chip test_chip_design.svx my_chip.gds.json

Extend: Add your own components to test_chip_design.svx

Questions and contributions are welcome!
