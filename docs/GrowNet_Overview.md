# GrowNet Overview

## Plain Language Summary
GrowNet is an AI research project exploring a neuron-centric alternative to classic artificial neural networks. Rather than a single weight and bias, each neuron maintains a set of "slots" that specialise for different input patterns. Learning happens locally and event-by-event, allowing the network to grow new slots, neurons, or layers as the data distribution shifts. The implementations aim to mirror each other across Python, Java, C++ and Mojo so researchers can experiment in whichever language they prefer.

## Technical Overview
* **Region orchestration.** The `Region` object manages layers, port bindings and tick-based execution, exposing helpers for scalar and image inputs as well as deterministic windowed wiring for spatial focus【F:src/python/region.py†L1-L60】【F:src/cpp/Region.h†L1-L90】
* **Neuron model.** Each neuron owns a slot map and uses a `SlotEngine` to select or create the active slot based on anchor-relative percent change. Reinforcement and threshold updates determine whether the neuron fires【F:src/python/neuron.py†L1-L107】【F:src/mojo/neuron.mojo†L1-L62】
* **Growth mechanics.** Java provides the semantic reference for growth heuristics, adding layers when average slots per neuron exceeds a threshold and marking outlier neurons for potential expansion【F:src/java/ai/nektron/grownet/growth/GrowthEngine.java†L18-L56】【F:src/java/ai/nektron/grownet/growth/GrowthEngine.java†L58-L103】
* **Cross-language parity.** The repository is designed as a cross-language reference with aligned public APIs and neuron types across Python, C++, Mojo and Java【F:docs/What_this_codebase_is_about.md†L3-L6】

## Vision and Goals
GrowNet aims to build a biologically inspired, event-driven neural fabric where temporal and spatial focus guide growth. Each neuron keeps a focus anchor; large anchor-relative deltas can trigger the creation of new slots, sibling neurons or layers, enabling capacity to expand as needed【F:docs/CONTEXT_GrowNet_Vision.md†L1-L22】

The research pursues three testable goals:
1. Achieve 80% of ProtoNet accuracy on Omniglot using no more than 10% of its labelled shots.
2. Limit accuracy drop to 5% on corrupted CIFAR-10 with 30% noise injection.
3. Reduce inference energy to below 30% of baseline on event-driven hardware【F:docs/GrowNet_Theory_of_Change.md†L18-L27】


This research work is aimed at being presented at NeurIPS.
