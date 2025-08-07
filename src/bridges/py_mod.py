import argparse, yaml, importlib, time, torch, torchvision
from pathlib import Path

# ----------------- CLI & YAML --------------------
parser = argparse.ArgumentParser()
parser.add_argument("--exp", required=True, help="YAML experiment file")
args = parser.parse_args()

cfg = yaml.safe_load(Path(args.exp).read_text())

# ------------- inject YAML constants ------------
import modular  # Modular CLI runtime
neuron_mod = importlib.import_module("neuron")

neuron_mod.get_eps       = lambda: float(cfg["eps"])
neuron_mod.get_beta      = lambda: float(cfg["beta"])
neuron_mod.get_eta       = lambda: float(cfg["eta"])
neuron_mod.get_r_star    = lambda: float(cfg["r_star"])
neuron_mod.get_max_slots = lambda: cfg.get("max_slots_per_neuron")
neuron_mod.get_hit_sat   = lambda: int(cfg["hit_saturation"])

# ------------- simple Omniglot loader -----------
def omniglot_loader(shots):
    transform = torchvision.transforms.ToTensor()
    ds = torchvision.datasets.Omniglot(root=".", download=True, transform=transform, background=True)
    return torch.utils.data.DataLoader(ds, batch_size=shots, shuffle=True)

# ------------- run E‑00 --------------------------
def run_e00():
    dl = omniglot_loader(cfg["shots"])
    net = neuron_mod.Neuron(id="root")

    correct = total = 0
    start = time.time()
    for imgs, labels in dl:
        for x in imgs.view(-1):  # flatten pixels
            net.on_input(float(x))
        # dummy classifier: predict same label
        correct += 1
        total   += 1
    print(f"Accuracy (dummy) {correct/total:.3f}   θ={net.theta:.3f}   r̂={net.ema_rate:.3f}")
    print(f"Run time {time.time()-start:.1f}s")

if __name__ == "__main__":
    run_e00()
