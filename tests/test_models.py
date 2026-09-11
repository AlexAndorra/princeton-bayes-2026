"""Structural tests for the PyMC models (no sampling)."""

import numpy as np
import pymc as pm
import pytest

from psychsim.models import (
    betabinomial_model,
    binomial_model,
    make_coords,
    talk_betabinomial_model,
    talk_binomial_model,
)
from psychsim.simulate import kappa_from_sd, simulate_study


@pytest.fixture(scope="module")
def sessions():
    s = simulate_study(n_participants=10, n_sessions=3, seed=11).sessions
    return s[s["condition"] == "standard"].reset_index(drop=True)


@pytest.fixture(scope="module")
def both_conditions():
    return simulate_study(n_participants=10, n_sessions=3, seed=11).sessions


def free_rv_names(model):
    return {rv.name for rv in model.free_RVs}


def test_make_coords_maps_participants_in_order(sessions):
    coords, idx = make_coords(sessions)
    assert list(coords["participant"]) == list(range(1, 11))
    assert coords["obs"].size == len(sessions)
    assert idx.dtype.kind == "i" and idx.max() == 9
    assert (np.asarray(coords["participant"])[idx] == sessions["participant"].to_numpy()).all()


def test_binomial_model_structure(sessions):
    m = binomial_model(sessions)
    assert free_rv_names(m) == {"mu", "sigma_participant", "theta"}
    assert m.named_vars["p_participant"].eval().shape == (10,)
    assert tuple(m.named_vars_to_dims["p_participant"]) == ("participant",)
    assert tuple(m.named_vars_to_dims["n_correct"]) == ("obs",)
    assert {"participant_idx", "n_trials", "n_correct_data"} <= set(m.named_vars)


def test_betabinomial_model_adds_kappa(sessions):
    m = betabinomial_model(sessions)
    assert free_rv_names(m) == {"mu", "sigma_participant", "theta", "kappa"}


def test_kappa_prior_puts_ninety_percent_of_mass_between_two_and_twenty_accuracy_points(sessions):
    m = betabinomial_model(sessions)
    draws = pm.draw(m["kappa"], draws=20_000, random_seed=1)
    lo, hi = kappa_from_sd(0.20), kappa_from_sd(0.02)
    assert np.mean((draws > lo) & (draws < hi)) == pytest.approx(0.90, abs=0.03)


def test_talk_models_have_condition_effect(both_conditions):
    m = talk_binomial_model(both_conditions)
    assert free_rv_names(m) == {"mu", "beta", "sigma_participant", "theta"}
    m2 = talk_betabinomial_model(both_conditions)
    assert free_rv_names(m2) == {"mu", "beta", "sigma_participant", "theta", "kappa"}
    assert tuple(m.named_vars_to_dims["p_obs"]) == ("obs",)


def test_talk_model_absurd_priors_are_absurd(both_conditions):
    wide = pm.draw(talk_binomial_model(both_conditions, priors="absurd")["mu"], draws=5000, random_seed=2)
    sane = pm.draw(talk_binomial_model(both_conditions, priors="sensible")["mu"], draws=5000, random_seed=2)
    assert wide.std() > 8 and sane.std() < 2


def test_models_reject_multiple_conditions_without_condition_term(both_conditions):
    with pytest.raises(ValueError, match="one condition"):
        binomial_model(both_conditions)
