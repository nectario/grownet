# Utility to emit a simple Forecast Card YAML string
def make_forecast_card(model_name, dataset, metrics):
    lines = []
    lines.append("version: 1")
    lines.append(f"model_name: {model_name}")
    lines.append("model_version: 0.1")
    lines.append(f"task: {dataset}")
    lines.append("metrics:")
    for k,v in metrics.items():
        lines.append(f"  {k}: {v}")
    return "\n".join(lines) + "\n"
