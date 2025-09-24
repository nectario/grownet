#!/usr/bin/env python3
# Placeholder for evaluation-only runs.
import json, sys, os
from forecast_card import make_forecast_card

def main():
    if len(sys.argv) < 3:
        print("usage: evaluate.py <metrics.json> <out_card.yaml> <dataset>")
        sys.exit(1)
    metrics_path, out_card, dataset = sys.argv[1], sys.argv[2], sys.argv[3]
    metrics = json.load(open(metrics_path))
    card = make_forecast_card(model_name="GrowNet-S (eval)", dataset=dataset, metrics=metrics)
    with open(out_card, "w") as f:
        f.write(card)
    print("wrote", out_card)

if __name__ == "__main__":
    main()
