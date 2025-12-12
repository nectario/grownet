Love this. Here’s a battle-tested way to use my “deep research” mode so we (a) find the work closest to GrowNet, (b) credit people correctly, and (c) clearly show what’s novel about yours.

------

## How to use me for deep research (simple playbook)

### 1) Lock the comparison axes (what I’ll match against)

Unless you override, I’ll use these GrowNet invariants as the “signature”:

- Local learning (no backprop end-to-end)
- Rule-based growth with **novelty ⇒ capacity** (Slots→Neurons→Layers→Regions)
- **Determinism**: recorded mesh rules, reproducible RNG, ordered PAL reductions
- **Bounded growth**: cooldowns; ≤1 growth per region per tick
- 2D **windowed wiring** with SAME/VALID **center rule** & **unique-source** return
- Freeze/unfreeze (prefer-last-slot-once)

> If you want to tweak the axes (e.g., add “energy/cost per joule”), tell me and I’ll include them.

### 2) I run a structured, citation-tracked sweep

I’ll use web search with scholarly bias and do **backward/forward snowballing**. Families I’ll definitely check:

- **Constructive / growing nets**: Growing Neural Gas (Fritzke), Cascade-Correlation (Fahlman & Lebiere), Dynamic/Constructive NN surveys
- **Self-organizing**: Kohonen SOM; related incremental maps (e.g., SOINN)
- **ART family** (Grossberg/Carpenter): category growth under novelty
- **Topology evolution / neuroevolution**: NEAT & descendants (node/edge addition)
- **Dynamic capacity/structure**: progressive nets, grow-and-prune, dynamic routing, network morphism
- **Memory vs capacity**: DNC, Neural Turing Machines (contrast with GrowNet’s capacity growth)
- **Bio & plasticity**: algorithmic neurogenesis papers and structural plasticity in ANNs
- **HTM / SDR** (Hawkins): local learning & sparsity (contrast on growth & determinism)

I’ll use multiple query shards (synonyms) so we don’t miss near-matches:

- “constructive neural network”, “growing neural gas”, “incremental structure learning”, “neural net **adds neuron**”, “layer growth rule”, “neurogenesis **artificial**”, “dynamic architecture search”, “network morphism”, “progressive neural network”, “grow-and-prune”, “adaptive resonance theory”

### 3) Deliverables you’ll get (all in Markdown you can paste into your paper/repo)

- **Positioning Matrix** (✓/✗/~) across the axes above, with **one-liner deltas** per work
- **Related-Work draft** (2–3 tight paragraphs) you can drop into NeurIPS format
- **Mini-abstracts** (3–5 bullets each) + the **direct quote** that is closest to GrowNet’s idea (with citation)
- **BibTeX** file for all items
- A short **Risk Notes** section (“these 2 are closest; cite prominently; wording to use”)

If you prefer, I can also add a **timeline** figure (who did what first) and a short **attribution policy** paragraph.

### 4) How to kick it off (lowest-effort from you)

Just say:

> **“Start with defaults. Focus on constructive/growing networks, ART/SOM, neuroevolution, progressive nets, grow-and-prune, and dynamic routing. Include dynamic memory (DNC/NTM) only as a contrast. Output: matrix + related-work draft + BibTeX.”**

Optional knobs you can add:

- **Cutoff** (e.g., include pre-2000 classics, emphasize 2015–2025)
- **Venue weight** (e.g., NeurIPS/ICLR/ICML/JMLR first)
- **Patent sweep** (yes/no)
- **Depth** (top-20 vs top-40 items)

### 5) What I’ll do under the hood (so it’s reproducible)

- Run targeted queries with date/venue filters; keep a **query log** (you’ll get it)
- Pull **primary sources** (papers/pdfs) and **official docs** first; avoid blog summaries for claims
- For each candidate: extract claims, growth mechanism, determinism, learning rule, 2D wiring semantics, and cite exact lines
- Perform **snowballing** (look at who they cite and who cites them) to catch near-misses
- Compile the **matrix + draft** with inline citations you can click

> You’ll see **citations on the 5 most load-bearing statements** per web.run rules. I won’t hide sources.

------

## Example of the output you’ll receive (condensed)

**Positioning Matrix (excerpt)**

| Work                       | Local (no backprop) | Growth trigger       | Hierarchy (slot→neuron→layer) | Deterministic wiring | Cooldowns / 1-growth/tick | 2D unique-source | Notes                                                        |
| -------------------------- | ------------------- | -------------------- | ----------------------------- | -------------------- | ------------------------- | ---------------- | ------------------------------------------------------------ |
| Growing Neural Gas (1995)  | ✓                   | quantization error   | node-only                     | ~ (heuristic)        | ✗                         | ✗                | Adds units; not hierarchical; not recorded mesh rules        |
| ART/ARTMAP                 | ✓                   | mismatch / vigilance | category nodes                | ✓ (rule-based)       | ~                         | ✗                | Closest philosophically; lacks explicit multi-rung growth & PAL determinism |
| Cascade-Correlation (1990) | ✗ (uses gradients)  | residual/error       | neuron (hidden)               | ✗                    | ✗                         | ✗                | Adds hidden units via gradient signal                        |
| Progressive Nets (2016)    | ✗                   | new task             | column/layer                  | ~                    | ✗                         | ✗                | Adds columns per task, not per novelty at tick-time          |
| Grow-and-Prune (2018)      | ✗                   | saliency/regularizer | prune/grow weights            | ✗                    | ✗                         | ✗                | Weight-level structure, not rule-based capacity              |

**Related Work draft (excerpt)**

> Our approach sits at the intersection of constructive/growing neural networks and self-organizing methods. Classical constructive models such as Cascade-Correlation and Growing Neural Gas increase capacity under error/quantization-based signals, but they do not provide a deterministic, rule-based hierarchy that escalates from slots to neurons to layers with explicit cooldowns and recorded mesh rules. ART/ARTMAP is philosophically closest in using novelty/vigilance to allocate categories; GrowNet generalizes this by formalizing growth at multiple rungs (slot→neuron→layer) within a two-phase tick and PAL-deterministic wiring regime, and by adding 2D windowed wiring with unique-source semantics… *(citations go here)*

------

## Ready to go?

If you reply with **“Start with defaults”**, I’ll begin the sweep **right here in this thread** and deliver:

1. Positioning Matrix
2. Related-Work draft (NeurIPS-ready)
3. BibTeX

If you want to add knobs (e.g., “include patents” or “limit to 2010–2025”), include that in your “Start” message.