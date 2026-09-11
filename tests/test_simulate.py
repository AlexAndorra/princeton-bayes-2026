"""Tests for the one synthetic world shared by the talk and the workshop."""

import json

import numpy as np
import pandas as pd
import pytest
from scipy.special import expit, logit

from psychsim.simulate import (
    RANDOM_SEED,
    SimulatedStudy,
    Truth,
    kappa_from_sd,
    sd_from_kappa,
    simulate_sessions,
    simulate_study,
    variance_ratio,
    write_study,
)

SESSION_COLUMNS = ["participant", "session", "condition", "n_trials", "n_correct"]
TRIAL_COLUMNS = ["participant", "session", "trial", "correct", "condition"]


@pytest.fixture(scope="module")
def study():
    return simulate_study()


def test_sd_kappa_roundtrip():
    assert kappa_from_sd(sd_from_kappa(42.0)) == pytest.approx(42.0)
    assert sd_from_kappa(42.0, p=0.7) == pytest.approx(np.sqrt(0.21 / 43))
    assert kappa_from_sd(0.07, p=0.7) == pytest.approx(0.21 / 0.07**2 - 1)


def test_default_study_sizes(study):
    t = study.truth
    assert (t.n_participants, t.n_sessions, t.n_trials) == (40, 5, 100)
    assert t.conditions == ("standard", "hard")
    assert t.seed == RANDOM_SEED == sum(map(ord, "real-or-noise"))


def test_sessions_schema(study):
    s = study.sessions
    assert list(s.columns) == SESSION_COLUMNS
    assert len(s) == 40 * 5 * 2
    assert sorted(s["participant"].unique()) == list(range(1, 41))
    assert sorted(s["session"].unique()) == list(range(1, 6))
    assert set(s["condition"]) == {"standard", "hard"}
    assert (s["n_trials"] == 100).all()
    assert s["n_correct"].between(0, 100).all()


def test_trials_schema(study):
    tr = study.trials
    assert list(tr.columns) == TRIAL_COLUMNS
    assert len(tr) == 40 * 5 * 2 * 100
    assert set(tr["correct"].unique()) <= {0, 1}
    assert sorted(tr["trial"].unique()) == list(range(1, 101))


def test_trials_aggregate_to_sessions(study):
    agg = (
        study.trials.groupby(["participant", "session", "condition"], sort=False)["correct"]
        .agg(n_correct="sum", n_trials="size")
        .reset_index()
    )
    merged = study.sessions.merge(agg, on=["participant", "session", "condition"], suffixes=("", "_from_trials"))
    assert len(merged) == len(study.sessions)
    assert (merged["n_correct"] == merged["n_correct_from_trials"]).all()
    assert (merged["n_trials"] == merged["n_trials_from_trials"]).all()


def test_condition_balance(study):
    per_cell = study.sessions.groupby(["participant", "session"])["condition"].nunique()
    assert (per_cell == 2).all()


def test_reproducible_under_seed():
    a, b = simulate_study(seed=7), simulate_study(seed=7)
    pd.testing.assert_frame_equal(a.sessions, b.sessions)
    pd.testing.assert_frame_equal(a.trials, b.trials)
    c = simulate_study(seed=8)
    assert not a.sessions["n_correct"].equals(c.sessions["n_correct"])


def test_truth_complete(study):
    t = study.truth
    assert isinstance(t, Truth) and isinstance(study, SimulatedStudy)
    assert t.mu == pytest.approx(logit(0.70))
    assert t.beta == -0.5 and t.sigma_participant == 0.4 and t.kappa == 42.0
    assert t.theta.shape == (40,)
    assert t.p_session.shape == (40, 5, 2)
    assert t.sd_between_sessions == pytest.approx(sd_from_kappa(42.0, p=expit(t.mu)))


def test_hard_condition_lowers_accuracy(study):
    means = study.sessions.groupby("condition")["n_correct"].mean()
    assert means["hard"] < means["standard"]


def test_implied_sd_matches_empirical():
    rng = np.random.default_rng(1)
    theta = np.full(50, logit(0.7))
    _, _, _, p_session = simulate_sessions(
        n_participants=50, n_sessions=200, n_trials=1, kappa=42.0, rng=rng, theta=theta
    )
    empirical = p_session.std(axis=1, ddof=1).mean()
    assert empirical == pytest.approx(sd_from_kappa(42.0, p=0.7), rel=0.10)


def test_variance_ratio_above_one_at_default_kappa():
    s = simulate_study(n_participants=200, kappa=42.0, seed=3).sessions
    vr = variance_ratio(s)
    assert vr.index.names == ["participant", "condition"]
    assert vr.median() > 2.0  # expected ratio 1 + 99/43 ≈ 3.3; the 4-df sample variance pulls the median down


def test_variance_ratio_near_one_when_kappa_huge():
    s = simulate_study(n_participants=200, kappa=1e6, seed=3).sessions
    assert 0.7 < variance_ratio(s).median() < 1.1


def test_write_study(tmp_path, study):
    write_study(study, tmp_path)
    names = {
        "sessions.csv",
        "trials.csv",
        "truth.json",
        "truth_participants.csv",
        "truth_sessions.csv",
    }
    assert names <= {p.name for p in tmp_path.iterdir()}
    back = pd.read_csv(tmp_path / "sessions.csv")
    pd.testing.assert_frame_equal(back, study.sessions)
    truth = json.loads((tmp_path / "truth.json").read_text())
    assert truth["kappa"] == 42.0 and truth["seed"] == RANDOM_SEED
    assert truth["sd_between_sessions"] == pytest.approx(study.truth.sd_between_sessions)
    tp = pd.read_csv(tmp_path / "truth_participants.csv")
    assert list(tp.columns) == ["participant", "theta", "p_standard", "p_hard"] and len(tp) == 40
    ts = pd.read_csv(tmp_path / "truth_sessions.csv")
    assert list(ts.columns) == ["participant", "session", "condition", "p_true"] and len(ts) == 400
