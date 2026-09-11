"""PyMC models. Workshop: one condition, participant ability only. Talk: two conditions, + `beta`.

Every model uses the same non-centered participant block
    theta_i = mu + sigma_participant * z_i,   p_participant_i = invlogit(theta_i)
and `pm.Data` containers so `pm.set_data` can swap in a held-out session.
"""

from __future__ import annotations

import pandas as pd
import preliz as pz
import pymc as pm

from .simulate import kappa_from_sd


def kappa_prior():
    """Concentration prior, elicited as session-to-session swings of 2 to 20 accuracy points (90% mass)."""
    return pz.maxent(pz.LogNormal(), lower=kappa_from_sd(0.20), upper=kappa_from_sd(0.02), plot=False)


PRIORS = {
    # weakly informative on the logit scale: accuracies from ~5% to ~95% are all plausible a priori
    "sensible": {"mu_sigma": 1.5, "beta_sigma": 1.0, "sigma_participant_sigma": 1.0},
    # "flat-ish" defaults: what most of the prior mass says is that participants score 0% or 100%
    "absurd": {"mu_sigma": 10.0, "beta_sigma": 10.0, "sigma_participant_sigma": 10.0},
}


def make_coords(sessions: pd.DataFrame):
    idx, participants = pd.factorize(sessions["participant"], sort=True)
    return {"participant": participants, "obs": sessions.index}, idx


def _require_one_condition(sessions: pd.DataFrame) -> None:
    if sessions["condition"].nunique() != 1:
        raise ValueError("workshop models expect one condition; filter `sessions` first")


def _data_and_participant_block(sessions: pd.DataFrame, pr: dict):
    coords, idx = make_coords(sessions)
    model = pm.Model(coords=coords)
    with model:
        participant_idx = pm.Data("participant_idx", idx, dims="obs")
        n_trials = pm.Data("n_trials", sessions["n_trials"].to_numpy(), dims="obs")
        n_correct_data = pm.Data("n_correct_data", sessions["n_correct"].to_numpy(), dims="obs")
        mu = pm.Normal("mu", 0.0, pr["mu_sigma"])  # population-average ability, logit scale
        sigma_participant = pm.HalfNormal("sigma_participant", pr["sigma_participant_sigma"])
        # Centered parameterisation: with ~400-800 trials per participant the likelihood dominates
        # the prior, so centered mixes far better than non-centered here (the reverse holds in the
        # small-data regime the workshop's playground explores).
        theta = pm.Normal("theta", mu, sigma_participant, dims="participant")
        pm.Deterministic("p_participant", pm.math.invlogit(theta), dims="participant")
    return model, theta, participant_idx, n_trials, n_correct_data


def binomial_model(sessions: pd.DataFrame, priors: str = "sensible") -> pm.Model:
    """Model 1: one stable ability per participant; sessions are just more trials."""
    _require_one_condition(sessions)
    model, theta, idx, n_trials, y = _data_and_participant_block(sessions, PRIORS[priors])
    with model:
        pm.Binomial("n_correct", n=n_trials, p=pm.math.invlogit(theta)[idx], observed=y, dims="obs")
    return model


def betabinomial_model(sessions: pd.DataFrame, priors: str = "sensible") -> pm.Model:
    """Model 2: each session's ability wobbles around the participant's, with concentration kappa."""
    _require_one_condition(sessions)
    model, theta, idx, n_trials, y = _data_and_participant_block(sessions, PRIORS[priors])
    with model:
        kappa = kappa_prior().to_pymc("kappa")
        p = pm.math.invlogit(theta)[idx]
        pm.BetaBinomial("n_correct", n=n_trials, alpha=p * kappa, beta=(1 - p) * kappa, observed=y, dims="obs")
    return model


def _talk_block(sessions: pd.DataFrame, pr: dict):
    model, theta, idx, n_trials, y = _data_and_participant_block(sessions, pr)
    with model:
        is_hard = pm.Data("is_hard", (sessions["condition"] == "hard").to_numpy().astype(float), dims="obs")
        beta = pm.Normal("beta", 0.0, pr["beta_sigma"])  # condition effect, logit scale
        p_obs = pm.Deterministic("p_obs", pm.math.invlogit(theta[idx] + beta * is_hard), dims="obs")
    return model, p_obs, n_trials, y


def talk_binomial_model(sessions: pd.DataFrame, priors: str = "sensible") -> pm.Model:
    """The glmer: correct ~ condition + (1 | participant), family = binomial, on session-level counts."""
    model, p_obs, n_trials, y = _talk_block(sessions, PRIORS[priors])
    with model:
        pm.Binomial("n_correct", n=n_trials, p=p_obs, observed=y, dims="obs")
    return model


def talk_betabinomial_model(sessions: pd.DataFrame, priors: str = "sensible") -> pm.Model:
    """The expanded glmer: same story plus a session-level wobble."""
    model, p_obs, n_trials, y = _talk_block(sessions, PRIORS[priors])
    with model:
        kappa = kappa_prior().to_pymc("kappa")
        pm.BetaBinomial(
            "n_correct",
            n=n_trials,
            alpha=p_obs * kappa,
            beta=(1 - p_obs) * kappa,
            observed=y,
            dims="obs",
        )
    return model
