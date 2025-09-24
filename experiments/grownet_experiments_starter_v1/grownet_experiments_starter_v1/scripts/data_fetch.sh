#!/usr/bin/env bash
set -euo pipefail
PYTHON=${PYTHON:-python3}

echo "[*] This script will try to download MNIST/Fashion/EMNIST/KMNIST via torchvision."
echo "    It will NOT download MNIST-C or other robustness sets due to licensing/hosting differences."
echo "    For MNIST-C, see: https://github.com/hendrycks/robustness (instructions in their README)."

$PYTHON scripts/download_datasets.py --root data/raw --datasets mnist fashion_mnist emnist_letters kmnist

echo "[*] Done. Datasets saved under data/raw/."
