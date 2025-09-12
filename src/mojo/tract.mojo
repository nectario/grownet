from synapse import Synapse

struct Tract:
    var src_layer_index: Int
    var dst_layer_index: Int
    var kernel_height: Int
    var kernel_width: Int
    var stride_height: Int
    var stride_width: Int
    var use_same_padding: Bool
    var feedback_enabled: Bool

    # Cached geometry
    var source_height: Int
    var source_width: Int
    var dest_height: Int
    var dest_width: Int

    fn init(mut self,
            src_layer_index: Int, dst_layer_index: Int,
            kernel_height: Int, kernel_width: Int,
            stride_height: Int, stride_width: Int,
            use_same_padding: Bool, feedback_enabled: Bool,
            source_height: Int, source_width: Int,
            dest_height: Int, dest_width: Int) -> None:
        self.src_layer_index = src_layer_index
        self.dst_layer_index = dst_layer_index
        self.kernel_height = if kernel_height > 0 then kernel_height else 1
        self.kernel_width  = if kernel_width  > 0 then kernel_width  else 1
        self.stride_height = if stride_height > 0 then stride_height else 1
        self.stride_width  = if stride_width  > 0 then stride_width  else 1
        self.use_same_padding = use_same_padding
        self.feedback_enabled = feedback_enabled
        self.source_height = source_height
        self.source_width  = source_width
        self.dest_height   = dest_height
        self.dest_width    = dest_width

    fn _origin_list(self) -> list[tuple[Int, Int]]:
        var origins: list[tuple[Int, Int]] = []
        if self.use_same_padding:
            var pad_rows = (self.kernel_height - 1) / 2
            var pad_cols = (self.kernel_width  - 1) / 2
            var origin_row = -pad_rows
            while origin_row + self.kernel_height <= self.source_height + pad_rows + pad_rows:
                var origin_col = -pad_cols
                while origin_col + self.kernel_width <= self.source_width + pad_cols + pad_cols:
                    origins.append((origin_row, origin_col))
                    origin_col = origin_col + self.stride_width
                origin_row = origin_row + self.stride_height
        else:
            var origin_row_valid = 0
            while origin_row_valid + self.kernel_height <= self.source_height:
                var origin_col_valid = 0
                while origin_col_valid + self.kernel_width <= self.source_width:
                    origins.append((origin_row_valid, origin_col_valid))
                    origin_col_valid = origin_col_valid + self.stride_width
                origin_row_valid = origin_row_valid + self.stride_height
        return origins

    fn _row_col_from_flat(self, flat_index: Int) -> tuple[Int, Int]:
        var row_index = flat_index / self.source_width
        var col_index = flat_index % self.source_width
        return (row_index, col_index)

    fn _center_for_origin(self, origin_row: Int, origin_col: Int) -> Int:
        var center_row = origin_row + (self.kernel_height / 2)
        var center_col = origin_col + (self.kernel_width  / 2)
        if center_row < 0: center_row = 0
        if center_col < 0: center_col = 0
        if center_row > (self.dest_height - 1): center_row = self.dest_height - 1
        if center_col > (self.dest_width  - 1): center_col = self.dest_width  - 1
        return center_row * self.dest_width + center_col

    fn attach_source_neuron(mut self, region: any, new_source_index: Int) -> Int:
        # Wires just-grown source neuron through this tract; returns created edge count.
        var created_edges = 0
        var (row_index, col_index) = self._row_col_from_flat(new_source_index)
        var window_origins = self._origin_list()

        # Determine if destination is OutputLayer2D
        var destination_is_output_2d = hasattr(region.layers[self.dst_layer_index], "height") \
                                and hasattr(region.layers[self.dst_layer_index], "width")

        if destination_is_output_2d:
            var seen_center_indices: dict[Int, Bool] = dict[Int, Bool]()
            var origin_index = 0
            while origin_index < window_origins.len:
                var origin_row = window_origins[origin_index][0]
                var origin_col = window_origins[origin_index][1]
                var window_row_start = if origin_row > 0 then origin_row else 0
                var window_col_start = if origin_col > 0 then origin_col else 0
                var window_row_end   = if (origin_row + self.kernel_height) < self.source_height \
                                       then (origin_row + self.kernel_height) else self.source_height
                var window_col_end   = if (origin_col + self.kernel_width) < self.source_width \
                                       then (origin_col + self.kernel_width) else self.source_width
                if row_index >= window_row_start and row_index < window_row_end \
                   and col_index >= window_col_start and col_index < window_col_end:
                    var center_flat_index = self._center_for_origin(origin_row, origin_col)
                    if not seen_center_indices.contains(center_flat_index):
                        var syn = Synapse(center_flat_index, self.feedback_enabled)
                        region.layers[self.src_layer_index].get_neurons()[new_source_index].outgoing.append(syn)
                        seen_center_indices[center_flat_index] = True
                        created_edges = created_edges + 1
                origin_index = origin_index + 1
            return created_edges

        # Generic destination: connect to all destination neurons
        var dest_neuron_list = region.layers[self.dst_layer_index].get_neurons()
        var dest_index = 0
        while dest_index < dest_neuron_list.len:
            var syn_generic = Synapse(dest_index, self.feedback_enabled)
            region.layers[self.src_layer_index].get_neurons()[new_source_index].outgoing.append(syn_generic)
            dest_index = dest_index + 1
            created_edges = created_edges + 1
        return created_edges

    # Parity adapter: deliver from a given source index to destination layer.
    fn on_source_fired(self, region: any, source_index: Int, amplitude: Float64) -> None:
        # If destination is OutputLayer2D, this tract wires source→center edges explicitly.
        # For generic destinations, forward to all destination neurons.
        var dest_layer = region.layers[self.dst_layer_index]
        var destination_is_output_2d = hasattr(dest_layer, "height") and hasattr(dest_layer, "width")
        if destination_is_output_2d:
            # Compute all centers for windows that include this source, and stimulate those outputs.
            var origins = self.origin_list()
            var row_index = source_index / self.source_width
            var col_index = source_index % self.source_width
            var seen_center = dict[Int, Bool]()
            var it = 0
            while it < origins.len:
                var orow = origins[it][0]
                var ocol = origins[it][1]
                var window_row_start = if orow > 0 then orow else 0
                var window_col_start = if ocol > 0 then ocol else 0
                var window_row_end = if (orow + self.kernel_height) < self.source_height then (orow + self.kernel_height) else self.source_height
                var window_col_end = if (ocol + self.kernel_width) < self.source_width then (ocol + self.kernel_width) else self.source_width
                if row_index >= window_row_start and row_index < window_row_end and col_index >= window_col_start and col_index < window_col_end:
                    var center = self.center_for_origin(orow, ocol)
                    if not seen_center.contains(center):
                        region.layers[self.dst_layer_index].propagate_from(center, amplitude)
                        seen_center[center] = True
                it = it + 1
            return
        # Generic destination: route using layer helper
        region.layers[self.dst_layer_index].propagate_from(source_index, amplitude)
