
# NeurIPS 2025 Paper Skeleton — GrowNet

**Date:** August 09, 2025

This folder is an Overleaf-ready LaTeX skeleton that follows the NeurIPS 2025 Call for Papers rules.

## How to use
1) **Get the official NeurIPS 2025 style files** and drop them next to `main.tex` (e.g., `neurips_2025.sty`, `.bst` if provided). Do **not** enable `final` or `preprint` for anonymous submission.
2) Fill out the section files under `/sections` with real content.
3) Add your figures into `/figures` and update the file names in the figure includes.
4) Compile with `latexmk -pdf main.tex` (or Overleaf). Keep total content to **9 pages** (figures+tables included); references, checklist, and appendices do not count toward the 9.

## Figures (placeholders)
We included three placeholder PDFs in `/figures` that you can swap:
- `fig_system.pdf` — system block diagram
- `fig_slot_closeup.pdf` — per-neuron slots & thresholds
- `fig_tick_timeline.pdf` — two-phase tick

## Notes
- The NeurIPS Paper Checklist is required; the 2025 style file includes it. Keep it enabled.
- Use double-blind anonymization for submission.
