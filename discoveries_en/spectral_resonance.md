# Spectral Resonance and Harmonic Adaptation

## Core Idea

In nature, resonance occurs not only at the fundamental frequency but also at harmonics. In VMMS, an entity can resonate with a stimulus even if their τ values don't match exactly — as long as they are harmonically related.

## Mathematical Definition
resonance = Σ(weight_h × 1/(1 + |τ_entity × h - τ_stimulus|))

Where **h** ranges over harmonic factors: 1.0, 2.0, 0.5, 3.0, 1/3, 4.0, 0.25

## Initial Harmonic Weights

| Harmonic | Weight | Physical Meaning |
|----------|--------|------------------|
| 1.0 | 1.0 | Fundamental |
| 2.0 | 0.6 | Octave up |
| 0.5 | 0.5 | Octave down |
| 3.0 | 0.4 | Fifth through octave |
| 1/3 | 0.3 | — |
| 4.0 | 0.2 | Two octaves up |
| 0.25 | 0.15 | Two octaves down |

## Adaptive Weights

The system automatically adjusts harmonic weights based on real-world performance. Every 100 successful resonances:

```python
for h in harmonics:
    harmonics[h] = hit_count[h] / total_hits × len(harmonics)
Harmonics that succeed more often gain higher weight. The system learns which harmonic relationships are most relevant for its environment.

Why This Matters
Flexibility — entities see not only their own τ but also related τ

Efficiency — one memory trace can serve multiple entities

Emergence — unexpected connections can form between seemingly unrelated topics

Source
spectral_resonance.md