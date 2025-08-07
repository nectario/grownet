# NektronAI GrowNet · Learning‑First, Grow‑as‑You‑Go Network

## 1. Guiding Intuition
Biological neurons do not converge all synapses into a single scalar; instead they integrate signals at multiple dendritic micro‑sites.  
GrowNet abstracts each neuron as an **elastic array of sub‑slots (“vector slots”)** whose count expands whenever novel input statistics appear.  
Learning is continuous, local, and memory is encoded **inside** the neuron (threshold surfaces + reinforced weights), not in an external optimiser state.

## 2. Core Mechanisms
| Aspect | Classic ANN | GrowNet Mechanism | Expected Advantage |
| ------ | ----------- | ----------------- | ------------------ |
| **Internal state** | Scalar weight per input | Elastic **vector / matrix** per neuron; each slot represents a 10 % Δ‑bin (or adaptive bin) in successive inputs | Higher expressivity per neuron, natural handling of distribution drift |
| **Firing rule** | Weighted sum > bias | Slot‑specific threshold; neuron fires when any slot’s cumulative activation > θ | Event‑driven, sparse compute |
| **Memory** | Stored in weights | Stored in thresholds **and** slot histories | Long‑term trace without back‑prop |
| **Weight update** | Gradient step | Non‑linear reinforcement → w ← min(w + α·f(hit_count), wₘₐₓ) | Few‑shot strengthening; energy‑efficient |
| **Growth** | Fixed width | Add slot (or new neuron) when OOD score > τ (Mahalanobis, cosine, etc.) | Progressive capacity; avoids over‑parameterisation |
| **Attention** | Softmax over channels | Intrinsic: neuron attends to highest local energy in its receptive field | Built‑in saliency without extra params |

## 3. Testable Predictions
1. **Sample efficiency**: 80 % of ProtoNet accuracy on Omniglot with ≤10 % of its labelled shots.  
2. **OOD robustness**: ≤5 % accuracy drop on corrupted CIFAR‑10 after 30 % noise injection (vs ≥15 % for CNN).  
3. **Energy**: <30 % of baseline energy per inference on event‑driven hardware trace.

## 4. Prototype Scope (E‑00)
**Dataset**: Omniglot 5‑way × 5‑shot  
**Metric**: Acc@5 vs #labels, params, energy (J/ex)  
**Hardware**: ▢ *RTX 4090 acceptable?*  
**Success criterion**: Hit prediction #1.

## 5. Risks & Unknowns
* Growth rule stability (slot explosion).  
* VRAM profile as matrix slots proliferate.  
* Mojo tooling maturity for GPU kernels.  
