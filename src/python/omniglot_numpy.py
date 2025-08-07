"""
Minimal Omniglot loader (no Torch).
Downloads once (~15 MB) and yields N-way K-shot episodes as NumPy arrays.
"""
import io, zipfile, random, requests
from pathlib import Path
from typing import Iterator, Tuple
import numpy as np
from PIL import Image

OMNIGLOT_URL = "https://github.com/brendenlake/omniglot/raw/master/python/images_background.zip"
DATA_DIR = Path(".omniglot_np")
IMG_SIZE = (28, 28)

def download_once() -> Path:
    DATA_DIR.mkdir(exist_ok=True)
    extracted = DATA_DIR / "images_background"
    if extracted.exists():
        return extracted
    print("Downloading Omniglot (~15 MB)...")
    resp = requests.get(OMNIGLOT_URL, timeout=60)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        zf.extractall(DATA_DIR)
    return extracted

def load_image(file_path: Path) -> np.ndarray:
    img = Image.open(file_path).convert("L").resize(IMG_SIZE, Image.LANCZOS)
    return np.asarray(img, dtype=np.float32) / 255.0

def omniglot_batches(shots: int, batch_classes: int = 5, seed: int = 42) -> Iterator[Tuple[np.ndarray, np.ndarray]]:
    random.seed(seed)
    root = download_once()
    class_dirs = [p for p in root.rglob("*") if p.is_dir() and any(p.iterdir())]
    while True:
        chosen = random.sample(class_dirs, batch_classes)
        images, labels = [], []
        for label, cls in enumerate(chosen):
            candidates = random.sample(list(cls.glob("*.png")), shots)
            for path in candidates:
                images.append(load_image(path))
                labels.append(label)
        yield np.stack(images), np.asarray(labels, dtype=np.int32)
