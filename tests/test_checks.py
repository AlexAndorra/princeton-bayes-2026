"""Numpy-level checks used by the story tests and the seed sweep."""

import numpy as np
import pytest

from psychsim.checks import interval_coverage, shrinkage_ratio


def test_interval_coverage_matches_nominal_for_well_specified_predictions():
    rng = np.random.default_rng(0)
    obs = rng.normal(0, 1, size=2000)
    pred = rng.normal(0, 1, size=(4000, 2000))  # draws x obs
    assert interval_coverage(pred, obs, prob=0.9) == pytest.approx(0.9, abs=0.02)


def test_interval_coverage_drops_when_predictions_too_narrow():
    rng = np.random.default_rng(0)
    obs = rng.normal(0, 2, size=2000)
    pred = rng.normal(0, 1, size=(4000, 2000))
    assert interval_coverage(pred, obs, prob=0.9) < 0.7


def test_interval_coverage_accepts_chain_draw_layout():
    rng = np.random.default_rng(0)
    obs = rng.normal(0, 1, size=500)
    pred = rng.normal(0, 1, size=(4, 1000, 500))  # chain x draw x obs
    assert interval_coverage(pred, obs, prob=0.9, sample_axes=(0, 1)) == pytest.approx(0.9, abs=0.04)


def test_shrinkage_ratio_is_one_without_pooling_and_below_one_with_it():
    raw = np.array([0.5, 0.6, 0.9, 0.8])
    pooled = raw.mean()
    assert shrinkage_ratio(raw, raw, pooled) == pytest.approx(1.0)
    halfway = pooled + 0.5 * (raw - pooled)
    assert shrinkage_ratio(raw, halfway, pooled) == pytest.approx(0.5)


def test_pit_coverage_matches_nominal_for_discrete_well_specified_predictions():
    from psychsim.checks import pit_coverage

    rng = np.random.default_rng(0)
    obs = rng.binomial(100, 0.7, size=3000)
    pred = rng.binomial(100, 0.7, size=(2000, 3000))
    cov = pit_coverage(pred, obs, probs=(0.5, 0.9), rng=np.random.default_rng(1))
    assert cov[0.5] == pytest.approx(0.5, abs=0.03) and cov[0.9] == pytest.approx(0.9, abs=0.02)


def test_pit_coverage_drops_for_overdispersed_data():
    from psychsim.checks import pit_coverage

    rng = np.random.default_rng(0)
    p = rng.beta(0.7 * 20, 0.3 * 20, size=3000)
    obs = rng.binomial(100, p)
    pred = rng.binomial(100, 0.7, size=(2000, 3000))
    cov = pit_coverage(pred, obs, probs=(0.5, 0.9), rng=np.random.default_rng(1), sample_axes=0)
    assert cov[0.5] < 0.35 and cov[0.9] < 0.7


def test_interval_coverage_discrete_flag_is_not_severely_biased():
    from psychsim.checks import interval_coverage

    rng = np.random.default_rng(0)
    obs = rng.binomial(20, 0.5, size=4000)
    pred = rng.binomial(20, 0.5, size=(3000, 4000))
    # linear-interpolation default is badly conservative on coarse counts; discrete=True is near nominal-or-above
    assert interval_coverage(pred, obs, prob=0.5, sample_axes=0, discrete=True) >= 0.5
    assert interval_coverage(pred, obs, prob=0.9, sample_axes=0, discrete=True) >= 0.9
