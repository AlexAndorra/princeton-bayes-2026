"""Small numpy checks used by the story tests and the seed sweep (plots stay in ArviZ)."""

from __future__ import annotations

import numpy as np


def interval_coverage(pred, observed, *, prob: float = 0.9, sample_axes=0, discrete: bool = False) -> float:
    """Fraction of observations inside the central `prob` predictive interval.

    `pred` has the sample axis/axes first (e.g. (draw, obs) or (chain, draw, obs) with
    sample_axes=(0, 1)); `observed` has shape (obs,).

    For *continuous* outcomes (`discrete=False`, default) linear-interpolated quantiles are exact.
    For *discrete counts* pass `discrete=True`: the bounds use the "lower"/"higher" quantile methods
    so the interval is the narrowest that still guarantees at least nominal coverage — plain linear
    interpolation biases discrete coverage (conservatively) and should not be used for counts. For
    the sharp calibration statistic the talk and workshop rely on, prefer `pit_coverage` (randomized
    PIT), which is exact for discrete data.
    """
    pred = np.asarray(pred)
    observed = np.asarray(observed)
    axes = (sample_axes,) if isinstance(sample_axes, int) else tuple(sample_axes)
    pred = np.moveaxis(pred, axes, tuple(range(len(axes)))).reshape(-1, *pred.shape[len(axes) :])
    q_lo, q_hi = (1 - prob) / 2, 1 - (1 - prob) / 2
    if discrete:
        lo = np.quantile(pred, q_lo, axis=0, method="lower")
        hi = np.quantile(pred, q_hi, axis=0, method="higher")
    else:
        lo, hi = np.quantile(pred, [q_lo, q_hi], axis=0)
    return float(np.mean((observed >= lo) & (observed <= hi)))


def shrinkage_ratio(raw, posterior_mean, pooled_mean) -> float:
    """How far the posterior means sit from the pooled mean, relative to the raw estimates. 1 = no pooling."""
    raw, post = np.asarray(raw, float), np.asarray(posterior_mean, float)
    return float(np.mean(np.abs(post - pooled_mean)) / np.mean(np.abs(raw - pooled_mean)))


def pit_coverage(pred, observed, *, probs=(0.5, 0.9), rng, sample_axes=0) -> dict:
    """Central-interval coverage computed from randomized PIT values (what ArviZ's coverage plot uses).

    For discrete outcomes the PIT is randomized between F(y-1) and F(y) so a calibrated model gives
    uniform PIT values. Coverage at `prob` = fraction of PIT values within prob/2 of 0.5.
    """
    pred = np.asarray(pred)
    observed = np.asarray(observed)
    axes = (sample_axes,) if isinstance(sample_axes, int) else tuple(sample_axes)
    pred = np.moveaxis(pred, axes, tuple(range(len(axes)))).reshape(-1, *pred.shape[len(axes) :])
    below = (pred < observed).mean(axis=0)
    at_or_below = (pred <= observed).mean(axis=0)
    pit = below + rng.random(observed.shape) * (at_or_below - below)
    return {p: float(np.mean(np.abs(pit - 0.5) < p / 2)) for p in probs}
