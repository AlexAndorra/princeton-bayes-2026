"""Refit with much wider variance-component priors to check mu_beta is robust.
psense_summary flagged sigma_alpha/sigma_beta/sigma_obs as prior-sensitive
(expected: each is informed by few independent groups). This checks whether
the substantive condition-effect conclusion depends on that prior choice.
"""
import numpy as np
import pandas as pd
import pymc as pm
import arviz as az

RANDOM_SEED = sum(map(ord, "participant-accuracy-condition-sensitivity"))
rng = np.random.default_rng(RANDOM_SEED)

sessions = pd.read_csv("data/sessions.csv")
participants = np.sort(sessions["participant"].unique())
participant_idx = sessions["participant"].map({p: i for i, p in enumerate(participants)}).to_numpy()
hard_ind = (sessions["condition"] == "hard").to_numpy().astype(float)
n_trials_obs = sessions["n_trials"].to_numpy()
n_correct_obs = sessions["n_correct"].to_numpy()

coords = {"participant": participants, "obs": np.arange(len(sessions))}

with pm.Model(coords=coords) as model:
    participant_idx_data = pm.Data("participant_idx", participant_idx, dims="obs")
    hard_ind_data = pm.Data("hard_ind", hard_ind, dims="obs")
    n_trials_data = pm.Data("n_trials", n_trials_obs, dims="obs")

    mu_alpha = pm.Normal("mu_alpha", mu=0.0, sigma=1.5)
    mu_beta = pm.Normal("mu_beta", mu=0.0, sigma=1.0)

    # Much wider than the main model (Gamma(2,2) mean 1 -> Gamma(2,0.5) mean 4;
    # Gamma(2,4) mean 0.5 -> Gamma(2,1) mean 2).
    sigma_alpha = pm.Gamma("sigma_alpha", alpha=2.0, beta=0.5)
    sigma_beta = pm.Gamma("sigma_beta", alpha=2.0, beta=0.5)
    alpha_raw = pm.Normal("alpha_raw", mu=0.0, sigma=1.0, dims="participant")
    beta_raw = pm.Normal("beta_raw", mu=0.0, sigma=1.0, dims="participant")
    alpha = pm.Deterministic("alpha", mu_alpha + alpha_raw * sigma_alpha, dims="participant")
    beta = pm.Deterministic("beta", mu_beta + beta_raw * sigma_beta, dims="participant")

    sigma_obs = pm.Gamma("sigma_obs", alpha=2.0, beta=1.0)
    eps_raw = pm.Normal("eps_raw", mu=0.0, sigma=1.0, dims="obs")

    logit_p = (
        alpha[participant_idx_data]
        + beta[participant_idx_data] * hard_ind_data
        + eps_raw * sigma_obs
    )
    p = pm.Deterministic("p", pm.math.invlogit(logit_p), dims="obs")
    pm.Binomial("n_correct", n=n_trials_data, p=p, observed=n_correct_obs, dims="obs")

    idata_wide = pm.sample(
        nuts_sampler="nutpie", target_accept=0.95, draws=1000, tune=1000, random_seed=rng
    )

print(az.summary(idata_wide, var_names=["mu_alpha", "mu_beta", "sigma_alpha", "sigma_beta", "sigma_obs"]))

idata_orig = az.from_netcdf("accuracy-hierarchical/inference_data.nc")
mb_orig = idata_orig.posterior["mu_beta"]
mb_wide = idata_wide.posterior["mu_beta"]
print("\noriginal priors: mu_beta mean", float(mb_orig.mean()), "94% HDI", az.hdi(mb_orig, prob=0.94).mu_beta.values)
print("wide priors:     mu_beta mean", float(mb_wide.mean()), "94% HDI", az.hdi(mb_wide, prob=0.94).mu_beta.values)
print("P(mu_beta<0) orig:", float((mb_orig < 0).mean()), "wide:", float((mb_wide < 0).mean()))
