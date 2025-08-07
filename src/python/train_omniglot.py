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
    for _ in tqdm(range(num_batches), desc="Omniglot episodes"):
        images, _ = next(batch_stream)             # shape: (N, 28, 28)
        for pixel_value in images.ravel():         # stream pixels
            layer.forward(float(pixel_value))
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
