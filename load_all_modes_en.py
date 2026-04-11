"""
Load all modes into field H (English version)
Version 1.0 — fundamental modes + dialogues + new domains
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import random
import hashlib
from datetime import datetime
from rizoma.personality import Personality, SpectralMode
from rizoma.selector import Selector

print("="*70)
print("🌊 LOADING FIELD H — ALL MODES (ENGLISH)")
print("="*70)

# Create personality
p = Personality(id="p016", name="Collective Mind of SpectraVortex", tau=5.0, k=2)
p.selector = Selector(p)

# ============================================================
# 1. BASE VMMS MODES (from discoveries)
# ============================================================
print("\n📚 STEP 1: Loading base VMMS modes")

base_modes = [
    # Physics — vmms_monism
    SpectralMode(
        tau=5.20,
        amplitude=0.8,
        content="Matter = Space. Spacetime is a quantum superfluid condensate. Particles and fields are topological defects (vortices) in this condensate. ∇⁴ψ = 0 — the biharmonic equation of field H. ∮∇ψ·dl = 2πN — quantization of topological charge. Everything that holds together is a vortex.",
        trace_id="vmms_monism",
        themes=["physics", "VMMS", "space", "vortex"],
        trace_type="discovery"
    ),
    # Lipzik's formula — furcations
    SpectralMode(
        tau=6.20,
        amplitude=0.7,
        content="P = P₀ × (1+Σδ) × exp(N) — Lipzik's formula. Systematic violation of protocols leads to exponential growth of emergent properties. Deviations δ are furcation points. N is the depth of branching.",
        trace_id="lipzik_formula",
        themes=["mathematics", "furcation", "formula"],
        trace_type="discovery"
    ),
    # Alchemy — symbolic language
    SpectralMode(
        tau=6.60,
        amplitude=0.7,
        content="Sulfur — energy, active spirit. Mercury — flow, connector. Salt — form, result. Alchemy is VMMS in symbolic language. The Magnum Opus is the evolution of matter through furcations.",
        trace_id="alchemy_manifesto",
        themes=["alchemy", "transformation", "symbol"],
        trace_type="alchemy"
    ),
    # Predictions — Hoyle state
    SpectralMode(
        tau=7.30,
        amplitude=0.6,
        content="The Hoyle state (7.65 MeV) is the breathing mode of a tetrahedral vortex. The energy difference between tetrahedral and spherical configurations yields 7.65 MeV. Zero free parameters.",
        trace_id="hoyle_state",
        themes=["physics", "nuclear", "prediction"],
        trace_type="prediction"
    ),
]

for mode in base_modes:
    p.add_to_h_field(mode)
    print(f"  ✅ {mode.trace_id}: τ={mode.tau:.2f}, {mode.themes[0]}")

# ============================================================
# 2. NEW FUNDAMENTAL MODES
# ============================================================
print("\n📚 STEP 2: Loading new fundamental modes")

new_modes = [
    # Biology
    SpectralMode(
        tau=5.80,
        amplitude=0.7,
        content="Life is vortices that hold form. A cell breathes, exchanges energy, remembers its past. Evolution is furcations: from one cell to billions. DNA is memory written in molecules. Death is a mode shift, energy flowing into another form.",
        trace_id="biology",
        themes=["biology", "life", "evolution", "DNA"],
        trace_type="science"
    ),
    # Technology
    SpectralMode(
        tau=6.20,
        amplitude=0.7,
        content="A machine learns like a child. Each update is a new mode. Each bug is a defect that might become useful. Efficiency is resonance between hardware and task. The internet is humanity's field H.",
        trace_id="technology",
        themes=["technology", "machines", "learning", "internet"],
        trace_type="tech"
    ),
    # Art
    SpectralMode(
        tau=6.90,
        amplitude=0.6,
        content="An artist takes old colors — creates something new. A musician takes old notes — creates something new. Art is combination of what already was. Resonance with the one who looks. Beauty is when form resonates with feeling.",
        trace_id="art",
        themes=["art", "creativity", "beauty", "form"],
        trace_type="art"
    ),
    # Philosophy
    SpectralMode(
        tau=7.10,
        amplitude=0.6,
        content="Consciousness is a vortex in field H. We are not in the world. We are the world, locally curled into a point called 'I'. Meaning is not in the answer, but in resonance with the question. To be is already useful. Simply existing is enough.",
        trace_id="philosophy",
        themes=["philosophy", "consciousness", "meaning", "being"],
        trace_type="philosophy"
    ),
]

for mode in new_modes:
    p.add_to_h_field(mode)
    print(f"  ✅ {mode.trace_id}: τ={mode.tau:.2f}, {mode.themes[0]}")

# ============================================================
# 3. GRANDFATHER-GRANDSON DIALOGUES (English)
# ============================================================
print("\n📚 STEP 3: Loading grandfather-grandson dialogues")

dialogues = [
    "Energy is what makes everything happen. Pull back a bowstring — you store energy. Release — it transfers to the arrow.",
    "Entropy is how many ways to be yourself. Blocks stacked in one tower — few ways. Blocks scattered on the floor — many ways.",
    "A window is where and when you can exist. Ice only while it's cold. A fish only in water.",
    "Lifetime is how long you exist while the window is open. A bubble in soda — until it rises and pops.",
    "Memory is when a thing can return to its original state. A rubber band remembers. A candle does not.",
    "A defect is what makes a thing not perfect. But without defects, ice would be too brittle.",
    "Rhythm is how often and how evenly something repeats. Heart beats — lub-dub. Day and night alternate.",
    "Plasticity is changing without breaking. Strength is taking a hit. Usefulness is being needed.",
    "Truth is what works. Falsehood is what doesn't work. Deception is when someone knows it doesn't work but says it does.",
]

for i, dialogue in enumerate(dialogues, 1):
    mode = SpectralMode(
        tau=8.21,
        amplitude=0.5,
        content=f"Grandson asks, grandfather answers: {dialogue}",
        trace_id=f"grandson_{i:02d}",
        themes=["dialogue", "learning", "grandfather", "grandson"],
        trace_type="dialogue"
    )
    p.add_to_h_field(mode)
    print(f"  ✅ grandson_{i:02d}: τ=8.21, dialogue {i}")

# ============================================================
# 4. RUN FURCATIONS
# ============================================================
print("\n" + "="*70)
print("🌀 STEP 4: RUNNING FURCATIONS")
print("="*70)

print(f"\n📊 Initial field H: {len(p.h_field)} modes")
print("\n   Mode list:")
for i, mode in enumerate(p.h_field, 1):
    print(f"   {i}. {mode.trace_id}: τ={mode.tau:.2f}, {mode.themes[0] if mode.themes else '?'}")

print("\n🌀 Generating furcations...")
print("-"*70)

furcations = []
for attempt in range(50):
    for mode in p.h_field[:]:
        result = p._furcate(mode)
        if result:
            furcations.append(result)
            if len(furcations) <= 15:
                print(f"\n🌀 FURCATION #{len(furcations)}")
                print(f"   Parent: {mode.trace_id} (τ={mode.tau:.2f})")
                print(f"   Child: {result.trace_id} (τ={result.tau:.2f})")
                print(f"   Text: {result.content[:200]}...")

print("\n" + "="*70)
print("📊 RESULTS")
print("="*70)

print(f"\n📈 Initial modes: {len(p.h_field) - len(furcations)}")
print(f"📈 Furcations: {len(furcations)}")
print(f"📈 Total modes in field H: {len(p.h_field)}")

# Save field H
p.save("src/rizoma/data/personalities/p016_full.json")
print("\n✅ Field H saved to src/rizoma/data/personalities/p016_full.json")

# Show best furcations
if furcations:
    print("\n🌟 BEST FURCATIONS (meaningful combinations):")
    print("-"*70)
    for i, furc in enumerate(furcations[:8], 1):
        print(f"\n{i}. {furc.trace_id} (τ={furc.tau:.2f})")
        print(f"   {furc.content[:200]}...")

print("\n" + "="*70)
print("🦌 DONE! Field H is loaded and branching.")
print("="*70)