# GrowNet · region_demo.mojo
# A tiny smoke test you can run with:  mojo run region_demo.mojo

from region import Region

fn main():
    r = Region("vision_like")
    l0 = r.add_layer(10, 2, 1)  # 10 excitatory, 2 inhibitory, 1 modulatory
    l1 = r.add_layer(12, 2, 1)

    r.connect_layers(l0, l1, probability=0.25, feedback=False)
    r.connect_layers(l1, l0, probability=0.05, feedback=True)

    r.bind_input("camera", [l0])

    step = 0
    while step < 5:
        metrics = r.tick("camera", 1.0 + 0.1 * step)
        print("step", step, metrics)
        step += 1

if __name__ == "__main__":
    main()
