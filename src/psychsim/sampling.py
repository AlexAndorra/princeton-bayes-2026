"""One call that runs the whole sampling arc and returns a DataTree with every group filled."""

from __future__ import annotations

import arviz_stats as azs
import numpy as np
import pymc as pm


def sample_model(
    model: pm.Model,
    *,
    rng: np.random.Generator,
    draws: int = 2000,
    tune: int = 1000,
    prior_draws: int = 500,
    target_accept: float = 0.9,
    progressbar: bool = False,
):
    """Prior predictive + NUTS (nutpie, default chains) + posterior predictive + pointwise log-likelihood."""
    with model:
        idata = pm.sample(
            nuts_sampler="nutpie",
            draws=draws,
            tune=tune,
            target_accept=target_accept,
            random_seed=rng,
            progressbar=progressbar,
        )
        prior = pm.sample_prior_predictive(draws=prior_draws, random_seed=rng)
        idata.update(prior)
        pm.sample_posterior_predictive(idata, extend_inferencedata=True, random_seed=rng, progressbar=progressbar)
        pm.compute_log_likelihood(idata, extend_inferencedata=True, progressbar=progressbar)
    return idata


def convergence_summary(idata, var_names=None) -> dict:
    summ = azs.summary(idata, var_names=var_names)
    return {
        "max_rhat": float(summ["r_hat"].max()),
        "min_ess": float(min(summ["ess_bulk"].min(), summ["ess_tail"].min())),
        "divergences": int(idata.sample_stats["diverging"].sum()),
    }
