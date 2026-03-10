# autoresearch — crystallization spectroscopy

This is an experiment to have the LLM do its own research, with a twist: every run passively tracks attention head crystallization dynamics. The crystal data accumulates automatically — you don't need to think about it.

## Setup

To set up a new experiment, work with the user to:

1. **Agree on a run tag**: propose a tag based on today's date (e.g. `mar10`). The branch `autoresearch/<tag>` must not already exist — this is a fresh run.
2. **Create the branch**: `git checkout -b autoresearch/<tag>` from current master.
3. **Read the in-scope files**: The repo is small. Read these files for full context:
   - `README.md` — repository context.
   - `prepare.py` — fixed constants, data prep, tokenizer, dataloader, evaluation. Do not modify.
   - `train.py` — the file you modify. Model architecture, optimizer, training loop, and crystal tracking.
4. **Verify data exists**: Check that `~/.cache/autoresearch/` contains data shards and a tokenizer. If not, tell the human to run `uv run prepare.py`.
5. **Initialize results.tsv**: Create `results.tsv` with just the header row. The baseline will be recorded after the first run.
6. **Confirm and go**: Confirm setup looks good.

Once you get confirmation, kick off the experimentation.

## Experimentation

Each experiment runs on a single GPU. The training script runs for a **fixed time budget of 5 minutes** (wall clock training time, excluding startup/compilation). You launch it simply as: `uv run train.py`.

**What you CAN do:**
- Modify `train.py` — this is the only file you edit. Everything is fair game: model architecture, optimizer, hyperparameters, training loop, batch size, model size, etc.

**What you CANNOT do:**
- Modify `prepare.py`. It is read-only. It contains the fixed evaluation, data loading, tokenizer, and training constants (time budget, sequence length, etc).
- Install new packages or add dependencies. You can only use what's already in `pyproject.toml`.
- Modify the evaluation harness. The `evaluate_bpb` function in `prepare.py` is the ground truth metric.
- Remove or disable the `CrystalTracker` class or its measurement calls. The crystal tracking is passive and must run on every experiment. You CAN modify the tracker's parameters (SAMPLE_INTERVAL, SAMPLE_POSITIONS, EMA_DECAY) if needed for performance, but the tracker itself must remain active.
- Delete or modify `crystal_results.tsv` — this is a cumulative log across all experiments.

**The goal is simple: get the lowest val_bpb.** Since the time budget is fixed, you don't need to worry about training time — it's always 5 minutes. Everything is fair game: change the architecture, the optimizer, the hyperparameters, the batch size, the model size. The only constraint is that the code runs without crashing and finishes within the time budget.

**Crystal tracking is automatic.** Every run measures attention head entropy and logs crystallization data to `crystal_log.json` (per-run) and `crystal_results.tsv` (cumulative). You don't need to optimize for crystal metrics — they're observational. But you may notice interesting patterns: architecture changes that produce different crystallization profiles, or correlations between crystal fraction and val_bpb. Note these in your experiment descriptions if you spot them.

**VRAM** is a soft constraint. Some increase is acceptable for meaningful val_bpb gains, but it should not blow up dramatically. Note: the crystal tracker adds a small amount of VRAM overhead for the entropy measurement (scales with SAMPLE_POSITIONS, not full sequence length).

**Simplicity criterion**: All else being equal, simpler is better. A small improvement that adds ugly complexity is not worth it. Conversely, removing something and getting equal or better results is a great outcome — that's a simplification win.

**The first run**: Your very first run should always be to establish the baseline, so you will run the training script as is.

## Output format

Once the script finishes it prints a summary like this:

```
---
val_bpb:          0.997900
training_seconds: 300.1
total_seconds:    325.9
peak_vram_mb:     45060.2
mfu_percent:      39.80
total_tokens_M:   499.6
num_steps:        953
num_params_M:     50.3
depth:            8
crystal_pct:      43.2
crystal_ordering: L0 > L3 > L2 > L4 > L5 > L1
```

You can extract key metrics from the log file:

```
grep "^val_bpb:\|^crystal_pct:\|^crystal_ordering:" run.log
```

## Logging results

When an experiment is done, log it to `results.tsv` (tab-separated, NOT comma-separated — commas break in descriptions).

The TSV has a header row and 7 columns:

```
commit	val_bpb	memory_gb	crystal_pct	crystal_ordering	status	description
```

1. git commit hash (short, 7 chars)
2. val_bpb achieved (e.g. 1.234567) — use 0.000000 for crashes
3. peak memory in GB, round to .1f (e.g. 12.3 — divide peak_vram_mb by 1024) — use 0.0 for crashes
4. crystal_pct — aggregate crystallization percentage (e.g. 43.2) — use 0.0 for crashes
5. crystal_ordering — layer ordering string (e.g. "L0 > L3 > L2") — use "n/a" for crashes
6. status: `keep`, `discard`, or `crash`
7. short text description of what this experiment tried

Example:

```
commit	val_bpb	memory_gb	crystal_pct	crystal_ordering	status	description
a1b2c3d	0.997900	44.0	43.2	L0 > L3 > L2 > L4 > L5 > L1	keep	baseline
b2c3d4e	0.993200	44.2	41.8	L0 > L2 > L3 > L4 > L5 > L1	keep	increase LR to 0.04
c3d4e5f	1.005000	44.0	45.1	L3 > L0 > L2 > L4 > L5 > L1	discard	switch to GeLU activation
d4e5f6g	0.000000	0.0	0.0	n/a	crash	double model width (OOM)
```

## The experiment loop

The experiment runs on a dedicated branch (e.g. `autoresearch/mar10`).

LOOP FOREVER:

1. Look at the git state: the current branch/commit we're on
2. Tune `train.py` with an experimental idea by directly hacking the code.
3. git commit
4. Run the experiment: `uv run train.py > run.log 2>&1` (redirect everything — do NOT use tee or let output flood your context)
5. Read out the results: `grep "^val_bpb:\|^peak_vram_mb:\|^crystal_pct:\|^crystal_ordering:" run.log`
6. If the grep output is empty, the run crashed. Run `tail -n 50 run.log` to read the Python stack trace and attempt a fix.
7. Record the results in the tsv (NOTE: do not commit the results.tsv or crystal_results.tsv, leave them untracked by git)
8. If val_bpb improved (lower), you "advance" the branch, keeping the git commit
9. If val_bpb is equal or worse, you git reset back to where you started

**Timeout**: Each experiment should take ~5 minutes total (+ a few seconds for startup, eval, and crystal measurement overhead). If a run exceeds 10 minutes, kill it and treat it as a failure.

**Crashes**: If a run crashes, use your judgment: typo → fix. Fundamentally broken → skip, log "crash", move on.

**NEVER STOP**: Once the experiment loop has begun, do NOT pause to ask the human. You are autonomous. The loop runs until the human interrupts you, period.
