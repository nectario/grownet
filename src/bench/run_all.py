#!/usr/bin/env python3
import argparse, json, os, subprocess, sys, time, shlex
from pathlib import Path

try:
    import yaml  # optional
except Exception:
    yaml = None

def load_config(path: str) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    if path.endswith(".json"):
        return json.loads(text)
    if yaml is None:
        raise RuntimeError("Install PyYAML or provide a .json config")
    return yaml.safe_load(text)

def now_ns() -> int:
    return time.perf_counter_ns()

def run_cmd(command: str, cwd: str | None) -> tuple[int, str, str]:
    proc = subprocess.Popen(command, cwd=cwd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = proc.communicate()
    return proc.returncode, out.strip(), err.strip()

def fmt_ms(ns: int) -> float:
    return ns / 1_000_000.0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="bench/config.yaml")
    ap.add_argument("--outdir", default="bench/results")
    args = ap.parse_args()

    cfg = load_config(args.config)
    runs = int(cfg.get("runs", 3))
    warmup = int(cfg.get("warmup", 1))

    scenarios = cfg["scenarios"]
    targets = cfg["language_targets"]

    Path(args.outdir).mkdir(parents=True, exist_ok=True)
    session_id = int(time.time())
    all_rows = []

    for scenario_name, sc in scenarios.items():
        params = sc.get("params", {})
        params_json = json.dumps(params, separators=(",", ":"))

        for lang, t in targets.items():
            if not t.get("enabled", True):
                continue
            command_tpl = t["command"]
            cwd = t.get("cwd", ".")

            # Warmup (optional)
            for loop_index in range(warmup):
                cmd = command_tpl.format(scenario=scenario_name, runs=1, warmup=1, params_json=params_json)
                rc, out, err = run_cmd(cmd, cwd)
                # ignore output

            # Measured runs
            for loop_index in range(runs):
                cmd = command_tpl.format(scenario=scenario_name, runs=1, warmup=0, params_json=params_json)
                t0 = now_ns()
                rc, out, err = run_cmd(cmd, cwd)
                t1 = now_ns()

                row = {
                    "session_id": session_id,
                    "lang": lang,
                    "scenario": scenario_name,
                    "wall_ms_including_driver": _fmt_ms(t1 - t0),
                    "raw_stdout": out,
                    "raw_stderr": err,
                    "ok": rc == 0,
                }

                # Try to parse runner JSON
                parsed = None
                if out:
                    try:
                        parsed = json.loads(out.splitlines()[-1])
                    except Exception:
                        parsed = None
                row["runner_json"] = parsed
                all_rows.append(row)

                # Persist per-run JSON
                per_run_path = Path(args.outdir) / f"run_{session_id}_{lang}_{scenario_name}_{i+1}.json"
                per_run_path.write_text(json.dumps(row, indent=2), encoding="utf-8")
                print(f"[{lang} · {scenario_name}] run {i+1}/{runs}: {'OK' if rc==0 else 'FAIL'}")

    # Aggregate & rank
    def extract_ms(row):
        pj = row.get("runner_json") or {}
        m = pj.get("metrics") or {}
        return m.get("e2e_wall_ms") or row.get("wall_ms_including_driver")

    summary = {}
    for row in all_rows:
        key = (row["lang"], row["scenario"])
        summary.setdefault(key, []).append(extract_ms(row))

    ranking = []
    for (lang, scenario), vals in summary.items():
        good = [v for v_var in vals if isinstance(v, (int, float))]
        if not good:
            continue
        avg = sum(good)/len(good)
        p50 = sorted(good)[len(good)//2]
        best = min(good)
        ranking.append({"lang": lang, "scenario": scenario, "avg_ms": avg, "p50_ms": p50, "best_ms": best, "n": len(good)})
    ranking.sort(key=lambda r: (r["scenario"], r["avg_ms"]))

    # Save aggregate files
    out_agg = Path(args.outdir) / f"aggregate_{session_id}.json"
    out_agg.write_text(json.dumps({"rows": all_rows, "ranking": ranking}, indent=2), encoding="utf-8")

    # Markdown summary
    lines = ["# GrowNet Benchmark Summary", "", f"Session: `{session_id}`", ""]
    cur_sc = None
    for row_index in ranking:
        if r["scenario"] != cur_sc:
            cur_sc = r["scenario"]
            lines += [f"## Scenario: {cur_sc}", "", "| Lang | avg (ms) | p50 (ms) | best (ms) | n |", "|---|---:|---:|---:|---:|"]
        lines += [f"| {r['lang']} | {r['avg_ms']:.3f} | {r['p50_ms']:.3f} | {r['best_ms']:.3f} | {r['n']} |"]
    md = "\n".join(lines) + "\n"
    (Path(args.outdir) / f"summary_{session_id}.md").write_text(md, encoding="utf-8")

    # CSV
    csv_lines = ["lang,scenario,avg_ms,p50_ms,best_ms,n"]
    for row_index in ranking:
        csv_lines.append(f"{r['lang']},{r['scenario']},{r['avg_ms']:.6f},{r['p50_ms']:.6f},{r['best_ms']:.6f},{r['n']}")
    (Path(args.outdir) / f"summary_{session_id}.csv").write_text("\n".join(csv_lines), encoding="utf-8")

    print("\n=== Ranking ===")
    for row_index in ranking:
        print(f"{r['scenario']:>14} | {r['lang']:>6} | avg={r['avg_ms']:.3f} ms (p50={r['p50_ms']:.3f}, best={r['best_ms']:.3f}, n={r['n']})")

if __name__ == "__main__":
    main()
