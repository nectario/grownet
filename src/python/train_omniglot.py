"""
Run a quick Omniglot stream through a single GrowNet layer.
No heavy frameworks: only numpy, pillow, requests, tqdm.
"""
import argparse, time
import numpy as np
from tqdm import tqdm
from omniglot_numpy import omniglot_batches
from layer import Layer

def run_few_shot(
    shots: int = 5,
    num_batches: int = 100,
    num_excit: int = 50,
    num_inhib: int = 0,
    num_mod: int = 0,
    p_feedforward: float = 0.1,
    p_feedback: float = 0.01,
):
    batch_stream = omniglot_batches(shots, batch_classes=5)
    layer = Layer(size_excit=num_excit, size_inhib=num_inhib, size_mod=num_mod)
    layer.wire_random_feedforward(probability=p_feedforward)
    layer.wire_random_feedback(probability=p_feedback)

    start_time = time.time()

    for batch_index in tqdm(range(num_batches), desc="Omniglot episodes"):
        images, _ = next(batch_stream)
        for pixel_value in images.ravel():
            layer.forward(float(pixel_value))

        if args.log_every and (batch_index + 1) % args.log_every == 0:
            readiness = [n.neuron_value("readiness") for n in layer.neurons]
            firing    = [n.neuron_value("firing_rate") for n in layer.neurons]
            memory    = [n.neuron_value("memory") for n in layer.neurons]
            avg_r = sum(readiness) / max(len(readiness), 1)
            max_r = max(readiness) if readiness else 0.0
            avg_f = sum(firing) / max(len(firing), 1)
            sum_m = sum(memory)
            print(f"[batch {batch_index+1}] readiness avg={avg_r:.3f} max={max_r:.3f} | "
                  f"firing avg={avg_f:.3f} | memory sum={sum_m:.3f}")


    duration = time.time() - start_time

    total_slots = sum(len(n.slots) for n in layer.neurons)
    average_ema = np.mean([w.ema_rate for n in layer.neurons for w in n.slots.values()]) if total_slots else 0.0
    total_synapses = sum(len(n.outgoing) for n in layer.neurons)

    print("\n=== Run summary ===")
    print(f"Shots per class          : {shots}")
    print(f"E/I/M neurons            : {num_excit}/{num_inhib}/{num_mod}")
    print(f"Feedforward / Feedback p : {p_feedforward:.3f} / {p_feedback:.3f}")
    print(f"Total slots       : {total_slots}")
    print(f"Total synapses           : {total_synapses}")
    print(f"Average firing EMA       : {average_ema:.4f}")
    print(f"Elapsed time             : {duration:.1f} s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--shots", type=int, default=5)
    parser.add_argument("--batches", type=int, default=100)
    parser.add_argument("--excit", type=int, default=50)
    parser.add_argument("--inhib", type=int, default=0)
    parser.add_argument("--mod", type=int, default=0)
    parser.add_argument("--p_feedforward", type=float, default=0.10)
    parser.add_argument("--p_feedback", type=float, default=0.01)
    parser.add_argument("--log_every", type=int, default=0, help="Log neuron values every N batches (0 = off)")

    args = parser.parse_args()

    run_few_shot(
        shots=args.shots,
        num_batches=args.batches,
        num_excit=args.excit,
        num_inhib=args.inhib,
        num_mod=args.mod,
        p_feedforward=args.p_feedforward,
        p_feedback=args.p_feedback,
    )
