# 3D Periodic Table & Electronegativity: A First-Principles Derivation from VMMS

This directory contains the complete pipeline, scripts, and results for a direct numerical simulation of the 3D structure of the entire Periodic Table (103 elements) and a quantitative theory of electronegativity (χ) based on the Vortex Model of Matter-Space (VMMS).

**No empirical data was used to determine the elements' positions.** The vortices self-organized into their equilibrium 3D structure, driven solely by the H-field equation (`∇⁴H = 0`).

## Key Results

1.  **3D Periodic Table:** A system of 103 vortices was evolved over 1024 time steps. The resulting stable 3D configuration shows a minimum inter-vortex distance that converges to a universal attractor: **`d_min = 2.76`** (in dimensionless model units).
2.  **Fractal Time:** The model incorporates discrete time scales for 7 electron shells (K-Q), each differing by a factor of 2. This correction alone reduces the systematic error in binding energy for heavy nuclei (e.g., Uranium) from **-17% to -4.2%**.
3.  **Quantitative Electronegativity (χ):** A formula for χ was derived based on vortex parameters: symmetry, fractal level, nuclear spin, relativistic correction, neutron skin, and atomic radius screening. The model parameters were calibrated against the experimental Pauling scale using a least-squares method.
    *   **Accuracy:** Achieved a Mean Absolute Error (MAE) of **0.41** (R² = 0.49) on the Pauling scale.
    *   **Predictions:** The model provides calculated χ values for elements where experimental data is uncertain or missing (e.g., lanthanides and actinides).

## Directory Structure

*   **Documentation:**
    *   `PERIODIC_TABLE_3D.md` — this file.
    *   `periodic_table_model/README_3D_TABLE.md` — detailed technical description of the simulation pipeline.
    *   `periodic_table_model/results/README_RESULTS.md` — guide to the output JSON file structures.
*   **Scripts (`periodic_table_model/scripts/`):**
    *   `run_3d_table.py` — main driver for the 3D evolution, including thermodynamics, ionization, and fractal time.
    *   `compute_chi_ultimate_skin.py` — final script for χ calculation. It performs least-squares optimization (calibration) of 6 physical model parameters against the Pauling scale.
    *   `biharmonic_3d.py` — 3D solver for the `∇⁴H = 0` equation.
    *   `thermodynamics.py` — module for temperature (T) and pressure (P) effects.
    *   `fractal_time.py` — module for discrete multi-level time evolution.
*   **Results (`periodic_table_model/results/`):**
    *   `autosave_T300.0_P0.1_128_local_final.json` — final 3D coordinates and energy history for T=300K.
    *   `autosave_T5000.0_P0.1_128_local_final.json` — results for the high-temperature (T=5000K) regime.
    *   `chi_optimized.json` — calculated χ values from the final calibrated model.

## Main Findings

*   **Model Self-Consistency:** The 3D structure of the table is reproduced under different initial conditions and electronegativity values. This indicates that the vortex topology (charge Z, symmetry) is the primary factor determining its position and emergent properties.
*   **The Universal Attractor `2.76`:** The distance `d_min = 2.76` acts as an attractor for the H-field. Deviations from this value may indicate "topological strain" and correlate with elemental or compound instability (radioactivity).
*   **Environment-Dependent Stability:** The model suggests that a "topologically strained" environment (a specific chemical compound) can alter an element's stability. This effect could potentially either decrease stability (inducing radioactivity) or increase it (stabilizing radioactive isotopes).
*   **Neutron Skin Effect:** Model calibration indicates a dual role for the neutron skin: it increases the effective nuclear charge (`δ_n ≈ -0.77`) while simultaneously increasing the effective screening radius (`skin_screening ≈ 1.40`).

## Quick Start (Reproducing Results)

```bash
# 1. Navigate to the scripts directory
cd periodic_table_model/scripts

# 2. Run the 3D table evolution (Warning: ~3 hours on a typical CPU)
python run_3d_table.py --steps 1024 --grid 128 --T 300 --P 0.1

# 3. Calculate the refined electronegativity from the final state
python compute_chi_ultimate_skin.py
Authors & Acknowledgements
VMMS Concept & SpectraVortex Architecture: Dimius0 / Popov D.V., Popov R.D.

3D Table Simulation & χ Theory Research: Conducted in a co-creative scientific dialogue between Dimius0 and the DeepSeek language model, serving as a digital co-author and accelerator.

License: MIT License. See the LICENSE file for details.