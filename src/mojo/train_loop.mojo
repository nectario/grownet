from layer import Layer
from std.random import rand

fn main():
    var layer = Layer()
    layer.init(ex=20, inh=5, mod=3)

    for _ in range(1000):
        layer.forward(rand())

    print("Mojo GrowNet synthetic pass finished.")


