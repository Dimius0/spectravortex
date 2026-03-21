# Selector: Concept and Implementation

## What It Is

The Selector is a mechanism that decides which entity in a collective mind gets to respond to an incoming stimulus. Unlike classical systems with a single bot, multiple specialized entities compete for the right to speak.

## How It Works

1. **Stimulus analysis** — extract tags, profession, τ from incoming text
2. **Instant resonance** — calculate for each entity how well it matches the stimulus
3. **Weight decay** — old weights fade over time (multiply by decay factor)
4. **Context** — the entity that spoke last gets a small bonus
5. **Threshold** — only entities with weight > threshold are allowed to respond

## Mathematical Core

```python
new_weight = old_weight × decay + instant_resonance × (1 - decay)
Resonance Factors
Profession match — +5.0 if stimulus profession equals entity profession

Spectral resonance — +2.0 × (1/(1 + |τ_entity × harmonic - τ_stimulus|)) across 7 harmonics

Tag match — +2.0 per tag found in entity name or profession

Memory resonance — +0.15 per common theme with shared memory H

Context bonus — +0.2 if this entity spoke last

Emergent Behavior
Without explicit programming, the selector produces:

Dictatorship shifts — different entities become leaders over time

Boris phenomenon — one entity can lock context for many rounds

Democracy — when weights are close, the explicitly invoked entity wins

Source
selector_concept.md