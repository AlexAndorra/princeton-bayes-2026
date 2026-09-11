"""Part 1: each participant's accuracy per condition, with a 95% credible interval.

Pools each participant's 5 sessions per condition (500 trials) and computes an
exact Bayesian credible interval via Beta-Binomial conjugacy with a Jeffreys
prior, Beta(0.5, 0.5) -- a standard non-informative choice for a binomial rate
that avoids the boundary issues of a flat Beta(1, 1) prior. This is a closed-form
posterior, so no MCMC is needed here (that comes in Part 2, where the
repeated-measures structure across participants actually matters).
"""

import pandas as pd
from scipy.stats import beta as beta_dist

sessions = pd.read_csv("data/sessions.csv")

agg = (
    sessions.groupby(["participant", "condition"])
    .agg(n_trials=("n_trials", "sum"), n_correct=("n_correct", "sum"))
    .reset_index()
)

PRIOR_A, PRIOR_B = 0.5, 0.5  # Jeffreys prior on a binomial rate
post_a = PRIOR_A + agg["n_correct"]
post_b = PRIOR_B + (agg["n_trials"] - agg["n_correct"])

agg["accuracy"] = agg["n_correct"] / agg["n_trials"]
agg["posterior_mean"] = post_a / (post_a + post_b)
agg["ci95_low"] = beta_dist.ppf(0.025, post_a, post_b)
agg["ci95_high"] = beta_dist.ppf(0.975, post_a, post_b)

agg = agg.sort_values(["participant", "condition"]).reset_index(drop=True)
agg.to_csv("analysis/participant_accuracy.csv", index=False)

print(agg.head(10).to_string(index=False))
print(f"\nSaved {len(agg)} rows (40 participants x 2 conditions) to analysis/participant_accuracy.csv")
print(f"\nOverall mean accuracy: standard={agg.loc[agg.condition=='standard','accuracy'].mean():.3f}, "
      f"hard={agg.loc[agg.condition=='hard','accuracy'].mean():.3f}")
print(f"Median 95% CI half-width: {((agg.ci95_high - agg.ci95_low) / 2).median():.3f}")
