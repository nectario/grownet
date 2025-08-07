import time, torch, torchvision
from neuron import Neuron
from tqdm import tqdm

def omniglot_loader(shots):
    tfm = torchvision.transforms.ToTensor()
    ds  = torchvision.datasets.Omniglot(root=".", download=True, transform=tfm, background=True)
    return torch.utils.data.DataLoader(ds, batch_size=shots, shuffle=True)

def run(shots=5):
    dl   = omniglot_loader(shots)
    root = Neuron("root")

    start = time.time()
    for imgs, _ in tqdm(dl, total=len(dl)):
        for x in imgs.view(-1):
            root.onInput(float(x))

    print(f"θ={root.theta:.3f}   r̂={root.ema_rate:.3f}   time={time.time()-start:.1f}s")

if __name__ == "__main__":
    run()
