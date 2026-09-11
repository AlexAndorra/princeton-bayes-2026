"""Part 2: does accuracy differ between conditions, accounting for repeated measures?

Generative story: each participant has their own baseline accuracy and their own
sensitivity to the "hard" condition (both correlated, since a participant who
starts stronger might also drop more or less under difficulty). We partially pool
these participant-level intercepts and condition-slopes toward population-level
means. The population-level slope (mu_slope) is "does accuracy differ between
conditions, on average, once we account for who's doing the task and that each
participant contributes 5 repeated sessions per condition" -- fitting this
directly avoids the pseudo-replication of e.g. treating all 200 hard-condition
session-rows as independent observations.

n_correct[i] ~ Binomial(n=100, p=invlogit(alpha[participant[i]] + beta[participant[i]] * condition[i]))
alpha, beta ~ correlated Normal across participants (partial pooling, LKJ prior on the correlation)
"""

import json

import arviz as az
import arviz_plots as azp
import arviz_stats as azs
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pymc as pm

RANDOM_SEED = sum(map(ord, "repeated-measures-accuracy-condition-effect"))
rng = np.random.default_rng(RANDOM_SEED)

sessions = pd.read_csv("data/sessions.csv")
participants = sorted(sessions["participant"].unique())
participant_map = {p: i for i, p in enumerate(participants)}
condition_map = {"standard": 0, "hard": 1}  # standard is the reference level

participant_idx = sessions["participant"].map(participant_map).to_numpy()
condition_idx = sessions["condition"].map(condition_map).to_numpy()

coords = {"participant": participants, "param": ["intercept", "condition_slope"]}

with pm.Model(coords=coords) as model:
    n_trials_data = pm.Data("n_trials", sessions["n_trials"].to_numpy(), dims="obs")
    condition_data = pm.Data("condition_idx", condition_idx, dims="obs")
    participant_data = pm.Data("participant_idx", participant_idx, dims="obs")

    # Weakly informative: logit(0.73) = 1.0 is a plausible center for an accuracy
    # task; sigma=1 lets the 95% prior range span roughly 12%-99% accuracy.
    mu_intercept = pm.Normal("mu_intercept", mu=1.0, sigma=1.0)
    # No assumed direction for the condition effect a priori.
    mu_slope = pm.Normal("mu_slope", mu=0.0, sigma=1.0)

    chol, corr, stds = pm.LKJCholeskyCov(
        "chol", n=2, eta=2.0, sd_dist=pm.Exponential.dist(1.0)
    )
    effects = pm.MvNormal(
        "effects", mu=pm.math.stack([mu_intercept, mu_slope]), chol=chol,
        dims=("participant", "param"),
    )
    alpha = pm.Deterministic("alpha", effects[:, 0], dims="participant")
    beta = pm.Deterministic("beta", effects[:, 1], dims="participant")

    logit_p = alpha[participant_data] + beta[participant_data] * condition_data
    p = pm.Deterministic("p", pm.math.invlogit(logit_p), dims="obs")

    pm.Binomial(
        "n_correct", n=n_trials_data, p=p,
        observed=sessions["n_correct"].to_numpy(), dims="obs",
    )

    # --- Prior predictive check ---
    prior_pred = pm.sample_prior_predictive(draws=500, random_seed=rng)
    prior_acc = (prior_pred.prior_predictive["n_correct"] / 100).to_numpy().ravel()
    obs_acc = (sessions["n_correct"] / sessions["n_trials"]).to_numpy()
    print(f"Prior predictive accuracy range: [{prior_acc.min():.3f}, {prior_acc.max():.3f}], "
          f"mean={prior_acc.mean():.3f}, std={prior_acc.std():.3f}")
    print(f"Observed accuracy range: [{obs_acc.min():.3f}, {obs_acc.max():.3f}]")
    # Plausibility: priors must not rule out the observed accuracy range, and
    # must not be so wide that a near-uniform [0,1] spread makes them uninformative.
    assert prior_acc.min() < obs_acc.min() and prior_acc.max() > obs_acc.max(), (
        "prior predictive range does not cover the observed accuracy range"
    )
    assert prior_acc.std() < 0.30, "prior predictive is implausibly diffuse (near-uniform)"

    # --- Inference ---
    idata = pm.sample(nuts_sampler="nutpie", random_seed=rng)
    idata.update(prior_pred)

    # --- Posterior predictive check ---
    idata.update(pm.sample_posterior_predictive(idata, random_seed=rng))

    # --- log-likelihood / log-prior for sensitivity checks ---
    pm.compute_log_likelihood(idata, model=model)
    pm.stats.compute_log_prior(idata, model=model)

# --- Save immediately after sampling ---
# No netCDF backend (netCDF4/h5netcdf) is installed in this env, but zarr is.
idata.to_zarr("analysis/inference_data.zarr", mode="w")

# --- Convergence diagnostics ---
problems_detected = azs.diagnose(idata)  # also prints a human-readable report
summary = az.summary(
    idata, var_names=["mu_intercept", "mu_slope", "chol_stds", "chol_corr"],
    ci_prob=0.95, ci_kind="hdi",
)
print("\n", summary)
key_summary = summary.loc[["mu_intercept", "mu_slope"]]
n_divergences = int(idata.sample_stats["diverging"].sum())
rhat_max = float(key_summary["r_hat"].max())
ess_min = float(key_summary["ess_bulk"].min())
n_chains = idata.posterior.sizes["chain"]

# --- Posterior predictive / calibration check ---
# kind="ecdf" avoids the KDE-on-discrete-counts warning for Binomial(100, p) data.
pc = azp.plot_ppc_dist(idata, kind="ecdf")
pc.savefig("analysis/ppc_check.png")
plt.close("all")

# --- Prior sensitivity check ---
psense = azs.psense_summary(idata, var_names=["mu_intercept", "mu_slope"])
print("\nPrior sensitivity:\n", psense)

# --- Light robustness check: refit with a deliberately wider prior on mu_slope ---
with pm.Model(coords=coords) as model_wide:
    n_trials_data = pm.Data("n_trials", sessions["n_trials"].to_numpy(), dims="obs")
    condition_data = pm.Data("condition_idx", condition_idx, dims="obs")
    participant_data = pm.Data("participant_idx", participant_idx, dims="obs")

    mu_intercept_w = pm.Normal("mu_intercept", mu=1.0, sigma=2.0)
    mu_slope_w = pm.Normal("mu_slope", mu=0.0, sigma=3.0)  # 3x wider than main model

    chol_w, _, _ = pm.LKJCholeskyCov("chol", n=2, eta=2.0, sd_dist=pm.Exponential.dist(1.0))
    effects_w = pm.MvNormal(
        "effects", mu=pm.math.stack([mu_intercept_w, mu_slope_w]), chol=chol_w,
        dims=("participant", "param"),
    )
    alpha_w = effects_w[:, 0]
    beta_w = effects_w[:, 1]
    logit_p_w = alpha_w[participant_data] + beta_w[participant_data] * condition_data
    p_w = pm.Deterministic("p", pm.math.invlogit(logit_p_w), dims="obs")
    pm.Binomial("n_correct", n=n_trials_data, p=p_w, observed=sessions["n_correct"].to_numpy(), dims="obs")

    idata_wide = pm.sample(nuts_sampler="nutpie", random_seed=rng)

idata_wide.to_zarr("analysis/inference_data_wide_prior.zarr", mode="w")

wide_slope_mean = float(idata_wide.posterior["mu_slope"].mean())
wide_slope_hdi = az.hdi(idata_wide.posterior["mu_slope"], prob=0.95).to_numpy()
main_slope_mean = float(idata.posterior["mu_slope"].mean())
main_slope_hdi = az.hdi(idata.posterior["mu_slope"], prob=0.95).to_numpy()

# Percentage-point-scale effect for both models, each using its OWN posterior
# intercept (the logit->pp conversion is nonlinear, so reusing the main model's
# intercept for the wide-prior model would silently misstate the comparison).
def pp_diff(post):
    acc_std = 1 / (1 + np.exp(-post["mu_intercept"]))
    acc_hard = 1 / (1 + np.exp(-(post["mu_intercept"] + post["mu_slope"])))
    return float(((acc_hard - acc_std) * 100).mean())

main_diff_pp = pp_diff(idata.posterior)
wide_diff_pp = pp_diff(idata_wide.posterior)

# --- Key results ---
slope_samples = idata.posterior["mu_slope"].to_numpy().ravel()
p_hard_worse = float((slope_samples < 0).mean())

results = {
    "n_divergences": n_divergences,
    "n_chains": int(n_chains),
    "convergence_problems_detected": bool(problems_detected),
    "rhat_max_key_params": rhat_max,
    "ess_bulk_min_key_params": ess_min,
    "mu_slope_mean": main_slope_mean,
    "mu_slope_hdi95": main_slope_hdi.tolist(),
    "p_hard_worse_than_standard": p_hard_worse,
    "mu_intercept_mean": float(idata.posterior["mu_intercept"].mean()),
    "main_diff_pp": main_diff_pp,
    "sensitivity_wide_prior_mu_slope_mean": wide_slope_mean,
    "sensitivity_wide_prior_mu_slope_hdi95": wide_slope_hdi.tolist(),
    "sensitivity_wide_prior_diff_pp": wide_diff_pp,
}
with open("analysis/results_summary.json", "w") as f:
    json.dump(results, f, indent=2)

print("\n=== Results ===")
print(json.dumps(results, indent=2))
