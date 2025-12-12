# Codex Requirements — Focus Phase‑B (Spatial Focus)

**TL;DR**
 Add first‑class **spatial focus** capabilities: (1) spatial slotting (anchor + 2D bins), (2) 2D wiring helpers, and (3) optional per‑tick **spatial metrics** (centroid/bbox/active count). Keep default behavior unchanged; Spatial Focus activates only when explicitly enabled.

------

## 0) Invariants (do not break)

- **V4 ports‑as‑edges** model remains the default.
- Existing Python tests must continue to pass without flags.
- `RegionMetrics` existing fields (`delivered_events`, `total_slots`, `total_synapses` + camelCase aliases) stay intact.
- Keep naming and style from the recent refactors (no re‑introducing 1–2 char names, camel/snake aliasing preserved).

------

## 1) Goals

1. **Spatial slotting (2D)**
   - Allow neurons to learn coarse **spatial offsets** from an anchor (row/col) using 2D bins, analogous to temporal FIRST‑anchor slotting.
   - Anchor policy: `FIRST` (first strong event fixes anchorRow/anchorCol); allow `ORIGIN` (0,0) for synthetic inputs.
2. **Windowed 2D wiring helper**
   - Provide a deterministic helper to wire **InputLayer2D → Layer** (or → OutputLayer2D) with a sliding window (`kernel_h/w`, `stride_h/w`, `padding` in {`valid`,`same`}).
3. **Spatial metrics (optional)**
   - When enabled, compute **activePixels**, **centroidRow/centroidCol**, and **bbox** after a 2D tick from the *most downstream* 2D layer that produced a frame this tick (prefer an `OutputLayer2D` if present; otherwise derive from the driven `InputLayer2D` amplitudes).
   - Metrics must be cheap to skip (guarded by a flag/config).

------

## 2) Non‑Goals (for this phase)

- No convolutional weights, pooling layers, or backprop/gradient methods.
- No change to default `deliveredEvents` accounting.
- No cross‑language test harness beyond compile parity (Python is the canonical test surface).

------

## 3) Entry State (assumed)

- Python: `Region`, `Layer`, `InputLayer2D`, `OutputLayer2D`, `SlotEngine`, `Neuron`, `Weight`, tests under `src/python/tests/`.
- C++/Java/Mojo: parallel core types exist and build (per recent refactors).
- V4 docs and `docs/TESTING.md` present.

------

## 4) Deliverables

- **Code (Python, reference)**: feature‑complete spatial focus (slotting + wiring + metrics).
- **Code (C++/Java/Mojo)**: compile‑ready data members + signatures; minimal no‑op implementations that keep behavior unchanged unless enabled.
- **Tests (Python)**: new tests for spatial slotting and spatial metrics.
- **Docs**: `docs/SPATIAL_FOCUS.md` and a short note in `docs/TESTING.md`.

------

## 5) Detailed Work (by language)

### 5.1 Python (authoritative)

**A) Slot engine extensions**

- File: `src/python/slot_engine.py`

  - Add config fields (keep snake + camel aliases if user‑facing anywhere):

    ```python
    class SlotConfig:
        # existing...
        spatial_enabled: bool = False
        row_bin_width_pct: float = 100.0
        col_bin_width_pct: float = 100.0
        anchor_mode: str = "FIRST"  # or "ORIGIN"
    ```

  - Add:

    ```python
    def slot_id_2d(self, anchor_rc, current_rc) -> Tuple[int,int]:
        """Return (rowBin, colBin) using |Δrow| and |Δcol| as % of denom (row/col wise)."""
    def select_or_create_slot_2d(self, neuron, row:int, col:int):
        """Like select_or_create_slot but based on 2D anchor/bins; respects slot_limit."""
    ```

  - Use the same **capacity clamp** behavior you implemented for scalar slots.

**B) Neuron spatial anchors + API**

- File: `src/python/neuron.py`

  - Add members (init defaults):

    ```python
    self.focus_anchor_row = None
    self.focus_anchor_col = None
    ```

  - Add:

    ```python
    def on_input_2d(self, value: float, row: int, col: int) -> bool:
        """Spatial variant: manage row/col FIRST anchor, select/create spatial slot, then reinforce/threshold like on_input."""
        # If not spatial_enabled in slot_cfg: fall back to on_input(value)
    ```

  - **Do not** change existing `on_input`.

**C) Layer propagation with 2D context**

- File: `src/python/layer.py`

  - Ensure `Layer` exposes (or stores) whether **spatial slotting** is desired (e.g., via constructor `slot_cfg` or a setter). This piggybacks on the layer’s existing `slot_cfg` if present.

  - Implement/extend:

    ```python
    def propagate_from(self, source_index: int, value: float) -> None:
        """If spatial slotting is enabled *and* we know the source 2D shape, compute (row,col) and call on_input_2d; else, default forward path."""
    ```

  - To compute `(row, col)`, prefer information passed by the tract (see D).

**D) Tract: pass source shape**

- File: `src/python/tract.py`

  - When constructed with a source `InputLayer2D`, capture its `(height,width)`.

  - In `on_source_fired`, provide source `(row,col)` to the destination layer via a new call:

    ```python
    self.dst.propagate_from(source_index, value)  # existing
    # Option A (minimal change): self.dst can discover shape by introspecting self.src
    # Option B (preferred): store self.src_shape on the tract and let dst query it via an injected callback
    ```

  - Minimal approach: keep the current call, but give `Layer.propagate_from` a way to look up the shape through a weak ref to the source layer if the layer is 2D.

**E) Region wiring helper (windowed)**

- File: `src/python/region.py`

  - Add:

    ```python
    def connect_layers_windowed(self,
        src_idx:int, dst_idx:int, kernel_h:int, kernel_w:int,
        stride_h:int=1, stride_w:int=1, padding:str="valid", feedback:bool=False
    ) -> int:
        """Wire src(2D) → dst in sliding windows; returns number of synapses created."""
    ```

  - Only support when `src` is `InputLayer2D` (or any layer exposing `height/width`). If `dst` is `OutputLayer2D`, wire one‑to‑one into the corresponding output neuron inside each window center; otherwise wire to all neurons in `dst` (simple fan‑out). Keep it **deterministic** (no RNG).

**F) Spatial metrics (optional)**

- File: `src/python/metrics.py`

  - Add **optional** fields + camelCase aliases (default to zero/None):

    ```python
    self.active_pixels = 0;      self.activePixels = 0
    self.centroid_row = 0.0;     self.centroidRow = 0.0
    self.centroid_col = 0.0;     self.centroidCol = 0.0
    self.bbox = (0, -1, 0, -1)   # (row_min,row_max,col_min,col_max), empty if row_min>row_max
    ```

  - Provide setters/getters mirroring V4 alias pattern.

- File: `src/python/region.py`

  - In `tick_2d`, if **env flag** `GROWNET_ENABLE_SPATIAL_METRICS=1` (or `region.enable_spatial_metrics` set), compute metrics:
    - Choose the **furthest downstream** 2D layer that has a frame snapshot this tick (prefer `OutputLayer2D`).
    - Threshold: `> 0.0` is active (configurable later).
    - Compute:
      - `active_pixels`
      - `centroid_row/col` as weighted average with weights = pixel values (fallback to simple average over active pixels).
      - `bbox` as min/max row/col over active pixels.
    - Set both snake and camel aliases.

**G) Tests (Python)**

- Add file: `src/python/tests/test_spatial_focus.py`

  1. **Spatial slotting basics**

     ```python
     def test_spatial_slotting_first_anchor_and_bins():
         region = Region("spatial")
         l_in = region.add_input_layer_2d(4, 4, 1.0, 0.01)
         l_hid = region.add_layer(excitatory_count=8, inhibitory_count=0, modulatory_count=0)
         # Enable spatial slotting in hidden layer (coarse 2x2 bins)
         for n in l_hid.get_neurons():
             n.slot_cfg.spatial_enabled = True
             n.slot_cfg.row_bin_width_pct = 50.0
             n.slot_cfg.col_bin_width_pct = 50.0
     
         # Wire deterministically with window 2x2 stride 2
         region.connect_layers_windowed(l_in, l_hid, kernel_h=2, kernel_w=2, stride_h=2, stride_w=2, padding="valid")
     
         region.bind_input("img", [l_in])
     
         # Tick a frame with a bright pixel at (1,1)
         frame1 = [[0,0,0,0],[0,1,0,0],[0,0,0,0],[0,0,0,0]]
         region.tick_2d("img", frame1)
     
         # Tick a shifted frame at (1,2): should create a **different** spatial slot bin in some neuron
         frame2 = [[0,0,0,0],[0,0,1,0],[0,0,0,0],[0,0,0,0]]
         m = region.tick_2d("img", frame2)
     
         # Structural evidence of spatial slotting
         assert m.total_slots > 0
     ```

     (Keep the assertion conservative; you may inspect specific neurons if convenient.)

  2. **Spatial metrics centroid/bbox**

     ```python
     def test_spatial_metrics_centroid_and_bbox(monkeypatch):
         import os; monkeypatch.setenv("GROWNET_ENABLE_SPATIAL_METRICS", "1")
     
         region = Region("spatial_metrics")
         l_in = region.add_input_layer_2d(3, 3, 1.0, 0.01)
         l_out = region.add_output_layer_2d(3, 3, smoothing=0.0)
     
         region.connect_layers(l_in, l_out, probability=1.0, feedback=False)  # full fanout for the test
         region.bind_input("img", [l_in, l_out])
     
         frame = [
             [0, 0.5, 0],
             [0, 1.0, 0],
             [0, 0,   0],
         ]
         m = region.tick_2d("img", frame)
     
         assert m.active_pixels >= 1
         # centroid must be near the (1,1) neighborhood; allow float tolerance
         assert 0.5 <= m.centroid_row <= 1.5
         assert 0.5 <= m.centroid_col <= 1.5
         r0, r1, c0, c1 = m.bbox
         assert r0 <= r1 and c0 <= c1
     ```

- Keep both tests self‑contained and fast; no fixtures beyond optional env monkeypatch.

**H) Docs**

- Add file: `docs/SPATIAL_FOCUS.md`
  - Describe:
    - What “spatial focus” means in GrowNet (FIRST anchor on (row,col) + 2D bins).
    - How to enable (`slot_cfg.spatial_enabled = True` on the receiving layer’s neurons).
    - `connect_layers_windowed` usage and parameter semantics.
    - Optional spatial metrics (env flag and the computed fields).
  - Cross‑reference `docs/TESTING.md` with a short section:
    - “Spatial metrics: set `GROWNET_ENABLE_SPATIAL_METRICS=1` to compute centroid/bbox during tests.”

------

### 5.2 C++ / Java / Mojo (compile parity; no behavior change unless enabled)

Implement data members + signatures sufficient to keep parity and avoid API drift. Do **not** enable logic by default.

**C++**

- `Neuron.h`

  - Add `int anchorRow = -1; int anchorCol = -1;`

  - Add:

    ```cpp
    bool onInput2D(double value, int row, int col); // default: calls onInput(value)
    ```

- `SlotEngine` or equivalent:

  - Add stubs `slotId2D`, `selectOrCreateSlot2D`.

- `Region`:

  - Add `connectLayersWindowed(...)` signature; implement deterministic wiring if straightforward, or return 0 with TODO if not (but prefer a minimal working version for 2D→Layer).

- `RegionMetrics`:

  - Add optional fields: `activePixels`, `centroidRow`, `centroidCol`, `bboxRowMin/RowMax/ColMin/ColMax`.
  - Only compute/set when a toggle is active (env or a `Region` flag).

**Java**

- `Neuron.java`:
  - `private int anchorRow = -1, anchorCol = -1;`
  - `public boolean onInput2D(double value, int row, int col) { return onInput(value); }`
- `SlotEngine.java`:
  - `int selectOrCreateSlot2D(Neuron neuron, int row, int col, SlotConfig cfg)` (no‑op default or reuse scalar path).
- `Region.java`:
  - `connectLayersWindowed(...)` method; deterministic wiring from `InputLayer2D`.
- `RegionMetrics.java`:
  - Add fields + accessors for `activePixels`, `centroidRow/Col`, `bbox`.

**Mojo**

- Mirror the same member additions and method signatures (default to the scalar path).

> **Note:** Keep compile parity but you don’t need to implement spatial metrics computation outside Python in this phase (leave TODO comments). Do ensure no exceptions are thrown when toggles are off.

------

## 6) Backwards Compatibility & Flags

- Spatial slotting is **off** unless `slot_cfg.spatial_enabled = True` for the destination neurons.
- Spatial metrics are **off** unless `GROWNET_ENABLE_SPATIAL_METRICS=1` (or a `Region.enable_spatial_metrics` boolean is set, your choice).
- Keep existing env flag `GROWNET_COMPAT_DELIVERED_COUNT` untouched.

------

## 7) Acceptance Criteria

- **All existing Python tests** pass with no flags.
- New tests in `test_spatial_focus.py` pass locally.
- Running `GROWNET_ENABLE_SPATIAL_METRICS=1 pytest -q` succeeds.
- C++/Java/Mojo projects build (or at least compile the touched files) with the new members/signatures.
- No changes to public defaults that would affect demos unless spatial is explicitly enabled.

------

## 8) Risk & Mitigation

- **Performance**: Spatial metrics can be O(H*W). Mitigate by guarding behind the env flag.
- **API drift across languages**: Keep method names and data members aligned; add TODOs where full implementation is deferred.
- **Over‑wiring**: `connect_layers_windowed` must be deterministic and bounded; avoid RNG.

------

## 9) Suggested commit structure

1. `feat(py): spatial slotting (FIRST anchor, 2D bins) + windowed wiring helper`
2. `feat(py): optional spatial metrics (centroid/bbox/activePixels) behind env flag`
3. `test(py): add test_spatial_focus (slotting + metrics)`
4. `docs: add SPATIAL_FOCUS.md; update TESTING.md with spatial metrics flag`
5. `chore(cpp,java,mojo): parity stubs for spatial slotting + metrics fields (no behavior change)`

------

## 10) How to validate locally (Python)

```bash
# default: no spatial metrics
pytest -q

# with spatial metrics enabled
GROWNET_ENABLE_SPATIAL_METRICS=1 pytest -q
```

------

## 11) Nice‑to‑have (post‑merge follow‑ups, not part of this PR)

- Add `SpatialPooling2D` (max/avg) as a thin `OutputLayer2D` variant.
- Per‑layer threshold for “active” pixel classification in spatial metrics.
- Converters to/from radial bins (`Δr, Δθ`) in the slot engine.

------

If you want, I can also draft the **PR description** text and a minimal **usage snippet** for `SPATIAL_FOCUS.md` (Python), but the above is sufficient for Codex to implement Phase‑B cleanly without breaking V4.