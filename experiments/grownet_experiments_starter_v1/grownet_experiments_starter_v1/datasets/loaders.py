# Dataset loaders (placeholders). For real runs, add torchvision-based loaders here.
# Synthetic loaders are provided for mnist_like, mnist1d_like, and morse.
# Real datasets will be downloaded into data/raw by scripts/download_datasets.py.

def load(dataset_name, data_root="data"):
    if dataset_name in ("mnist_like","mnist1d_like","morse"):
        return {"status":"ok","path":f"{data_root}/synthetic/{dataset_name}"}
    else:
        return {"status":"needs_download","path":f"{data_root}/raw/{dataset_name}"}
