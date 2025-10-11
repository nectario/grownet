# Show HN Draft

**Title:** Show HN: GrowNet — a neural network that grows when the data is novel

**Body (concise):**
We’re exploring a growth‑capable neural architecture for continual learning. When the incoming data looks meaningfully new, GrowNet **allocates new capacity** (slot/layer/region) if a formal utility test says specialization will outperform further adaptation inside the current parameters. Growth events are logged and measurable; underperforming capacity can be merged or pruned. Code + docs: https://github.com/nectario/grownet. Feedback and skeptical questions welcome.

**Comment Prompts:**
- Where would growth help (or hurt) in your workloads?
- Best benchmarks for controlled distribution shift?
- How would you measure “utility of specialization” in your domain?
