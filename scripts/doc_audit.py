import os, re, json, difflib, pathlib, time

REPO = pathlib.Path(__file__).resolve().parents[1]
DOCS = REPO / "docs"
READ_ORDER = DOCS / "READ_ORDER.md"

def read(p): return p.read_text(encoding="utf-8", errors="ignore")
def md_files():
    out=[]
    for root,_,files in os.walk(DOCS):
        for f in files:
            if f.lower().endswith(".md"):
                out.append(pathlib.Path(root)/f)
    return out

# 1) Parse READ_ORDER
refs=set()
if READ_ORDER.exists():
    for line in read(READ_ORDER).splitlines():
        for m in re.finditer(r'`?([A-Za-z0-9_\-./]+\.md)`?', line):
            ref = m.group(1).replace("docs/","")
            refs.add(ref)

ref_paths = {DOCS / r for r in refs}
missing_refs = [r for r in sorted(refs) if not (DOCS / r).exists()]

# Docs not in READ_ORDER yet
all_md = md_files()
not_in_order = [str(p.relative_to(REPO)) for p in all_md if p not in ref_paths and p.name.lower()!="read_order.md"]

# 2) Divergence checks
patterns = {
    "connect_layers_windowed_mentions": r"connect_layers_windowed",
    "windowed_return_unique_sources": r"unique source(s)?|unique sources|unique source count",
    "center_rule_terms": r"\b(center rule|SAME|VALID|floor|clamp)\b",
    "freeze_unfreeze": r"freeze_last_slot|unfreeze_last_slot|prefer.*once",
    "neuron_growth_trigger": r"fallback_growth_threshold|neuron_growth_cooldown_ticks|fallback streak",
    "region_growth_trigger": r"avg_slots_threshold|percentAtCapFallback|percent_at_cap_fallback",
    "one_growth_per_region": r"one growth per region per tick",
    "pal_determinism": r"ordered reduction|deterministic|stable tiling",
    "ts_layer_growth": r"one growth per layer per tick|percentAtCapFallbackThreshold",
    "mojo_copy_model": r"\.copy\(|\blet\b|iterators.*reference|ImplicitlyCopyable|Copyable",
    "bus_decay": r"inhibition.*decay|modulation.*1\.0|current_step"
}
hits = {k: [] for k in patterns}
contradictions = []

for p in all_md:
    text = read(p)
    rel = str(p.relative_to(DOCS))
    for key, pat in patterns.items():
        if re.search(pat, text, flags=re.IGNORECASE|re.DOTALL):
            hits[key].append(rel)
    if re.search(patterns["connect_layers_windowed_mentions"], text, re.I) and not re.search(patterns["windowed_return_unique_sources"], text, re.I):
        if "changelog" not in rel.lower() and "/prs/" not in rel.lower():
            contradictions.append(rel)

# 3) Suggested READ_ORDER patch (append missing docs)
orig = read(READ_ORDER) if READ_ORDER.exists() else ""
updated = (orig + "\n\n## Missing docs found (suggested to include)\n\n" +
           "\n".join(f"- `docs/{pathlib.Path(p).relative_to('docs')}`"
                     for p in sorted(not_in_order) if p.startswith("docs/"))) if orig else "# READ_ORDER (new)\n"
diff = "\n".join(difflib.unified_diff(orig.splitlines(), updated.splitlines(),
                                      fromfile="a/docs/READ_ORDER.md",
                                      tofile="b/docs/READ_ORDER.md", lineterm=""))

out_dir = REPO / "tools" / "doc_audit_out"
out_dir.mkdir(parents=True, exist_ok=True)
(out_dir/"docs_divergence_report.json").write_text(json.dumps({
    "generated_on": time.strftime("%Y-%m-%d %H:%M:%S"),
    "missing_refs_in_read_order": missing_refs,
    "docs_not_in_read_order": sorted(not_in_order),
    "contradictions_windowed_return": sorted(contradictions),
    "search_hits": {k: sorted(v) for k,v in hits.items()}
}, indent=2), encoding="utf-8")
(out_dir/"READ_ORDER.suggested.patch.diff").write_text(diff or "# New file", encoding="utf-8")
print("Audit complete. See tools/doc_audit_out/")
