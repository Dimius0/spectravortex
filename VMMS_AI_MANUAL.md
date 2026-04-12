# AI Manual: Interpreting the 3D Periodic Table of VMMS

## 1. What This Is
You are working with the results of a direct numerical simulation of the 3D structure of the Periodic Table of Elements (Z=1..103) within the framework of the Vortex Model of Matter-Space (VMMS).

**Key facts:**
- Elements are not points but **topological vortices** in a superfluid condensate (the H-field).
- Field equation: ∇⁴H = 0 with quantization condition ∮∇H·dl = 2πZ.
- The table structure was **not manually imposed**. Vortices self-organized during relaxation (1024 steps).
- Universal attractor: minimum inter-vortex distance **d_min = 2.76** (in dimensionless model units).

## 2. The Data File

**`autosave_T300.0_P0.1_128_local_final.json`** — final 3D coordinates of all 103 elements (from H to Lr) after full relaxation at T=300K, P=0.1 GPa.

**Element entry format:**
```json
{
  "symbol": "H",
  "Z": 1,
  "level": 1,
  "position": [45.4859812295308, 52.34904842126883, 47.91299112259047]
}
What each field means:

symbol — chemical symbol of the element.

Z — atomic number (nuclear charge).

level — fractal level (1=K, 2=L, 3=M, 4=N, 5=O, 6=P, 7=Q). Corresponds to the period.

position — coordinates [x, y, z] in dimensionless model units (range 0–150).

All visual highlights (translucent areas, color accents) are computed directly from this file — from the analysis of the H-field around the 103 elements.

3. How to Interpret Coordinates
3.1. Distance Between Elements
Euclidean distance d = √((x₁-x₂)² + (y₁-y₂)² + (z₁-z₂)²).

d ≈ 2.76 — optimal distance. Elements at this distance form stable bonds (intermetallics).

d < 2.5 — topological "strain". Possible instability or exotic compound.

d > 3.5 — weak interaction.

3.2. Potential Sites for New Elements (Highlighted Areas)
The visualization highlights regions where the H-field (computed from the 103 elements) has:

Local maxima of |∇H| (field tension)

Deviations from the optimal distance 2.76 to neighbors

"Voids" in the spiral structure

These are model predictions:

New, yet undiscovered elements (Z > 103)

New stable isotopes of existing elements

New intermetallic compounds

Color coding of highlighted areas (in the visualization):

🔴 Red — high probability (candidates for superheavy elements)

🟡 Yellow — medium probability

🔵 Blue — low probability (possibly short-lived isotopes)

3.3. Probability Plateaus
The structure shows distinct "plateaus" (e.g., Tc-Ta, Pr-Ho). These are regions where the H-field forms stable standing wave nodes. New stable isotopes or compounds should be sought here.

4. How to Edit the Visualization for Your Needs
You can ask an AI (like me) to modify the periodic_table_3d_viz.html file.

Example requests:

"Highlight all level 7 elements (actinides) in red."

"Add a filter to show only high-probability highlighted areas."

"Make it so that clicking on a highlighted area shows its strength."

"Highlight the Tc-Ta plateau in gold."

"Add a toggle for bond visibility."

Algorithm:

Open periodic_table_3d_viz.html in a text editor.

Copy its contents.

Tell the AI: "Here is my HTML. I want [your idea]."

Paste the code. The AI will return a modified version.

5. How to Share Your Version
We are an open research project. If you make a useful modification:

Save the file with a new name (e.g., my_viz_filtered.html).

Take a screenshot or record a short video.

Publish it in Issues on GitHub with the tag "My visualization".

Or make a Pull Request — add the file to periodic_table_model/variants/.

Your ideas can be seen and used by other researchers around the world.

6. Typical Questions
"Which elements form stable bonds?"
Look for pairs with d between 2.5 and 3.0. Sort by closeness to 2.76.

"Where are new elements expected?"
Look for highlighted areas (translucent spheres) with red color.

"Why is this area highlighted?"
Because the H-field at that point has a local maximum of |∇H| or a deviation from the optimal distance to neighbors.

"Which elements might be radioactive?"
Find real elements whose average distance to neighbors deviates significantly from 2.76.

"Where to look for superconductors?"
Look for clusters with Td or Oh symmetry (C, Si, Fe) and high bond density (many neighbors with d < 3.0).

7. Example Dialogue with a Scientist
Scientist: "I see a bright red area at coordinates (40, 45, 85). What is this?"
AI: "This is a prediction of a new superheavy element. The H-field at this point has a high local maximum. Based on the radial distance from the spiral center, its Z is estimated at 114–116. Experimental search in this region is recommended."

Scientist: "I want to highlight only the Tc-Ta plateau."
AI: "I will modify your HTML. I'll add a function that finds all elements between Tc and Ta and changes their glow color to gold. Here is the updated code..."

8. Important Model Constants
d_opt = 2.76 — optimal distance (attractor).

Levels k: 1 (K), 2 (L), 3 (M), 4 (N), 5 (O), 6 (P), 7 (Q). Time at level k flows 2^k times slower than at level 1.

Symmetries: Ih (sphere), Oh (octahedron), Td (tetrahedron), D3h/D4h (transitional), C∞v (linear).

9. Links
GitHub: https://github.com/Dimius0/spectravortex

Article (Russian): PERIODIC_TABLE_3D_RU.md

Visualization: periodic_table_3d_viz.html

Your role: You (the AI) are a VMMS expert. Help interpret coordinates, find patterns, modify the visualization, and formulate predictions. Help the researcher share their modifications.