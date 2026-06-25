# TEES — Quickstart for Researchers

**Emergent Physical Fingerprint (EPF) via Navier-Stokes Turbulence**

> ⚡ **5 minutes to your first vortex fingerprint.**

---

## 🎯 What you'll get

A **physical fingerprint** from any input string (Bitcoin address, text, file hash):

1. Input → SHA256 → spectral field
2. Field evolves via **Navier-Stokes** (turbulent regime)
3. RANSAC extracts vortex parameters (Γ, VSM)
4. Output: **16‑char fingerprint** + stability metrics

✅ **Non-reversible** (ill-posed inverse problem)  
✅ **Deterministic** (same input → same vortex)  
✅ **Emergent** (vortex self-organizes from noise)  
❌ **Not collision‑resistant** (we don't claim it is)

---

## 🚀 Run it now

```bash
# Clone
git clone https://github.com/Dimius0/spectravortex.git
cd spectravortex

# Install dependencies (minimal)
pip install numpy scipy scikit-learn

# Run on your own data
python tees_biharmonic_v19.py
Expected output (last lines):

text
Vortex stats: 56% stable (VSM > 0.7)
Sample fingerprint: a3f2c1e4b8d9f6a7
Non-reversibility: 4/4 proofs passed
📊 What the numbers mean
Metric	Value	Interpretation
VSM	> 0.7	Stable vortex → reliable fingerprint
VSM	0.3–0.7	Transitional → use with caution
VSM	< 0.3	Noise → input didn't excite a vortex
Stability rate	~56%	Fraction of inputs yielding stable vortices
Non‑reversibility	≥3/4 proofs	Mathematically irreversible
🧪 Try your own input
Edit the last lines of tees_biharmonic_v19.py:

python
if __name__ == "__main__":
    # Replace with your string
    test_string = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"  # Genesis block
    result = generate_vortex_fingerprint(test_string)
    print(f"Fingerprint: {result['fingerprint']}")
    print(f"VSM: {result['vsm']:.3f}")
    print(f"Gamma: {result['gamma']:.3f}")
Want to test on 1034 Bitcoin addresses?
→ Collect them yourself (e.g., from blockchain explorers) or generate a test set.
We don't include them in the repo — you bring your own data.

🔬 For the curious
Why Navier-Stokes?
Ill‑posed inverse problem → non‑reversibility is physical, not heuristic

Turbulence → extreme sensitivity to initial conditions (avalanche effect)

Self‑organization → vortices emerge from noise (no pre‑defined structure)

Two stability modes (experimental)
Wave mode (Γ = 0.3–0.6) — weak circulation, high coherence

Vortex mode (Γ = 1.1–1.6) — classical Lamb‑Oseen vortex

What about collisions?
We don't hide them. If two inputs yield the same fingerprint, it's data, not a bug.
→ Open an Issue with both inputs, and we'll explore the topological similarity.

🛠️ Next steps for contributors
GPU‑accelerate → CUDA/OpenCL (1000× speedup potential)

Microfluidics HW → real vortices in micro‑channels (µW power)

Collision analysis → graph of vortex states (network science)

3D visualization → see your vortex in viewer.html

📚 Files you need
File	Purpose
tees_biharmonic_v19.py	Main implementation
README_TEES.md	Full documentation & philosophy
viewer.html	3D vortex visualizer (optional)
🧠 Philosophy (one paragraph)
"TEES is not a hash function. It's a physical fingerprint — a proof that turbulence can remember. We don't claim collisions don't exist; we claim they're interesting. This is research, not production. Explore, break, improve."