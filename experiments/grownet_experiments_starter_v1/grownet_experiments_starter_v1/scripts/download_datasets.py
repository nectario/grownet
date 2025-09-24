#!/usr/bin/env python3
# Downloads datasets using torchvision if available.
import argparse, sys, os
parser = argparse.ArgumentParser()
parser.add_argument("--root", type=str, default="data/raw")
parser.add_argument("--datasets", nargs="+", default=["mnist","fashion_mnist","emnist_letters","kmnist"])
args = parser.parse_args()

try:
    from torchvision import datasets, transforms
except Exception as e:
    print("torchvision not available. Please install torch/torchvision to auto-download datasets.", file=sys.stderr)
    sys.exit(1)

os.makedirs(args.root, exist_ok=True)
tf = transforms.ToTensor()

for name in args.datasets:
    if name == "mnist":
        datasets.MNIST(args.root, train=True, download=True, transform=tf)
        datasets.MNIST(args.root, train=False, download=True, transform=tf)
    elif name == "fashion_mnist":
        datasets.FashionMNIST(args.root, train=True, download=True, transform=tf)
        datasets.FashionMNIST(args.root, train=False, download=True, transform=tf)
    elif name == "emnist_letters":
        datasets.EMNIST(args.root, split="letters", train=True, download=True, transform=tf)
        datasets.EMNIST(args.root, split="letters", train=False, download=True, transform=tf)
    elif name == "kmnist":
        datasets.KMNIST(args.root, train=True, download=True, transform=tf)
        datasets.KMNIST(args.root, train=False, download=True, transform=tf)
    else:
        print(f"Unknown dataset: {name}")
print("All requested datasets downloaded.")
