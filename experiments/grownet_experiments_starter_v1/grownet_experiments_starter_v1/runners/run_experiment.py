#!/usr/bin/env python3
import argparse, os, yaml, random, time, json
from pathlib import Path

def ensure_dir(p): os.makedirs(p, exist_ok=True)

def dummy_metrics(dataset):
    random.seed(1337 + hash(dataset) % 10000)
    # pretend better results for sMNIST/pMNIST/morse
    base_acc = {
        "mnist_like": 0.96,
        "smnist": 0.985,
        "pmnist": 0.981,
        "fashion_mnist": 0.992,
        "emnist_letters": 0.955,
        "kmnist": 0.965,
        "mnist_c": 0.90,
        "mnist1d_like": 0.94,
        "morse": 0.95
    }.get(dataset, 0.90)
    ece = 0.05 if base_acc > 0.95 else 0.10
    return {"accuracy": base_acc, "ece": ece}

def write_forecast_card(outdir, dataset, metrics):
    from forecast_card import make_forecast_card
    card = make_forecast_card(model_name="GrowNet-S (dummy)", dataset=dataset, metrics=metrics)
    with open(os.path.join(outdir, "forecast_card.yaml"), "w") as f:
        f.write(card)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=str, default=None)
    ap.add_argument("--dataset", type=str, default=None)
    ap.add_argument("--mode", type=str, default="dummy", choices=["dummy", "torch"])
    ap.add_argument("--out", type=str, required=True)
    args = ap.parse_args()

    if args.config and not args.dataset:
        import yaml
        cfg = yaml.safe_load(open(args.config))
        dataset = cfg.get("dataset","unknown")
    else:
        dataset = args.dataset or "unknown"

    outdir = Path(args.out)
    ensure_dir(outdir)

    print(f"[run] dataset={dataset} mode={args.mode}")
    time.sleep(0.2)
    # In 'torch' mode you'd import torchvision loaders & a small model here.
    metrics = dummy_metrics(dataset)
    with open(outdir / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    write_forecast_card(str(outdir), dataset, metrics)
    print(f"[done] wrote {outdir}")

if __name__ == "__main__":
    main()
