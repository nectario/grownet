# GrowNet — Core Messaging

**Tagline:** Adaptive neural networks that *grow* when the data changes.

**One‑liner:** GrowNet is a research project proposing a growth‑capable neural architecture that allocates new representational capacity under distributional novelty—so models adapt by **growing** instead of endlessly fine‑tuning.

**Elevator (90s):**
Most deep nets are static: we keep tweaking the same parameters as data drifts. GrowNet takes a different path. When incoming data looks meaningfully new, GrowNet allocates capacity—new slots, layers, or regions—guided by a principled rule: *grow if (and only if) specialization’s expected utility beats adaptation within current parameters*. The goal is a system that scales structure with experience, like biological learning.

**Golden Rule (formal):**
*A learning system should allocate new representational capacity if—and only if—the expected marginal utility of specialization under distributional novelty exceeds that of adaptation within existing parameters.*

**Key Messages (pick 5–7):**
1) **Growth on novelty:** Detects distributional novelty and allocates capacity at the right granularity (slot → layer → region).
2) **Principled trigger:** Growth is governed by an explicit utility comparison, not ad‑hoc heuristics.
3) **Continual learning:** Reduces catastrophic forgetting by specializing instead of over‑writing.
4) **Modular structure:** New capacity is labeled and measurable; metrics track usefulness and pruning.
5) **Transparent evolution:** Every growth event is logged; you can trace *why* the model changed.
6) **General approach:** Works conceptually across modalities—language, vision, time series, control.
7) **Open work-in-progress:** Code and docs are public; experiments and ablations are being added.

**Boilerplate (short):**
GrowNet explores growth‑capable neural architectures that expand structure in response to distributional novelty. The project aims to make continual learning practical by allocating new capacity when specialization is more useful than further adaptation. Code and docs: https://github.com/nectario/grownet

**FAQ (short):**
- **Is this another mixture‑of‑experts?** Related in spirit (specialization), but GrowNet emphasizes **structural growth events** governed by a decision rule, not just routing across a fixed pool.
- **Does it prune?** Yes—capacity that underperforms can be flagged for merge or prune.
- **What’s the status?** Active research. Public repo; milestones include MNIST-style benchmarks, Morse code detection, and ablations on growth criteria.
- **Why not just fine‑tune?** Because drift + heterogeneity often benefit from *specialized structure* rather than reusing the same parameters for everything.
- **Where to learn more?** Read the overview docs in the repo and follow issue threads for experiments.
