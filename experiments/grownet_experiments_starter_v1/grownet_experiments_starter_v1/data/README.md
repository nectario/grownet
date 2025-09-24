# Data folder

- `synthetic/` contains small samples included in this zip for smoke tests:
  - `mnist_like/` — 28x28 grayscale CSVs (100 images total) with `labels.csv`.
  - `mnist1d_like/` — 1D sequences CSVs with `labels.csv`.
  - `morse/` — WAV audio files + `labels.csv` for A–Z and 0–9 (2 examples each).

- `raw/` will hold official datasets after running `scripts/data_fetch.sh`.
  - Requires `torchvision` for MNIST, Fashion-MNIST, EMNIST, and KMNIST.
  - For MNIST-C and robustness suites, follow authors' instructions.
