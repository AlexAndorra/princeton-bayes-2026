"""Exploratory checks before modeling: ranges, overdispersion, missingness."""
import numpy as np
import pandas as pd

sessions = pd.read_csv("data/sessions.csv")
trials = pd.read_csv("data/trials.csv")

print("=== shape / missingness ===")
print("sessions:", sessions.shape, "nulls:", sessions.isnull().sum().sum())
print("trials:", trials.shape, "nulls:", trials.isnull().sum().sum())
print("participants:", sessions["participant"].nunique(), "sessions:", sorted(sessions["session"].unique()))
print("conditions:", sessions["condition"].unique())
print("n_trials unique:", sessions["n_trials"].unique())

print("\n=== parity check: sessions.csv n_correct vs trials.csv sum(correct) ===")
trial_agg = (
    trials.groupby(["participant", "session", "condition"])["correct"]
    .agg(["sum", "count"])
    .reset_index()
    .rename(columns={"sum": "n_correct_trials", "count": "n_trials_trials"})
)
merged = sessions.merge(trial_agg, on=["participant", "session", "condition"])
mismatch = merged[
    (merged["n_correct"] != merged["n_correct_trials"])
    | (merged["n_trials"] != merged["n_trials_trials"])
]
print("rows checked:", len(merged), "mismatches:", len(mismatch))

print("\n=== overall accuracy by condition ===")
overall = sessions.groupby("condition").agg(
    n_correct=("n_correct", "sum"), n_trials=("n_trials", "sum")
)
overall["acc"] = overall["n_correct"] / overall["n_trials"]
print(overall)

print("\n=== per-participant accuracy by condition (pooled over sessions) ===")
pp = sessions.groupby(["participant", "condition"]).agg(
    n_correct=("n_correct", "sum"), n_trials=("n_trials", "sum")
)
pp["acc"] = pp["n_correct"] / pp["n_trials"]
pp_wide = pp["acc"].unstack("condition")
print(pp_wide.describe())
print("\nparticipant-level range: standard", pp_wide["standard"].min(), "-", pp_wide["standard"].max())
print("participant-level range: hard", pp_wide["hard"].min(), "-", pp_wide["hard"].max())
print("\nmean(standard - hard) per participant:", (pp_wide["standard"] - pp_wide["hard"]).mean())
print("participants with hard >= standard:", (pp_wide["hard"] >= pp_wide["standard"]).sum(), "/", len(pp_wide))

print("\n=== overdispersion check: session-to-session variance vs binomial-expected ===")
sessions["p_hat"] = sessions["n_correct"] / sessions["n_trials"]
grp = sessions.groupby(["participant", "condition"])
obs_var = grp["p_hat"].var(ddof=1)
mean_p = grp["p_hat"].mean()
n = sessions["n_trials"].iloc[0]
binom_var = mean_p * (1 - mean_p) / n
ratio = obs_var / binom_var
print("median overdispersion ratio (obs var / binomial var):", ratio.median())
print("fraction of participant-conditions with ratio > 2:", (ratio > 2).mean())
print(ratio.describe())

print("\n=== is there a session/learning trend? ===")
by_session = sessions.groupby(["session", "condition"])["p_hat"].mean()
print(by_session)
