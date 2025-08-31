# GrowNet · region_demo.mojo
# A tiny smoke test you can run with:  mojo run region_demo.mojo

from region import Region

fn main():
    region = Region("vision_like")
    layer0 = region.add_layer(10, 2, 1)  # 10 excitatory, 2 inhibitory, 1 modulatory
    layer1 = region.add_layer(12, 2, 1)

    region.connect_layers(layer0, layer1, probability=0.25, feedback=False)
    region.connect_layers(layer1, layer0, probability=0.05, feedback=True)

    region.bind_input("camera", [layer0])

    step = 0
    while step < 5:
        metrics = region.tick("camera", 1.0 + 0.1 * step)
        print("step", step, metrics)
        step += 1

if __name__ == "__main__":
    main()
