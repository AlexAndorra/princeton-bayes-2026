"""Guard: the notebook's inline simulator/models match src/psychsim (which drives the talk figures
and the seed sweep). The .ipynb is source-of-truth now; if you intentionally change a model in the
notebook, sync src/psychsim/{simulate,models}.py too, or the talk figures and this test will drift."""

from pathlib import Path

import nbformat
import numpy as np
import pandas as pd
import preliz as pz
import pymc as pm
import pytest
from scipy.special import expit, logit

from psychsim.models import betabinomial_model, binomial_model
from psychsim.simulate import kappa_from_sd, sd_from_kappa, simulate_sessions, simulate_study

NB = Path(__file__).resolve().parents[1] / "workshop" / "notebooks" / "01_real_or_noise.ipynb"


def tagged_source(tag: str) -> str:
    nb = nbformat.read(NB, as_version=4)
    cells = [c for c in nb.cells if tag in c.metadata.get("tags", [])]
    assert len(cells) == 1, f"expected exactly one cell tagged {tag!r}, found {len(cells)}"
    return cells[0].source


def test_inline_simulator_matches_package():
    ns = {"np": np, "pd": pd, "expit": expit, "logit": logit}
    exec(tagged_source("simulator"), ns)
    kw = dict(n_participants=6, n_sessions=3, n_trials=20, kappa=42.0)
    a = ns["simulate_sessions"](rng=np.random.default_rng(5), **kw)
    b = simulate_sessions(rng=np.random.default_rng(5), **kw)
    pd.testing.assert_frame_equal(a[0], b[0])
    pd.testing.assert_frame_equal(a[1], b[1])
    np.testing.assert_allclose(a[2], b[2])
    np.testing.assert_allclose(a[3], b[3])
    assert ns["sd_from_kappa"](42.0) == sd_from_kappa(42.0)
    assert ns["kappa_from_sd"](0.07) == kappa_from_sd(0.07)


@pytest.fixture(scope="module")
def train():
    s = simulate_study(n_participants=8, n_sessions=3, seed=4).sessions
    return s[(s["condition"] == "standard") & (s["session"] <= 2)].reset_index(drop=True)


def source_containing(text: str) -> str:
    nb = nbformat.read(NB, as_version=4)
    cells = [c for c in nb.cells if c.cell_type == "code" and text in c.source]
    assert len(cells) == 1, f"expected exactly one code cell containing {text!r}, found {len(cells)}"
    return cells[0].source


def test_inline_models_match_package(train):
    ns = {
        "np": np,
        "pd": pd,
        "pm": pm,
        "train": train,
        "kappa_from_sd": kappa_from_sd,
        "sd_from_kappa": sd_from_kappa,
    }
    exec(source_containing("COORDS ="), ns)  # defines participants_idx, participants, COORDS
    ns["kappa_prior"] = pz.maxent(pz.LogNormal(), lower=kappa_from_sd(0.20), upper=kappa_from_sd(0.02), plot=False)
    for tag in ("model-binomial", "model-betabinomial"):
        src = "\n".join(line for line in tagged_source(tag).splitlines() if "model_to_graphviz" not in line)
        exec(src, ns)
    for nb_model, pkg_model in [
        (ns["m1"], binomial_model(train)),
        (ns["m2"], betabinomial_model(train)),
    ]:
        assert {rv.name for rv in nb_model.free_RVs} == {rv.name for rv in pkg_model.free_RVs}
        assert set(nb_model.named_vars) == set(pkg_model.named_vars)
        point = pkg_model.initial_point(random_seed=1)
        assert nb_model.compile_logp()(point) == pytest.approx(pkg_model.compile_logp()(point), abs=1e-8)
