# Is That Variability Real, or Just Noise?

A Bayesian-workflow talk and hands-on workshop on repeated-measures accuracy data, built for
[Princeton Psychology](https://psychology.princeton.edu/news-events/2026/alexandre-andorra-senior-data-scientist) (September 2026).

**[▶ Open the workshop notebook in Colab](https://colab.research.google.com/github/AlexAndorra/princeton-bayes-2026/blob/main/workshop/notebooks/01_real_or_noise.ipynb)** — nothing to install.

**[▶ The talk slides](https://alexandorra.github.io/princeton-bayes-2026/)**

## The question

A participant runs the same task across five sessions and their accuracy moves: .58, .81, .66, .62, .64.
Real change from session to session, or just the noise of a hundred coin flips? The talk builds the
standard repeated-measures model from its generative story and shows how to tell; the workshop makes
you do it, and then hands the same data to an AI assistant for the room to critique.

## What's here

| Path | What it is |
|---|---|
| `workshop/notebooks/01_real_or_noise.ipynb` | The 90-minute Colab session: binomial vs beta-binomial, prior predictive, parameter recovery, coverage, model comparison, trial-by-trial updating, a playground, and the agent critique |
| `talk/` | The Slidev deck (`slides.md`), the figures it uses (`public/`), and the script that renders them (`figures/make_figures.py`) |
| `agent/` | The student prompt and two recorded Claude Code runs on this data, with and without the Bayesian-workflow skill: each run's report, code and figures |
| `src/psychsim/` | The synthetic-data generator and the PyMC models |
| `data/` | The generated study and its known truth (`truth.json`, `truth_*.csv`); codebook in `data/README.md` |
| `scripts/` | `make_data.py` (regenerate the data), `seed_sweep.py` (are the pedagogical claims seed-robust?) |
| `tests/` | Simulator, model, notebook-parity, story-holds, notebook-execution, and figure tests |

## Reproduce

```bash
uv sync                        # Python 3.12, pinned PyMC 6 / ArviZ 1.x / nutpie
uv run python scripts/make_data.py
uv run pytest                  # fast tests; add -m slow to sample the models and check the claims
uv run python talk/figures/make_figures.py
```

The notebook is the source of truth: edit `workshop/notebooks/01_real_or_noise.ipynb` in Colab (File → Save a copy in GitHub) or Jupyter, and commit it with its outputs.
