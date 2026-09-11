"""
Hierarchical logistic regression for per-participant accuracy by condition.

Generative story: each participant i has a baseline accuracy in the standard
condition (alpha_i, logit scale) and a participant-specific shift when moving
to the hard condition (beta_i), both partially pooled across participants.
Session counts are overdispersed relative to plain binomial sampling (EDA:
obs/binomial variance ratio ~2.6x) -- some sessions are just off days. A first
version captured this with a per-observation logit-normal noise term, but that
adds one latent parameter per row (400 of them), which made LOO-CV degenerate
(most Pareto k > 0.7, p_loo ~ n_obs) and is unnecessary: a Beta-Binomial
likelihood captures the same overdispersion analytically, with a single shared
concentration parameter, and keeps per-observation model checks meaningful.
"""
import os

import arviz as az
import numpy as np
import pandas as pd
import pymc as pm

RANDOM_SEED = sum(map(ord, "participant-accuracy-condition-v1"))
rng = np.random.default_rng(RANDOM_SEED)

RESULTS_DIR = "accuracy-hierarchical"
os.makedirs(RESULTS_DIR, exist_ok=True)

sessions = pd.read_csv("data/sessions.csv")

participants = np.sort(sessions["participant"].unique())
participant_idx = sessions["participant"].map({p: i for i, p in enumerate(participants)}).to_numpy()
hard_ind = (sessions["condition"] == "hard").to_numpy().astype(float)
n_trials_obs = sessions["n_trials"].to_numpy()
n_correct_obs = sessions["n_correct"].to_numpy()

coords = {
    "participant": participants,
    "param": ["alpha", "beta"],
    "obs": np.arange(len(sessions)),
}

with pm.Model(coords=coords) as model:
    participant_idx_data = pm.Data("participant_idx", participant_idx, dims="obs")
    hard_ind_data = pm.Data("hard_ind", hard_ind, dims="obs")
    n_trials_data = pm.Data("n_trials", n_trials_obs, dims="obs")

    # Population-level means on the logit scale.
    # logit(0.7) ~= 0.85, logit(0.5) = 0: Normal(0, 1.5) comfortably covers
    # accuracies from ~5% to ~95% within 2 SD, without ruling out extremes.
    mu_alpha = pm.Normal("mu_alpha", mu=0.0, sigma=1.5)
    # Condition shift centered at 0 (no assumed direction), SD=1 allows large shifts.
    mu_beta = pm.Normal("mu_beta", mu=0.0, sigma=1.0)

    # Varying intercept (alpha_i) and slope (beta_i) per participant, non-centered.
    # A correlated (LKJ) version was tried first but showed poor mixing (R-hat >
    # 1.01, low ESS) on chol_stds/effects: with 40 participants x 5 sessions the
    # intercept-slope correlation is only weakly identified (posterior ~ prior,
    # HDI [-0.62, 0.51]), so it added sampling difficulty without informing the
    # substantive question. Independent varying effects are simpler and mix well.
    # Gamma(2, 2): mean 1 logit-unit of between-participant SD, avoids the
    # near-zero funnel of HalfCauchy/HalfFlat.
    sigma_alpha = pm.Gamma("sigma_alpha", alpha=2.0, beta=2.0)
    sigma_beta = pm.Gamma("sigma_beta", alpha=2.0, beta=2.0)
    alpha_raw = pm.Normal("alpha_raw", mu=0.0, sigma=1.0, dims="participant")
    beta_raw = pm.Normal("beta_raw", mu=0.0, sigma=1.0, dims="participant")
    alpha = pm.Deterministic("alpha", mu_alpha + alpha_raw * sigma_alpha, dims="participant")
    beta = pm.Deterministic("beta", mu_beta + beta_raw * sigma_beta, dims="participant")

    logit_p = alpha[participant_idx_data] + beta[participant_idx_data] * hard_ind_data
    p = pm.Deterministic("p", pm.math.invlogit(logit_p), dims="obs")

    # Beta-Binomial concentration kappa: for a Beta-Binomial(n, p, kappa), the
    # variance-inflation factor over plain Binomial(n, p) is (kappa + n) / (kappa + 1).
    # Solving for the EDA's observed ratio (~2.6x) at n=100 gives kappa ~ 61.
    # Gamma(4, 1/15): mean 60, weakly informative around that back-of-envelope
    # value while leaving room for the data to move it.
    kappa = pm.Gamma("kappa", alpha=4.0, beta=1.0 / 15.0)

    pm.BetaBinomial(
        "n_correct",
        n=n_trials_data,
        alpha=p * kappa,
        beta=(1 - p) * kappa,
        observed=n_correct_obs,
        dims="obs",
    )

    # --- Prior predictive check ---
    prior_pred = pm.sample_prior_predictive(draws=500, random_seed=rng)

    # --- Inference ---
    idata = pm.sample(
        nuts_sampler="nutpie",
        target_accept=0.95,
        draws=2000,
        tune=2000,
        random_seed=rng,
    )
    idata["prior"] = prior_pred["prior"]
    idata["prior_predictive"] = prior_pred["prior_predictive"]
    ppc = pm.sample_posterior_predictive(idata, random_seed=rng)
    idata["posterior_predictive"] = ppc["posterior_predictive"]

    pm.compute_log_likelihood(idata, model=model)
    pm.compute_log_prior(idata, model=model)

    idata.to_netcdf(os.path.join(RESULTS_DIR, "inference_data.nc"))

print("Saved inference data to", os.path.join(RESULTS_DIR, "inference_data.nc"))

# Model graph
try:
    gv = pm.model_to_graphviz(model)
    gv.render(os.path.join(RESULTS_DIR, "model_graph"), format="png", cleanup=True)
except Exception as e:
    print("graphviz render failed:", e)

az.summary(
    idata, var_names=["mu_alpha", "mu_beta", "sigma_alpha", "sigma_beta", "kappa"]
).to_csv(os.path.join(RESULTS_DIR, "summary.csv"))
print("Done.")
