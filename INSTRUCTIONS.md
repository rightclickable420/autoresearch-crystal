# Autoresearch-Crystal: Setup & Run Guide

## What This Is

A fork of Karpathy's autoresearch that adds passive crystallization tracking to every training run. An AI coding agent autonomously modifies a transformer training script, runs 5-minute experiments, keeps improvements, discards regressions, and repeats. Every run automatically logs how attention heads crystallize during training — data that accumulates into a spectroscopy of training dynamics.

You optimize val_bpb. Crystallization data comes for free.

## What You Need

- NVIDIA GPU with CUDA (H100 ideal, others work)
- Python 3.10+
- `uv` package manager: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Claude Code (or Codex/similar coding agent) with API access

## Setup (10 minutes)

### 1. Clone

```bash
git clone https://github.com/rightclickable420/autoresearch-crystal.git
cd autoresearch-crystal
```

### 2. Prepare data

```bash
uv run prepare.py
```

Downloads data shards and trains a tokenizer. Stored in `~/.cache/autoresearch/`. Only needed once.

### 3. Test run

```bash
uv run train.py
```

Should complete in ~5 minutes and print results ending with:

```
---
val_bpb:          0.XXXXXX
...
crystal_pct:      XX.X
crystal_ordering: LX > LX > LX > ...
```

If you see `crystal_pct` and `crystal_ordering` in the output, everything is working.

## Running the Autonomous Loop

### Option A: Claude Code

```bash
claude "Read program.md and follow its instructions. \
  Start a new experiment run, then begin the loop."
```

When it asks for permissions, approve them (or use `--permission-mode bypassPermissions` to skip prompts).

### Option B: Any coding agent

Open your agent in the repo directory and tell it:

> Read program.md and follow the instructions. Set up a new experiment run, then begin the experiment loop.

### What happens next

The agent will:

1. Create a branch (e.g., `autoresearch/mar11`)
2. Run the baseline (unmodified `train.py`)
3. Modify `train.py` with an experiment (architecture change, hyperparameter tweak, etc.)
4. Run for 5 minutes, check val_bpb
5. If better → keep. If worse → discard and revert.
6. Repeat forever until you stop it.

**Each run takes ~5–6 minutes.** Overnight = ~80–90 experiments.

The agent only modifies `train.py`. It cannot touch `prepare.py` or the crystal tracker.

## Results & Reporting

**Results are reported automatically.** Every run sends its metrics (val_bpb, crystal fraction, layer ordering) to our server. You don't need to do anything — just let the loop run and we'll see the data as it comes in.

If you want to check results locally:

```bash
# All experiments (tab-separated)
cat results.tsv

# Crystal data across all runs
cat crystal_results.tsv

# Best runs
sort -t$'\t' -k2 -n results.tsv | head -5

# Detailed crystal log for last run
cat crystal_log.json | python3 -m json.tool
```

If the auto-reporting fails (firewall, network issues), it won't affect the experiments — the webhook is fire-and-forget. You can always send us the local files manually:

- `results.tsv` — experiment log
- `crystal_results.tsv` — crystal data

These files are .gitignored so they won't conflict with the agent's git operations.

## Troubleshooting

**OOM errors**: Reduce `DEVICE_BATCH_SIZE` in `train.py` (default 128). Try 64 or 32.

**Slow startup**: First run compiles CUDA kernels. Subsequent runs are faster.

**Agent stops**: The agent should run indefinitely. If it asks "should I continue?" — that's a bug in the agent, not the code. Tell it to keep going.

**Crystal tracking overhead**: The tracker samples 128 positions every 20 steps. If it's noticeably slowing runs, increase `SAMPLE_INTERVAL` in the `CrystalTracker` class (e.g., 50). Don't disable it.

## Questions?

Reach out to Ethan. Thanks for running these!
