"""Per-participant accuracy summaries (95% HDI) and the population condition
effect, translated to the accuracy scale, for the lab-meeting report."""
import numpy as np
import pandas as pd
import arviz as az
import xarray as xr

RESULTS_DIR = "accuracy-hierarchical"
idata = az.from_netcdf(f"{RESULTS_DIR}/inference_data.nc")
post = idata.posterior

participants = post["participant"].values

# Per-participant, per-condition accuracy on the probability scale.
# invlogit(alpha) = standard-condition accuracy; invlogit(alpha+beta) = hard.
p_standard = xr.apply_ufunc(lambda x: 1 / (1 + np.exp(-x)), post["alpha"])
p_hard = xr.apply_ufunc(lambda x: 1 / (1 + np.exp(-x)), post["alpha"] + post["beta"])

rows = []
for i, pid in enumerate(participants):
    for label, arr in [("standard", p_standard), ("hard", p_hard)]:
        draws = arr.isel(participant=i)
        mean = float(draws.mean())
        hdi = az.hdi(draws, prob=0.95)
        lo, hi = float(hdi.sel(ci_bound="lower")), float(hdi.sel(ci_bound="upper"))
        rows.append({"participant": int(pid), "condition": label, "accuracy_mean": mean, "hdi_2.5%": lo, "hdi_97.5%": hi})

participant_df = pd.DataFrame(rows)
participant_df.to_csv(f"{RESULTS_DIR}/participant_accuracy.csv", index=False)
print(participant_df.head(10))

# Population-level condition effect, on both logit and accuracy scales.
mu_alpha = post["mu_alpha"]
mu_beta = post["mu_beta"]
pop_standard = xr.apply_ufunc(lambda x: 1 / (1 + np.exp(-x)), mu_alpha)
pop_hard = xr.apply_ufunc(lambda x: 1 / (1 + np.exp(-x)), mu_alpha + mu_beta)
pop_diff = pop_standard - pop_hard  # accuracy points lost in hard condition

print("\n=== Population-level condition effect ===")
print("mu_beta (logit scale) mean:", float(mu_beta.mean()), "94% HDI:", az.hdi(mu_beta, prob=0.94).values)
print("P(mu_beta < 0):", float((mu_beta < 0).mean()))
print("Population standard accuracy: mean", float(pop_standard.mean()), "95% HDI", az.hdi(pop_standard, prob=0.95).values)
print("Population hard accuracy: mean", float(pop_hard.mean()), "95% HDI", az.hdi(pop_hard, prob=0.95).values)
print("Population accuracy-point difference (standard - hard): mean", float(pop_diff.mean()), "95% HDI", az.hdi(pop_diff, prob=0.95).values)
print("P(standard accuracy > hard accuracy):", float((pop_diff > 0).mean()))

# Per-participant difference, to report how consistent the effect is.
diff_i = p_standard - p_hard
diff_mean_per_participant = diff_i.mean(dim=["chain", "draw"])
print("\nParticipants where P(standard > hard) > 0.95:",
      int((diff_i.mean(dim=["chain", "draw"]) > 0).sum()), "/", len(participants))

summary_stats = {
    "mu_beta_mean": float(mu_beta.mean()),
    "mu_beta_hdi94": [float(x) for x in az.hdi(mu_beta, prob=0.94).values],
    "P_mu_beta_lt_0": float((mu_beta < 0).mean()),
    "pop_standard_mean": float(pop_standard.mean()),
    "pop_standard_hdi95": [float(x) for x in az.hdi(pop_standard, prob=0.95).values],
    "pop_hard_mean": float(pop_hard.mean()),
    "pop_hard_hdi95": [float(x) for x in az.hdi(pop_hard, prob=0.95).values],
    "pop_diff_mean": float(pop_diff.mean()),
    "pop_diff_hdi95": [float(x) for x in az.hdi(pop_diff, prob=0.95).values],
}
import json
with open(f"{RESULTS_DIR}/population_effect.json", "w") as f:
    json.dump(summary_stats, f, indent=2)
print("\nSaved:", f"{RESULTS_DIR}/population_effect.json", f"{RESULTS_DIR}/participant_accuracy.csv")
