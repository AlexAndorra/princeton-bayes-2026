"""The committed workshop notebook is the source of truth: it must run end to end and stay
pre-executed and clean (slow: fits models). It is no longer generated — edit the .ipynb directly."""

import os
import shutil
from pathlib import Path

import nbformat
import pytest
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "workshop" / "notebooks" / "01_real_or_noise.ipynb"
pytestmark = pytest.mark.slow


def error_outputs(nb):
    return [
        (i, o.get("ename"))
        for i, c in enumerate(nb.cells)
        if c.cell_type == "code"
        for o in c.get("outputs", [])
        if o.output_type == "error"
    ]


def test_committed_notebook_executes():
    if shutil.which("dot") is None:
        pytest.skip("Graphviz `dot` not on PATH (the notebook renders model graphs); install graphviz to run this")
    nb = nbformat.read(NB, as_version=4)
    os.environ["PSYCHSIM_LOCAL"] = str(ROOT / "data")  # load committed data, not the raw GitHub URL
    NotebookClient(nb, timeout=1800, kernel_name="python3", resources={"metadata": {"path": str(NB.parent)}}).execute()
    assert error_outputs(nb) == []
    figures = sum(
        1 for c in nb.cells if c.cell_type == "code" for o in c.get("outputs", []) if "image/png" in o.get("data", {})
    )
    assert figures >= 12


def test_committed_notebook_is_pre_executed_and_clean():
    nb = nbformat.read(NB, as_version=4)
    executed = [c for c in nb.cells if c.cell_type == "code" and c.get("outputs")]
    assert len(executed) >= 15, "commit the notebook with its outputs (Run all in Colab/Jupyter, then save)"
    assert error_outputs(nb) == []
