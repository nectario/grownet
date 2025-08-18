#!/usr/bin/env python3
# apply_mojo_snake_case_patch.py
# --------------------------------
# Purpose:
#   Safely convert selected CamelCase method names to snake_case across your Mojo codebase
#   and align RegionMetrics field usage, without changing class/type names.
#
# Usage:
#   python3 apply_mojo_snake_case_patch.py --root /path/to/your/mojo/sources --apply
#   (omit --apply to see a dry-run diff summary)
#
# Notes:
#   * Creates .bak backups next to every modified file.
#   * Replacements are word-boundary anchored to avoid false positives.
#   * You can fine-tune the MAPPINGS list below if you need additional renames.

import argparse, re, os, sys, difflib

# ---- mappings (word-boundary anchored) ----
MAPPINGS = [
    ("\bgetName\b", "get_name"),
    ("\baddLayer\b", "add_layer"),
    ("\bconnectLayers\b", "connect_layers"),
    ("\bbindInput\b", "bind_input"),
    ("\bbindOutput\b", "bind_output"),
    ("\bpulseInhibition\b", "pulse_inhibition"),
    ("\bpulseModulation\b", "pulse_modulation"),
    ("\btickImage\b", "tick_image"),
    ("\bendTick\b", "end_tick"),
    ("\bonInput\b", "on_input"),
    ("\bonOutput\b", "on_output"),
    ("\bgetBus\b", "get_bus"),
    ("\bgetNeurons\b", "get_neurons"),
    ("\bgetOutgoing\b", "get_outgoing"),
    ("\bgetSlots\b", "get_slots"),
    # RegionMetrics field/call-site cleanup (if any direct field access is present)
    ("\bdeliveredEvents\b", "delivered_events"),
    ("\btotalSlots\b", "total_slots"),
    ("\btotalSynapses\b", "total_synapses"),
]

def rewrite_text(src: str) -> str:
    out = src
    for pat, repl in MAPPINGS:
        out = re.sub(pat, repl, out)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="Root directory containing .mojo sources")
    ap.add_argument("--apply", action="store_true", help="Apply changes (otherwise dry-run)")
    args = ap.parse_args()

    changed = []
    for dirpath, _, filenames in os.walk(args.root):
        for fn in filenames:
            if not fn.endswith(".mojo"):
                continue
            path = os.path.join(dirpath, fn)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    original = f.read()
            except Exception as e:
                print(f"Skipping {path}: {e}", file=sys.stderr)
                continue

            updated = rewrite_text(original)
            if updated != original:
                changed.append(path)
                if args.apply:
                    # write .bak and updated
                    with open(path + ".bak", "w", encoding="utf-8") as fb:
                        fb.write(original)
                    with open(path, "w", encoding="utf-8") as fw:
                        fw.write(updated)
                else:
                    # dry-run diff
                    diff = difflib.unified_diff(
                        original.splitlines(True),
                        updated.splitlines(True),
                        fromfile=path,
                        tofile=path + " (patched)",
                    )
                    sys.stdout.writelines(diff)

    if not changed:
        print("No changes detected.")
    else:
        if args.apply:
            print(f"Patched {len(changed)} files:")
            for p in changed:
                print("  -", p)
        else:
            print("\nDry-run complete. Re-run with --apply to write files.")

if __name__ == "__main__":
    main()
