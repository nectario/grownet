from region import Region

def main():
    region = Region("dbg")
    layer_0 = region.add_layer(1, 0, 0)
    region.bind_input("x", [layer_0])

    region_metrics = region.tick("x", 0.42)
    # RegionMetrics has camelCase fields (DTO parity) but you can just print it if __repr__ is defined.
    print("deliveredEvents:", getattr(region_metrics, "deliveredEvents", None))
    print("totalSlots:", getattr(region_metrics, "totalSlots", None))
    print("totalSynapses:", getattr(region_metrics, "totalSynapses", None))

    # Optional: propagation path
    l1 = region.add_layer(1, 0, 0)
    region.connect_layers(layer_0, l1, 1.0, False)
    region_metrics_2 = region.tick("x", 0.95)
    print("deliveredEvents:", getattr(region_metrics_2, "deliveredEvents", None))

if __name__ == "__main__":
    main()
