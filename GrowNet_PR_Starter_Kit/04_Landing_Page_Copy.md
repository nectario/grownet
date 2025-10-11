# GrowNet — A Neural Network That Grows

**Hero H1:** Models that evolve with the world.  
**Subhead:** GrowNet allocates new capacity when data is *meaningfully new*, following a principled Golden Rule.

**Primary CTA:** ★ Star the repo · https://github.com/nectario/grownet  
**Secondary CTA:** Read the overview → `/docs/GrowNet_Overview.md`

## Why Grow?
Data drifts. Heterogeneity expands. Fine‑tuning a static model forever is brittle. GrowNet specializes **only when it pays off**, so the model’s structure keeps up with reality.

## How It Works (short)
1. **Detect novelty** in the incoming distribution.
2. **Estimate utility** of specialization vs. adapting existing parameters.
3. **Grow** (slot/layer/region) iff specialization wins.
4. **Measure & prune**: track the utility of new capacity; merge or prune if needed.

## Roadmap (live checklist)
- [ ] Baseline tasks (MNIST‑style)
- [ ] Morse‑code detection (signal novelty)
- [ ] Growth threshold ablations
- [ ] Pruning/merging policies
- [ ] Multi‑modal prototype

## Get Involved
- Open issues labeled **good first issue**
- Join discussions in **/docs** and **/issues**
- Share feedback or experiments
