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

## Getting Started

### Requirements

- **GPU**: NVIDIA GPU with CUDA support (H100 recommended, others should work)
- **Python**: 3.10+
- **uv**: Python package manager ([install](https://docs.astral.sh/uv/getting-started/installation/))
- **Claude Code** or **Codex**: AI coding agent for the autonomous loop

### Step 1: Clone and prep data

```bash
git clone https://github.com/rightclickable420/autoresearch-crystal.git
cd autoresearch-crystal
uv run prepare.py
```

This downloads data shards and trains a BPE tokenizer. Data is stored in `~/.cache/autoresearch/`. Takes a few minutes on first run.

### Step 2: Verify with a baseline run

```bash
uv run train.py
```

This runs a single 5-minute training session. You should see output ending with:

```
---
val_bpb:          X.XXXXXX
training_seconds: 300.X
...
crystal_pct:      XX.X
crystal_ordering: LX > LX > LX > ...
```

If this works, you're ready for autonomous runs.

### Step 3: Set up the autonomous loop

The autonomous loop uses an AI coding agent (Claude Code or Codex) running with `program.md` as its instructions. The agent modifies `train.py`, runs for 5 minutes, checks if val_bpb improved, keeps or discards the change, and repeats indefinitely.

**With Claude Code:**

```bash
claude --print --permission-mode bypassPermissions \
  "Read program.md and follow the instructions. Set up a new experiment run, then begin the experiment loop."
```

**With Codex (or similar):**

Open your coding agent in the repo directory and paste:

> Read program.md and follow the instructions. Set up a new experiment run, then begin the experiment loop.

The agent will:
1. Create a branch (`autoresearch/<tag>`)
2. Run the baseline
3. Start modifying `train.py` and testing changes
4. Keep improvements, discard regressions
5. Loop indefinitely until you stop it

### Step 4: Let it run

Each experiment takes ~5–6 minutes (5 min training + startup/eval). Overnight (~8 hours) produces ~80–90 experiments. You can leave it running as long as you like.

### Step 5: Check results

When you come back:

```bash
# See all experiments
cat results.tsv

# See crystallization data across all runs
cat crystal_results.tsv

# Best val_bpb achieved
sort -t$'\t' -k2 -n results.tsv | head -5

# Crystal data for a specific run
cat crystal_log.json | python3 -m json.tool
```

The key files:
- `results.tsv` — one row per experiment (val_bpb, crystal_pct, crystal_ordering, status, description)
- `crystal_results.tsv` — cumulative crystal data across all runs
- `crystal_log.json` — detailed per-step crystal measurements for the most recent run
- `run.log` — full output of the most recent run

## Output Format

Each run appends to `crystal_results.tsv`:

| steps | val_bpb | crystal_pct | ordering | per_layer |
|-------|---------|-------------|----------|-----------|
| 953 | 0.997900 | 43.2 | L0 > L3 > L2 > L4 > L5 > L1 | [64.1, 10.2, 55.8, 55.1, 47.3, 27.0] |

And the agent logs to `results.tsv`:

| commit | val_bpb | memory_gb | crystal_pct | crystal_ordering | status | description |
|--------|---------|-----------|-------------|------------------|--------|-------------|
| a1b2c3d | 0.997900 | 44.0 | 43.2 | L0 > L3 > ... | keep | baseline |

## What We're Looking For

As experiments accumulate, interesting patterns may emerge:

- **Does crystal fraction correlate with val_bpb?** (lower crystal = better generalization?)
- **Does layer ordering change with architecture?** (more layers → different ordering?)
- **Is there a natural ceiling?** (we observed ~43% on small models — does it hold at scale?)
- **Does the ordering match our small-model findings?** (input-first in ungated, middle-out with gating)

You don't need to optimize for crystal metrics — they're observational. Just let the agent optimize val_bpb and the crystal data accumulates as a side effect.

## Reference

Gill, E. & Ash, K. (2026). "Crystallizing Attention: Natural Self-Partitioning of Attention Heads During Transformer Training."
