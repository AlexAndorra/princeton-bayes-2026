# The same data, handed to an AI assistant twice

`prompt.md` is the request, written the way a second-year student would type it. It was given to
Claude Code (on Claude Sonnet) in a folder containing the data, its codebook, and a Python
environment with PyMC, ArviZ and statsmodels already installed.

| run | skill loaded | read this |
|---|---|---|
| `without-skill/` | no | [report](runs/without-skill/report.md), figures in `figures/` |
| `with-skill/` | [bayesian-workflow](https://github.com/Learning-Bayesian-Statistics/baygent-skills) | [report](runs/with-skill/report.md), then [review](runs/with-skill/review.md); figures and diagnostics in `accuracy-hierarchical/` |

In the skill run, `report.md` is the assistant's first draft, `review.md` is its own review of that
draft, and `model.py` is the beta-binomial it rebuilt afterwards. The diagnostics in
`accuracy-hierarchical/` belong to the rebuilt model.
