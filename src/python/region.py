# region.py — Python Region implementation (clean, parity-focused)
from typing import List, Dict, Any
import random
from metrics import RegionMetrics
from typing import List, Dict, Any, Callable, SupportsInt, cast

# Layer and shape-aware layers are imported lazily to avoid import cycles.


class Region:
    """Orchestrates layers, port bindings, and ticks.

    Ports are modeled as edge layers. A tick drives the bound edge exactly once;
    downstream layers receive activity via wiring from that edge.
    """
    class PruneSummary:
        def __init__(self):
            self.prunedSynapses = 0
            self.prunedEdges = 0  # reserved

    def __init__(self, name: str):
        self.name: str = name
        self.layers: List[Any] = []          # Any to keep static analyzers calm
        self.input_ports: Dict[str, List[int]] = {}
        self.output_ports: Dict[str, List[int]] = {}

        # Edge layers per port (created lazily on bind)
        self.input_edges: Dict[str, int] = {}
        self.output_edges: Dict[str, int] = {}

        # Region-scope bus (optional; some codebases keep only per-layer buses)
        self.bus = None
        self.rng = random.Random(1234)
        # Optional flag to compute spatial metrics in tick_2d (also gated by env var)
        self.enable_spatial_metrics = False

    # ---------------- construction ----------------
    def add_layer(self, excitatory_count: int, inhibitory_count: int, modulatory_count: int) -> int:
        from layer import Layer
        layer = Layer(excitatory_count, inhibitory_count, modulatory_count)
        self.layers.append(layer)
        return len(self.layers) - 1

    def add_input_layer_2d(self, height: int, width: int, gain: float, epsilon_fire: float) -> int:
        from input_layer_2d import InputLayer2D
        layer = InputLayer2D(height, width, gain, epsilon_fire)
        self.layers.append(layer)
        return len(self.layers) - 1

    
    def add_input_layer_nd(self, shape: list[int], gain: float, epsilon_fire: float) -> int:
        from input_layer_nd import InputLayerND
        layer = InputLayerND(shape, gain, epsilon_fire)
        self.layers.append(layer)
        return len(self.layers) - 1


    def add_output_layer_2d(self, height: int, width: int, smoothing: float) -> int:
        from output_layer_2d import OutputLayer2D
        layer = OutputLayer2D(height, width, smoothing)
        self.layers.append(layer)
        return len(self.layers) - 1

    # ---------------- wiring ----------------
    def connect_layers(self, source_index: int, dest_index: int, probability: float, feedback: bool = False) -> int:
        """Create random synapses from every neuron in `source_index` to neurons in `dest_index`.
        Returns the number of edges created (edge count parity with Java/C++)."""
        if source_index < 0 or source_index >= len(self.layers):
            raise IndexError(f"source_index out of range: {source_index}")
        if dest_index < 0 or dest_index >= len(self.layers):
            raise IndexError(f"dest_index out of range: {dest_index}")
        prob = max(0.0, min(1.0, float(probability)))
        src_layer = self.layers[source_index]
        dst_layer = self.layers[dest_index]
        count = 0

        # Layer exposes get_neurons(); neurons expose connect(target, feedback=False)
        for src_neuron in getattr(src_layer, "get_neurons")():
            for dst_neuron in getattr(dst_layer, "get_neurons")():
                if self.rng.random() <= prob:
                    try:
                        src_neuron.connect(dst_neuron, feedback=feedback)
                    except TypeError:
                        src_neuron.connect(dst_neuron)
                    count += 1
        return count

    def connect_layers_windowed(self,
                                src_index: int,
                                dest_index: int,
                                kernel_h: int,
                                kernel_w: int,
                                stride_h: int = 1,
                                stride_w: int = 1,
                                padding: str = "valid",
                                feedback: bool = False) -> int:
        """Wire src(2D) → dst using sliding windows (deterministic).

        - If dst is OutputLayer2D: each window sends all its source pixels to the
          output neuron at the window's center.
        - Otherwise: allowed source pixels are connected via a Tract that forwards
          events to dst.propagate_from_2d, which then fans to dst neurons.
        Returns number of hook wires created (deterministic count).
        """
        from input_layer_2d import InputLayer2D
        from output_layer_2d import OutputLayer2D
        if src_index < 0 or src_index >= len(self.layers):
            raise IndexError("src_index out of range")
        if dest_index < 0 or dest_index >= len(self.layers):
            raise IndexError("dest_index out of range")

        src_layer = self.layers[src_index]
        dst_layer = self.layers[dest_index]
        if not isinstance(src_layer, InputLayer2D):
            raise ValueError("connect_layers_windowed requires src to be InputLayer2D")

        H, W = int(getattr(src_layer, "height", 0)), int(getattr(src_layer, "width", 0))
        kh, kw = int(kernel_h), int(kernel_w)
        sh, sw = max(1, int(stride_h)), max(1, int(stride_w))
        pad = str(padding or "valid").lower()

        # Determine window origins (top-left) for 'valid' (no padding) or 'same' (approximate center pad)
        origins = []
        if pad == "same":
            pr = max(0, (kh - 1) // 2)
            pc = max(0, (kw - 1) // 2)
            r0 = -pr
            c0 = -pc
            r = r0
            while r + kh <= H + pr + pr:
                c = c0
                while c + kw <= W + pc + pc:
                    origins.append((r, c))
                    c += sw
                r += sh
        else:
            r = 0
            while r + kh <= H:
                c = 0
                while c + kw <= W:
                    origins.append((r, c))
                    c += sw
                r += sh

        # Compute allowed source indices and (optionally) sink map for OutputLayer2D
        allowed: set[int] = set()
        sink_map: dict[int, set[int]] = {}
        # We'll return the number of unique source subscriptions installed.
        wires = 0

        if isinstance(dst_layer, OutputLayer2D):
            for (r0, c0) in origins:
                # window clamp to valid coordinates
                rr0, cc0 = max(0, r0), max(0, c0)
                rr1, cc1 = min(H, r0 + kh), min(W, c0 + kw)
                if rr0 >= rr1 or cc0 >= cc1:
                    continue
                # center index (integer floor)
                cr = min(H - 1, max(0, r0 + kh // 2))
                cc = min(W - 1, max(0, c0 + kw // 2))
                center_idx = cr * W + cc
                for rr in range(rr0, rr1):
                    for cc2 in range(cc0, cc1):
                        src_idx = rr * W + cc2
                        allowed.add(src_idx)
                        sink_map.setdefault(src_idx, set()).add(center_idx)
            # Create a tract that delivers directly to mapped output neurons
            from tract import Tract
            Tract(src_layer, dst_layer, self.bus, feedback, None,
                  allowed_source_indices=allowed, sink_map=sink_map)
            wires = len(allowed)
        else:
            # For generic layers, allow all pixels that participate in any window;
            # destination layer will fan to its neurons with 2D context.
            for (r0, c0) in origins:
                rr0, cc0 = max(0, r0), max(0, c0)
                rr1, cc1 = min(H, r0 + kh), min(W, c0 + kw)
                if rr0 >= rr1 or cc0 >= cc1:
                    continue
                for rr in range(rr0, rr1):
                    for cc2 in range(cc0, cc1):
                        allowed.add(rr * W + cc2)
            from tract import Tract
            Tract(src_layer, dst_layer, self.bus, feedback, None,
                  allowed_source_indices=allowed)
            wires = len(allowed)

        return wires

    # ---------------- edge helpers ----------------
    def ensure_input_edge(self, port: str) -> int:
        """Ensure an Input edge layer exists for this port; create lazily."""
        idx = self.input_edges.get(port)
        if idx is not None:
            return idx

        # Minimal scalar input edge: a 1-neuron layer that forwards to internal graph.
        edge_idx = self.add_layer(1, 0, 0)
        self.input_edges[port] = edge_idx
        return edge_idx

    def ensure_output_edge(self, port: str) -> int:
        """Ensure an Output edge layer exists for this port; create lazily."""
        idx = self.output_edges.get(port)
        if idx is not None:
            return idx

        # Minimal scalar output edge: a 1-neuron layer acting as a sink.
        edge_idx = self.add_layer(1, 0, 0)
        self.output_edges[port] = edge_idx
        return edge_idx

    def bind_input(self, port: str, layer_indices: List[int]) -> None:
        """Bind a scalar input port to one or more layers (edge-only delivery).

        If any target is an InputLayer2D, treat it as the port's edge and wire
        it forward to the remaining targets (convenience path).
        """
        self.input_ports[port] = list(layer_indices)

        # Convenience: if user passes a shape-aware input layer as a bound target,
        # treat that layer as the edge for this port and wire it forward.
        try:
            from input_layer_2d import InputLayer2D  # type: ignore
        except Exception:
            InputLayer2D = None  # type: ignore

        edge_idx = None
        if layer_indices and InputLayer2D is not None:
            for layer_index in layer_indices:
                layer_obj = self.layers[layer_index]
                if isinstance(layer_obj, InputLayer2D):
                    edge_idx = layer_index
                    break
        if edge_idx is not None:
            self.input_edges[port] = edge_idx

            # Wire edge to any other attached layers (excluding itself)
            for layer_index in layer_indices:
                if layer_index != edge_idx:
                    self.connect_layers(edge_idx, layer_index, 1.0, False)
        else:

            # Scalar edge layer path
            in_edge = self.ensure_input_edge(port)
            for layer_index in layer_indices:
                self.connect_layers(in_edge, layer_index, 1.0, False)

    def bind_input_2d(self, port: str, height: int, width: int, gain: float, epsilon_fire: float, attach_layers: List[int]) -> None:
        from input_layer_2d import InputLayer2D

        # create or reuse edge
        edge_idx = self.input_edges.get(port)
        if edge_idx is None or not isinstance(self.layers[edge_idx], InputLayer2D):
            edge_idx = self.add_input_layer_2d(height, width, gain, epsilon_fire)
            self.input_edges[port] = edge_idx

        # wire edge → attached layers
        for layer_index in attach_layers:
            self.connect_layers(edge_idx, layer_index, 1.0, False)


    def bind_output(self, port: str, layer_indices: List[int]) -> None:
        self.output_ports[port] = list(layer_indices)
        out_edge = self.ensure_output_edge(port)

        for layer_index in layer_indices:
            self.connect_layers(layer_index, out_edge, 1.0, False)

    
    def bind_input_nd(self, port: str, shape: list[int], gain: float, epsilon_fire: float, layer_indices: list[int]) -> None:
        idx = self.input_edges.get(port)
        need_new = True
        if idx is not None:
            layer_obj = self.layers[idx]
            if hasattr(layer_obj, "has_shape") and layer_obj.has_shape(shape):
                need_new = False
        if idx is None or need_new:
            edge_idx = self.add_input_layer_nd(shape, gain, epsilon_fire)
            self.input_edges[port] = edge_idx
            idx = edge_idx
        self.input_ports[port] = list(layer_indices)
        for layer_index in layer_indices:
            self.connect_layers(idx, layer_index, 1.0, False)


    # ---------------- pulses ----------------
    def pulse_inhibition(self, factor: float) -> None:
        """Raise inhibition for the next tick (ephemeral)."""
        try:
            if self.bus is not None and hasattr(self.bus, "inhibition_factor"):
                self.bus.inhibition_factor = factor
        except Exception:
            pass
        for layer in self.layers:
            try:
                if hasattr(layer, "bus") and layer.bus is not None:
                    layer.bus.inhibition_factor = factor
            except Exception:
                pass

    def pulse_modulation(self, factor: float) -> None:
        """Scale modulation for the next tick (ephemeral)."""
        try:
            if self.bus is not None and hasattr(self.bus, "modulation_factor"):
                self.bus.modulation_factor = factor
        except Exception:
            pass
        for layer in self.layers:
            try:
                if hasattr(layer, "bus") and layer.bus is not None:
                    layer.bus.modulation_factor = factor
            except Exception:
                pass

    # ---------------- ticks ----------------
    def tick(self, port: str, value: float) -> RegionMetrics:
        """Drive a scalar into the edge bound to `port`; return per-tick metrics."""
        metrics = RegionMetrics()

        edge_idx = self.input_edges.get(port)
        if edge_idx is None:
            raise KeyError(f"No InputEdge for port '{port}'. Call bind_input(...) first.")

        self.layers[edge_idx].forward(value)

        # Default accounting: one event per port
        metrics.inc_delivered_events(1)

        # Optional compatibility shim for tests that count bound layers
        try:
            import os
            bound = self.input_ports.get(port, [])
            if os.environ.get("GROWNET_COMPAT_DELIVERED_COUNT") == "bound":
                delivered = max(1, len(bound))
                metrics.set_deliveredEvents(delivered)
        except Exception:
            pass

        for layer in self.layers:
            layer.end_tick()

        if self.bus is not None and hasattr(self.bus, "decay"):
            self.bus.decay()

        for layer in self.layers:
            for neuron in getattr(layer, "get_neurons")():
                slots_map = getattr(neuron, "slots", None)
                metrics.add_slots(len(slots_map) if isinstance(slots_map, dict) else 0)
                outgoing = neuron.get_outgoing() if hasattr(neuron, "get_outgoing") else []
                metrics.add_synapses(len(outgoing))

        return metrics


    
    def tick_2d(self, port: str, frame) -> RegionMetrics:
        """Drive a 2D frame into an InputLayer2D edge bound to `port`."""
        metrics = RegionMetrics()
        edge_idx = self.input_edges.get(port)
        if edge_idx is None:
            raise ValueError(f"No InputEdge for port '{port}'. Call bind_input_2d(...) first.")
        layer = self.layers[edge_idx]
        if hasattr(layer, "forward_image"):
            layer.forward_image(frame)
        else:
            raise ValueError(f"InputEdge for '{port}' is not 2D (expected InputLayer2D).")
        metrics.inc_delivered_events(1)

        # Optional compatibility shim for tests that count bound layers
        try:
            import os
            bound = self.input_ports.get(port, [])
            if os.environ.get("GROWNET_COMPAT_DELIVERED_COUNT") == "bound":
                delivered = max(1, len(bound))
                metrics.set_deliveredEvents(delivered)
        except Exception:
            pass
        for layer_obj in self.layers:
            layer_obj.end_tick()
        try:
            if self.bus is not None and hasattr(self.bus, "decay"):
                self.bus.decay()
        except Exception:
            pass
        for layer_obj in self.layers:
            for neuron in getattr(layer_obj, "get_neurons")():
                slots_map = getattr(neuron, "slots", None)
                metrics.add_slots(len(slots_map) if isinstance(slots_map, dict) else 0)
                outgoing = neuron.get_outgoing() if hasattr(neuron, "get_outgoing") else []
                metrics.add_synapses(len(outgoing))

        # Optional spatial metrics
        try:
            import os
            if self.enable_spatial_metrics or os.environ.get("GROWNET_ENABLE_SPATIAL_METRICS") == "1":
                self.compute_spatial_metrics(metrics, frame)
        except Exception:
            pass

        return metrics


    def tick_image(self, port: str, frame) -> RegionMetrics:
        return self.tick_2d(port, frame)

    
    def prune(
        self,
        synapse_stale_window: int = 10000,
        synapse_min_strength: float = 0.05) -> 'Region.PruneSummary':
        """Prune weak/stale synapses via per-neuron hooks; returns a small summary."""

        prune_summary = Region.PruneSummary()

        # A prune function takes (int, float) and returns something int()-convertible.
        PruneFn = Callable[[int, float], SupportsInt]

        for layer in self.layers:
            for neuron in getattr(layer, "get_neurons")():
                fn = getattr(neuron, "prune_synapses", None) or getattr(neuron, "pruneSynapses", None)
                if callable(fn):
                    prune_fn = cast(PruneFn, fn)
                    try:
                        result = prune_fn(synapse_stale_window, synapse_min_strength)
                    except Exception:
                        result = 0  # defensive default if an impl raises
                    try:
                        prune_summary.prunedSynapses += int(result)
                    except (TypeError, ValueError):

                        # If an implementation returns a non-numeric/None, ignore it.
                        pass
        return prune_summary

    # ---------------- accessors ----------------
    def get_name(self) -> str:
        return self.name

    def get_layers(self) -> List[Any]:
        return self.layers

    def get_bus(self):
        return self.bus

    # ---------------- internal helpers ----------------
    def compute_spatial_metrics(self, metrics: RegionMetrics, input_frame) -> None:
        """Compute activePixels, centroid, and bbox from the best available 2D layer.

        Prefer the furthest downstream OutputLayer2D frame this tick; if no non-zero
        output is found, fall back to the input frame passed to tick_2d.
        """
        from output_layer_2d import OutputLayer2D

        chosen = None
        # pick last OutputLayer2D (furthest downstream by index)
        for layer in reversed(self.layers):
            if isinstance(layer, OutputLayer2D):
                try:
                    fr = layer.get_frame()
                    chosen = fr
                    break
                except Exception:
                    continue

        if chosen is None:
            chosen = input_frame

        # If chosen is entirely zeros, but input has non-zeros, prefer input
        def is_all_zero(img):
            try:
                for row in img:
                    for v in row:
                        if float(v) != 0.0:
                            return False
                return True
            except Exception:
                return True

        if chosen is not input_frame and is_all_zero(chosen) and not is_all_zero(input_frame):
            chosen = input_frame

        # Compute metrics
        total = 0.0
        sum_r = 0.0
        sum_c = 0.0
        rmin, rmax, cmin, cmax = 10**9, -1, 10**9, -1
        H = len(chosen) if chosen is not None else 0
        W = len(chosen[0]) if H > 0 else 0

        for r in range(H):
            row = chosen[r]
            for c in range(min(W, len(row))):
                v = float(row[c])
                if v > 0.0:
                    total += v
                    sum_r += r * v
                    sum_c += c * v
                    if r < rmin: rmin = r
                    if r > rmax: rmax = r
                    if c < cmin: cmin = c
                    if c > cmax: cmax = c

        active = 0
        if H > 0 and W > 0:
            # count active pixels (value > 0.0)
            active = sum(1 for r in range(H) for c in range(W) if float(chosen[r][c]) > 0.0)

        metrics.active_pixels = active
        metrics.activePixels = active
        if total > 0.0:
            metrics.centroid_row = sum_r / total
            metrics.centroid_col = sum_c / total
            metrics.centroidRow = metrics.centroid_row
            metrics.centroidCol = metrics.centroid_col
        else:
            metrics.centroid_row = 0.0
            metrics.centroid_col = 0.0
            metrics.centroidRow = 0.0
            metrics.centroidCol = 0.0

        bbox = (0, -1, 0, -1) if rmax < rmin or cmax < cmin else (rmin, rmax, cmin, cmax)
        metrics.bbox = bbox
        try:
            metrics.bboxRowMin, metrics.bboxRowMax, metrics.bboxColMin, metrics.bboxColMax = bbox
        except Exception:
            pass
