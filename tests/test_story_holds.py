"""The pedagogical claims the workshop and the talk make must hold on the committed data.

Slow: samples the models once per session. Run with `uv run pytest -m slow tests/test_story_holds.py -s`.
"""

import json
from pathlib import Path

import arviz_stats as azs
import numpy as np
import pandas as pd
import pytest

from psychsim.checks import pit_coverage, shrinkage_ratio
from psychsim.models import (
    betabinomial_model,
    binomial_model,
    talk_betabinomial_model,
    talk_binomial_model,
)
from psychsim.sampling import convergence_summary, sample_model
from psychsim.simulate import RANDOM_SEED, sd_from_kappa

pytestmark = pytest.mark.slow
ROOT = Path(__file__).resolve().parents[1]


def eti(da, prob=0.9):
    q = da.quantile([(1 - prob) / 2, 1 - (1 - prob) / 2], dim=("chain", "draw"))
    return float(q[0]), float(q[1])


@pytest.fixture(scope="module")
def data():
    sessions = pd.read_csv(ROOT / "data" / "sessions.csv")
    truth = json.loads((ROOT / "data" / "truth.json").read_text())
    return sessions, truth


@pytest.fixture(scope="module")
def workshop(data):
    sessions, _ = data
    train = sessions[(sessions["condition"] == "standard") & (sessions["session"] <= 4)].reset_index(drop=True)
    rng = np.random.default_rng(RANDOM_SEED)
    m1, m2 = binomial_model(train), betabinomial_model(train)
    return train, sample_model(m1, rng=rng), sample_model(m2, rng=rng)


@pytest.fixture(scope="module")
def talk(data):
    sessions, _ = data
    train = sessions[sessions["session"] <= 4].reset_index(drop=True)
    rng = np.random.default_rng(RANDOM_SEED)
    return (
        train,
        sample_model(talk_binomial_model(train), rng=rng),
        sample_model(talk_betabinomial_model(train), rng=rng),
    )


def test_model2_recovers_kappa(workshop, data):
    _, _, idata2 = workshop
    lo, hi = eti(idata2.posterior["kappa"])
    print(f"\nkappa 90% interval [{lo:.1f}, {hi:.1f}], truth {data[1]['kappa']}")
    assert lo <= data[1]["kappa"] <= hi


def test_model2_recovers_between_session_sd(workshop, data):
    _, _, idata2 = workshop
    lo, hi = eti(sd_from_kappa(idata2.posterior["kappa"], p=0.7))
    print(f"\nimplied SD 90% interval [{lo:.3f}, {hi:.3f}], truth {data[1]['sd_between_sessions']:.3f}")
    assert lo <= data[1]["sd_between_sessions"] <= hi


def test_both_models_recover_sigma_participant(workshop, data):
    _, idata1, idata2 = workshop
    for name, idata in [("binomial", idata1), ("betabinomial", idata2)]:
        lo, hi = eti(idata.posterior["sigma_participant"])
        print(f"\n{name}: sigma_participant 90% [{lo:.2f}, {hi:.2f}], truth {data[1]['sigma_participant']}")
        assert lo <= data[1]["sigma_participant"] <= hi


def coverage(idata, train):
    return pit_coverage(
        idata.posterior_predictive["n_correct"],
        train["n_correct"],
        probs=(0.5, 0.9),
        rng=np.random.default_rng(RANDOM_SEED),
        sample_axes=(0, 1),
    )


def test_model1_session_coverage_below_nominal(workshop):
    """The session-blind model's intervals keep less than they promise, at every level."""
    train, idata1, _ = workshop
    cov = coverage(idata1, train)
    print(f"\nbinomial PIT coverage: 50% -> {cov[0.5]:.3f}, 90% -> {cov[0.9]:.3f}")
    assert cov[0.5] < 0.42 and cov[0.9] < 0.85


def test_model2_session_coverage_nominal(workshop):
    train, _, idata2 = workshop
    cov = coverage(idata2, train)
    print(f"\nbetabinomial PIT coverage: 50% -> {cov[0.5]:.3f}, 90% -> {cov[0.9]:.3f}")
    assert 0.40 <= cov[0.5] <= 0.62 and 0.84 <= cov[0.9] <= 0.97


def test_loo_prefers_model2_without_a_threshold(workshop):
    _, idata1, idata2 = workshop
    cmp = azs.compare({"binomial": idata1, "betabinomial": idata2})
    print("\n", cmp[["elpd", "elpd_diff", "dse"]] if "dse" in cmp.columns else cmp)
    assert cmp.index[0] == "betabinomial"


def test_sampling_is_clean(workshop, talk):
    _, idata1, idata2 = workshop
    _, idata_talk, idata_talk2 = talk
    for name, idata in [
        ("binomial", idata1),
        ("betabinomial", idata2),
        ("talk", idata_talk),
        ("talk-expanded", idata_talk2),
    ]:
        s = convergence_summary(idata)
        print(f"\n{name}: {s}")
        assert s["divergences"] == 0 and s["max_rhat"] <= 1.01 and s["min_ess"] >= 400


def test_expanded_talk_model_recovers_condition_effect(talk, data):
    """The session-aware glmer's 90% interval on beta contains the truth (the session-blind one
    under-covers systematically: ~70% across seeds, see sweep_report.md — that is a talk slide)."""
    _, idata_blind, idata_expanded = talk
    lo, hi = eti(idata_expanded.posterior["beta"])
    blo, bhi = eti(idata_blind.posterior["beta"])
    print(
        f"\nbeta 90%: session-blind [{blo:.2f}, {bhi:.2f}] width {bhi - blo:.2f} | expanded [{lo:.2f}, {hi:.2f}] width {hi - lo:.2f} | truth {data[1]['beta']}"
    )
    assert lo <= data[1]["beta"] <= hi
    assert (bhi - blo) < (hi - lo)


def first_trials(n: int) -> pd.DataFrame:
    """Session-level rows built from only the first `n` trials of session 1, standard condition."""
    trials = pd.read_csv(ROOT / "data" / "trials.csv")
    t = trials[(trials["condition"] == "standard") & (trials["session"] == 1) & (trials["trial"] <= n)]
    return t.groupby(["participant", "session", "condition"], as_index=False).agg(
        n_trials=("correct", "size"), n_correct=("correct", "sum")
    )


def test_shrinkage_visible_after_twenty_trials():
    s1 = first_trials(20)
    idata = sample_model(binomial_model(s1), rng=np.random.default_rng(RANDOM_SEED))
    raw = (s1["n_correct"] / s1["n_trials"]).to_numpy()
    post = idata.posterior["p_participant"].mean(dim=("chain", "draw")).to_numpy()
    ratio = shrinkage_ratio(raw, post, raw.mean())
    print(f"\nshrinkage ratio after 20 trials: {ratio:.2f}")
    assert ratio < 0.75
