"""The talk figure script must produce every PNG the deck references, non-empty (slow: fits models)."""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.slow

EXPECTED = [
    "fig02_prior_absurd",
    "fig03_prior_sensible",
    "fig04_posterior_truth",
    "fig05a_shrinkage_20trials",
    "fig05b_shrinkage_progression",
    "fig06_ci_vs_credible",
    "fig07_ppc_dist",
    "fig08_coverage_binomial",
    "fig09_pit_ecdf",
    "fig10_coverage_betabinomial",
    "fig11_compare_panel",
]


def test_figures_script_produces_all_pngs(tmp_path):
    res = subprocess.run(
        [
            sys.executable,
            str(ROOT / "talk" / "figures" / "make_figures.py"),
            "--out",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=1200,
    )
    assert res.returncode == 0, res.stderr[-3000:]
    for name in EXPECTED:
        f = tmp_path / f"{name}.png"
        assert f.exists() and f.stat().st_size > 15_000, f"{name}.png missing or too small"
