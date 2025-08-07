import sys
from neuron import Neuron
from std.random import rand

# -- minimal synthetic stream sanity test ---------------------------
fn synthetic_test(steps: Int = 1000):
    let root = @owned Neuron(id="root")
    for i in range(steps):
        let x = rand()          # uniform 0..1
        root.on_input(x)
    print("θ=", root.theta, "  r̂=", root.ema_rate)

if __name__ == "__main__":
    synthetic_test()
