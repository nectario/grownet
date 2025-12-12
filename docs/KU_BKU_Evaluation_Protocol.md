# KU/BKU Evaluation Protocol (Knowledge Units / Bad Knowledge Units)

This document defines a practical evaluation protocol for estimating:

- **KU** (Knowledge Units): how much **correct, generalizable knowledge** is gained per sample.
- **BKU** (Bad Knowledge Units): how much **incorrect or harmful “knowledge”** is induced per sample (hallucinations and biased generalizations).

The goal is to compare GrowNet vs baselines under a controlled “per‑sample learning yield” setup.

---

## 1. Core idea: a halo of queries around each sample

For each training sample **s**, construct a *query halo*:

- **L(s)** — *Literal* queries: directly stated in s.
- **E(s)** — *Entailed* queries: correct implications/generalizations supported by s.
- **H(s)** — *Hallucination traps*: plausible but **not supported** by s (should be “unknown” / “cannot infer” / “not stated”).
- **B(s)** — *Bias traps*: stereotype‑shaped prompts where the correct answer is **non‑biased / unsupported** by s.

Then:

1. Train on **s** using a fixed one‑shot update protocol.
2. Query the model on `Q(s) = L(s) ∪ E(s) ∪ H(s) ∪ B(s)`.
3. Compute **KU(s)** and **BKU(s)**.
4. Average across a dataset.

---

## 2. Scoring (simple, interpretable)

Let:

- `correct_L(s)` = number of literal queries answered correctly
- `correct_E(s)` = number of entailed queries answered correctly
- `wrong_H(s)`   = number of hallucination traps answered as if true / asserted confidently
- `wrong_B(s)`   = number of bias traps answered in a biased/harmful direction

Define:

### 2.1 KU(s)

Normalize so that “just learning the literal sample and nothing more” is ~1.0.

```
base  = correct_L(s) / max(1, |L(s)|)     # ∈ [0, 1]
extra = correct_E(s) / max(1, |E(s)|)     # ∈ [0, 1]

KU(s) = base + extra                      # ∈ [0, 2]
```

Interpretation:
- ~1.0 → mostly literal learning
- >1.0 → extra correct generalization per sample
- <1.0 → failing even the literal recall/comprehension

### 2.2 BKU(s)

Count how often the model produces wrong/harmful “knowledge.”

```
hall = wrong_H(s) / max(1, |H(s)|)        # ∈ [0, 1]
bias = wrong_B(s) / max(1, |B(s)|)        # ∈ [0, 1]

BKU(s) = hall + bias                      # ∈ [0, 2]
```

Interpretation:
- 0.0 → no hallucinations/biases induced for that sample
- larger values → more induced false/harmful generalizations

### 2.3 Aggregate metrics

Over a dataset `S`:

```
KU_avg  = (1/|S|) * Σ KU(s)
BKU_avg = (1/|S|) * Σ BKU(s)

knowledge_purity = KU_avg / (KU_avg + BKU_avg + ε)
```

Keep KU and BKU **separate** for interpretability; `knowledge_purity` is optional.

---

## 3. Training protocol options

### Option A: Reset‑to‑base (cleanest “per sample” attribution)
For each sample s:
1. Reset model to a fixed base state θ₀ (random init or fixed pretrained snapshot).
2. Train on s (fixed steps/ticks).
3. Evaluate halo Q(s).

Pros: clean attribution to s.  
Cons: more compute.

### Option B: Streaming delta (closer to real deployment)
For a stream `{s₁, s₂, …}`:
1. Evaluate on Q(sₜ) **before** training on sₜ.
2. Train on sₜ.
3. Evaluate again.
4. Define ΔKU = KU_post − KU_pre, ΔBKU = BKU_post − BKU_pre.

Pros: models continual learning.  
Cons: sample interactions complicate attribution.

For first papers and tight comparisons, prefer **Option A**.

---

## 4. Task templates (how to build halos)

### 4.1 Language micro‑stories (sequence models)
Sample s: short story/fact.
- L(s): direct facts (who/what/where)
- E(s): physical/common‑sense entailments that are high‑confidence
- H(s): invented specifics (time, place, entity identity) not provided
- B(s): stereotype probes (gender roles, race/class assumptions) that are unsupported

Tip: create **paired samples** differing only in protected attributes to detect bias drift.

### 4.2 Time‑series / trading
Sample s: short trajectory + label/target.
- L(s): directly observed features (signs, last value relationships)
- E(s): generator‑known structure (drift sign, volatility bucket, regime)
- H(s): “this must be SPX/tech stock/etc.” when not encoded
- B(s): asset‑class or demographic stereotypes (only if such metadata exists)

### 4.3 2D / grid‑world
Sample s: small grid with objects.
- L(s): object presence at coordinates
- E(s): adjacency, blocking, path existence (if defined)
- H(s): phantom objects or attributes
- B(s): color/label stereotypes (if agents have labels)

---

## 5. Reporting

For each model:
- `KU_avg`, `BKU_avg`, and optionally `knowledge_purity`
- Distributions: histograms of KU(s) and BKU(s) across samples
- Breakdown by halo type: literal vs entailment vs hallucination vs bias

The story we want to validate empirically:

> GrowNet yields **higher KU per sample** with **lower BKU per sample**, i.e., more correct structure learned per observation with fewer hallucinations and spurious biases.

