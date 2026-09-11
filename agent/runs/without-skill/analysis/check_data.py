"""Data-integrity checks, run before any modeling.

Verifies that sessions.csv (the aggregated counts we model) is consistent
with trials.csv (the raw trial-level records), and that the design is what
the codebook claims. A silent mismatch here (e.g. wrong participant/condition
alignment, double-counted trials) would corrupt every downstream estimate
without ever raising an error, so we check it explicitly and cheaply before
paying for MCMC.
"""

import pandas as pd

sessions = pd.read_csv("data/sessions.csv")
trials = pd.read_csv("data/trials.csv")

# --- shape / codebook checks ---
assert set(sessions["participant"]) == set(range(1, 41)), "expected participants 1..40"
assert set(sessions["session"]) == {1, 2, 3, 4, 5}, "expected sessions 1..5"
assert set(sessions["condition"]) == {"standard", "hard"}, "unexpected condition labels"
assert len(sessions) == 40 * 5 * 2, "expected one row per participant x session x condition"
assert (sessions["n_trials"] == 100).all(), "expected 100 trials per row"
assert sessions["n_correct"].between(0, 100).all(), "n_correct out of range"

assert set(trials["participant"]) == set(range(1, 41))
assert set(trials["session"]) == {1, 2, 3, 4, 5}
assert set(trials["condition"]) == {"standard", "hard"}
assert set(trials["correct"].unique()) <= {0, 1}
assert len(trials) == 40 * 5 * 2 * 100, "expected 100 trials per participant x session x condition"

# --- sessions.csv must be the exact aggregate of trials.csv ---
trial_agg = (
    trials.groupby(["participant", "session", "condition"])
    .agg(n_trials=("correct", "size"), n_correct=("correct", "sum"))
    .reset_index()
)
merged = sessions.merge(
    trial_agg, on=["participant", "session", "condition"], suffixes=("_sessions", "_trials")
)
assert len(merged) == len(sessions), "row mismatch between sessions.csv and trials.csv aggregate"
assert (merged["n_trials_sessions"] == merged["n_trials_trials"]).all(), "n_trials mismatch"
assert (merged["n_correct_sessions"] == merged["n_correct_trials"]).all(), (
    "n_correct mismatch between sessions.csv and trials.csv -- aggregation bug"
)

# --- per-participant-condition total trials, used by the Part 1 CI script ---
per_pc = sessions.groupby(["participant", "condition"])["n_trials"].sum()
assert (per_pc == 500).all(), "expected 500 trials per participant per condition (5 sessions x 100)"

print("OK: sessions.csv matches trials.csv exactly; design matches codebook.")
print(f"  {sessions['participant'].nunique()} participants, "
      f"{sessions['session'].nunique()} sessions, "
      f"{sessions['condition'].nunique()} conditions, "
      f"{len(sessions)} session-condition rows, {len(trials)} trials.")
