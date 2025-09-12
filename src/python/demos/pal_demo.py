from pal.api import ParallelOptions, parallel_map
from pal.domains import IndexDomain


def run_pal_demo() -> None:
    # Simple deterministic sum of squares using PAL
    options = ParallelOptions(max_workers=None, tile_size=1024, reduction_mode="ordered", device="cpu")
    domain = IndexDomain(count=10000)

    def kernel(index: int) -> float:
        value = float(index)
        return value * value

    def reduce_in_order(locals_list: list[float]) -> float:
        total = 0.0
        for value in locals_list:
            total += value
        return total

    total_sum = parallel_map(domain, kernel, reduce_in_order, options)
    print(f"[PAL Demo] sum of squares 0..9999 = {total_sum:.0f}")


if __name__ == "__main__":
    run_pal_demo()

