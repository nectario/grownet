# GrowNet Experiments Starter (v1)

This bundle gives you ready-to-run folders for MNIST variants and a **Morse** signals task, plus small **synthetic sample datasets** so you can smoke-test the pipeline immediately. For full benchmarks, use the auto-download script to fetch official datasets.

## Contents
- `configs/` – YAML configs per dataset (thresholds, horizons, curriculum, flags like `--fix.anchor_adjustment`).
- `runners/` – CLI scripts: `run_experiment.py`, `evaluate.py`, `forecast_card.py`.
- `datasets/` – lightweight loaders and synthetic generators.
- `scripts/` – `data_fetch.sh` and `download_datasets.py` (uses `torchvision` if available).
- `data/synthetic/` – small MNIST-like, MNIST-1D-like, and Morse audio sample sets.
- `forecast_cards/templates/` – card template for reporting.
- `outputs/` – results will be written here.

## Quick Start (smoke test, no heavy deps)
```bash
python3 runners/run_experiment.py --dataset mnist_like --mode dummy --out outputs/mnist_like
python3 runners/run_experiment.py --dataset mnist1d_like --mode dummy --out outputs/mnist1d
python3 runners/run_experiment.py --dataset morse --mode dummy --out outputs/morse
```

## Full Datasets
Run:
```bash
bash scripts/data_fetch.sh
```
This uses `torchvision` to download MNIST, Fashion-MNIST, EMNIST (letters), and KMNIST into `data/raw/`. For MNIST-C and other robustness sets, the script explains where to obtain them. **Note:** This zip ships only *small synthetic samples* due to size/licensing. The fetch script pulls official data directly from standard sources on your machine.

## Forecast Cards
After each run, a `forecast_card.yaml` is written. Edit `configs/*` to set your acceptance thresholds.

---
Generated on 2025-09-22.
