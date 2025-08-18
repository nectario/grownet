# region.mojo
# Region orchestration updated to use RegionMetrics helpers.
from metrics import RegionMetrics

# Minimal protocol types; in your codebase these should be real classes:
# - Layer with fn forward(value: Float64) and fn endTick() and fn getNeurons() -> List[Any]
# - InputLayer2D with fn forwardImage(frame: Any)
# Here we declare 'opaque' types and use duck typing at runtime; adjust as needed in your project.

struct PruneSummary:
    var prunedSynapses: Int64
    var prunedEdges: Int64
    fn __init__() -> Self:
        return Self(prunedSynapses=0, prunedEdges=0)

struct Region:
    var _name: String
    var _layers: List[Any]
    var _inputPorts: Dict[String, List[Int32]]
    var _outputPorts: Dict[String, List[Int32]]

    fn __init__(name: String) -> Self:
        return Self(_name=name, _layers=List[Any](), _inputPorts=Dict[String, List[Int32]](), _outputPorts=Dict[String, List[Int32]]())

    fn addLayer(inout self, excitatoryCount: Int32, inhibitoryCount: Int32, modulatoryCount: Int32) -> Int32:
        # In your real code, import the concrete Layer and construct it.
        # Here we error at runtime if not wired by the integrator.
        raise "Region.addLayer requires Layer factory in Mojo environment"

    fn addInputLayer2D(inout self, height: Int32, width: Int32, gain: Float64, epsilonFire: Float64) -> Int32:
        raise "Region.addInputLayer2D requires InputLayer2D factory in Mojo environment"

    fn addOutputLayer2D(inout self, height: Int32, width: Int32, smoothing: Float64) -> Int32:
        raise "Region.addOutputLayer2D requires OutputLayer2D factory in Mojo environment"

    fn bindInput(inout self, port: String, layerIndices: List[Int32]) -> None:
        self._inputPorts[port] = layerIndices

    fn bindOutput(inout self, port: String, layerIndices: List[Int32]) -> None:
        self._outputPorts[port] = layerIndices

    fn tick(self, port: String, value: Float64) -> RegionMetrics:
        var m = RegionMetrics()
        if let entry = self._inputPorts.get(port):
            for idx in entry:
                let layer = self._layers[idx]
                layer.forward(value)     # expects Layer API
                m.incDeliveredEvents(1)
        # end-of-tick housekeeping
        for layer in self._layers:
            layer.endTick()
        # aggregates
        for layer in self._layers:
            for neuron in layer.getNeurons():
                m.addSlots(neuron.getSlots().len().to_int64())
                m.addSynapses(neuron.getOutgoing().len().to_int64())
        return m

    fn tickImage(self, port: String, frame: Any) -> RegionMetrics:
        var m = RegionMetrics()
        if let entry = self._inputPorts.get(port):
            for idx in entry:
                let layer = self._layers[idx]
                if layer.isInputLayer2D():
                    layer.forwardImage(frame)
                    m.incDeliveredEvents(1)
        for layer in self._layers:
            layer.endTick()
        for layer in self._layers:
            for neuron in layer.getNeurons():
                m.addSlots(neuron.getSlots().len().to_int64())
                m.addSynapses(neuron.getOutgoing().len().to_int64())
        return m

    fn getName(self) -> String:
        return self._name

    fn getLayers(self) -> List[Any]:
        return self._layers
