# autoresearch-crystal

Fork of [karpathy/autoresearch](https://github.com/karpathy/autoresearch) with passive crystallization tracking.

## What's Added

Every training run automatically tracks per-head attention entropy and logs crystallization dynamics:
- **crystal_pct**: aggregate percentage of attention heads that have crystallized
- **crystal_ordering**: which layers crystallize first (e.g., `L0 > L3 > L2 > L4 > L5 > L1`)
- **per_layer**: detailed crystal fraction per layer

The tracking is passive — it observes entropy through a lightweight manual attention computation on a small sample of positions. It does not modify gradients or training dynamics.

## Why

We discovered that transformer attention heads naturally self-partition into "crystallized" (fixed-pattern) and "fluid" (variable-pattern) populations during standard training. The crystal fraction and layer ordering vary by architecture and dataset — functioning as a zero-cost spectroscopy of training dynamics.

By adding crystal tracking to autoresearch's autonomous experiment loop, every 5-minute run contributes a data point to the spectroscopy space. Hundreds of runs map the relationship between architecture choices, val_bpb, and crystallization patterns.

## Output

Each run produces:
- Standard autoresearch output (val_bpb, training stats)  
- `crystal_log.json` — detailed per-step crystal measurements for this run
- `crystal_results.tsv` — cumulative one-line-per-run crystal summary (persists across runs)

## Usage

Same as autoresearch:
```bash
uv run prepare.py  # one-time data prep
uv run train.py    # 5-minute training run with crystal tracking
```

## Reference

Gill, E. & Ash, K. (2026). "Crystallizing Attention: Natural Self-Partitioning of Attention Heads During Transformer Training."
