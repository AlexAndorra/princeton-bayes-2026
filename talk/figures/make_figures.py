"""Render every figure the talk deck uses into talk/public/ (or --out). Reproducible from the data.

    uv run python talk/figures/make_figures.py

Samples the talk models (both conditions, sessions 1-4, session-level rows) once, reuses them.
Uses the dark house style so PNGs drop onto the Slidev dark slides.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import arviz as az
import arviz_plots as azp
import arviz_stats as azs
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pymc as pm
from scipy import stats

from psychsim.checks import pit_coverage
from psychsim.models import binomial_model, talk_betabinomial_model, talk_binomial_model
from psychsim.sampling import sample_model
from psychsim.simulate import RANDOM_SEED

ROOT = Path(__file__).resolve().parents[2]
STYLE = Path(__file__).resolve().parent / "dark.mplstyle"
BLUE, YELLOW, LTBLUE, RED = "#0078ee", "#fbc02d", "#9bddfb", "#ff6651"
TRUTHC = "#F5F6F7"


def save(fig, out: Path, name: str):
    fig.savefig(out / f"{name}.png")
    plt.close(fig)
    print("wrote", name)


def load():
    sessions = pd.read_csv(ROOT / "data" / "sessions.csv")
    truth = json.loads((ROOT / "data" / "truth.json").read_text())
    return sessions, truth


def two_model_tree(posteriors: dict, observed) -> az.DataTree:
    """One tree with a `model` dimension, so ArviZ draws both models side by side."""
    return az.from_dict(
        {
            "posterior": {name: idata.posterior["mu"].values for name, idata in posteriors.items()},
            "posterior_predictive": {
                name: idata.posterior_predictive["n_correct"].values for name, idata in posteriors.items()
            },
            "log_likelihood": {name: idata.log_likelihood["n_correct"].values for name, idata in posteriors.items()},
            "observed_data": {name: observed for name in posteriors},
        }
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "talk" / "public")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    plt.style.use(str(STYLE))

    sessions, truth = load()
    train = sessions[sessions["session"] <= 4].reset_index(drop=True)
    observed = train["n_correct"].to_numpy()
    rng = np.random.default_rng(RANDOM_SEED)

    # ---- prior predictive: absurd vs sensible (talk binomial, both conditions) ----
    for tag, priors, title in [
        ("fig02_prior_absurd", "absurd", "Flat-ish defaults: Normal(0, 10)"),
        ("fig03_prior_sensible", "sensible", "Weakly informative: Normal(0, 1.5)"),
    ]:
        with talk_binomial_model(train, priors=priors):
            prior = pm.sample_prior_predictive(draws=600, random_seed=rng)
        prior_tree = az.from_dict(
            {
                "prior_predictive": {title: prior.prior_predictive["n_correct"].values},
                "observed_data": {title: observed},
            }
        )
        azp.plot_ppc_rootogram(
            prior_tree, group="prior_predictive", backend="matplotlib", figure_kwargs={"figsize": (9, 5)}
        )
        save(plt.gcf(), a.out, tag)

    # ---- sample the talk models once ----
    posteriors = {
        "session-blind model": sample_model(talk_binomial_model(train), rng=rng),
        "session-aware model": sample_model(talk_betabinomial_model(train), rng=rng),
    }
    idata_blind, idata_aware = posteriors.values()

    # ---- posteriors, with the truth ----
    pc = azp.plot_dist(
        idata_blind,
        var_names=["mu", "beta", "sigma_participant"],
        backend="matplotlib",
        figure_kwargs={"figsize": (13, 4.2)},
    )
    azp.add_lines(
        pc,
        {"mu": truth["mu"], "beta": truth["beta"], "sigma_participant": truth["sigma_participant"]},
        color=TRUTHC,
        linestyle="--",
    )
    for var, label in [
        ("mu", "population mean (logit)"),
        ("beta", "condition effect"),
        ("sigma_participant", "participant SD"),
    ]:
        pc.viz["plot"][var].item().set(title=label)
    save(pc.viz["figure"].item(), a.out, "fig04_posterior_truth")

    # ---- shrinkage: first 20 trials of session 1 (arrows), standard condition ----
    trials = pd.read_csv(ROOT / "data" / "trials.csv")

    def first_n(n, sess=(1,)):
        t = trials[(trials["condition"] == "standard") & (trials["session"].isin(sess)) & (trials["trial"] <= n)]
        return t.groupby(["participant", "session", "condition"], as_index=False).agg(
            n_trials=("correct", "size"), n_correct=("correct", "sum")
        )

    def shrinkage(df):
        """Raw accuracy vs partially pooled posterior mean, one participant per row."""
        agg = df.groupby("participant", as_index=False).agg(
            n_trials=("n_trials", "sum"), n_correct=("n_correct", "sum")
        )
        agg["condition"] = "standard"
        idata = sample_model(
            binomial_model(agg[["participant", "n_trials", "n_correct", "condition"]].assign(session=1)),
            rng=np.random.default_rng(RANDOM_SEED),
            draws=1500,
            tune=1500,
            target_accept=0.95,
            prior_draws=10,
        )
        raw = (agg["n_correct"] / agg["n_trials"]).to_numpy()
        post = idata.posterior["p_participant"].mean(dim=("chain", "draw")).to_numpy()
        return raw, post

    raw, post = shrinkage(first_n(20))
    pooled = raw.mean()
    order = np.argsort(raw)
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.axvline(pooled, color=YELLOW, lw=2, ls=":", label="population mean")
    for k, i in enumerate(order):
        ax.annotate(
            "", xy=(post[i], k), xytext=(raw[i], k), arrowprops=dict(arrowstyle="->", color=LTBLUE, lw=1.5, alpha=0.8)
        )
    ax.plot(raw[order], range(len(raw)), "o", color=RED, ms=6, label="raw accuracy (20 trials)")
    ax.plot(post[order], range(len(raw)), "o", color=BLUE, ms=6, label="partial-pooling estimate")
    ax.set(xlabel="accuracy (first 20 trials)", yticks=[], ylabel="participant")
    ax.legend(loc="lower right")
    save(fig, a.out, "fig05a_shrinkage_20trials")

    # ---- shrinkage shrinks as data arrive ----
    stages = [
        ("20 trials", first_n(20)),
        ("100 trials", first_n(100)),
        ("2 sessions", first_n(100, (1, 2))),
        ("4 sessions", first_n(100, (1, 2, 3, 4))),
    ]
    fig, axes = plt.subplots(1, 4, figsize=(15, 4.2), sharey=True, constrained_layout=True)
    for ax, (label, df) in zip(axes, stages):
        raw, post = shrinkage(df)
        pooled = raw.mean()
        ratio = np.mean(np.abs(post - pooled)) / np.mean(np.abs(raw - pooled))
        order = np.argsort(raw)
        for k, i in enumerate(order):
            ax.annotate(
                "",
                xy=(post[i], k),
                xytext=(raw[i], k),
                arrowprops=dict(arrowstyle="->", color=LTBLUE, lw=1.2, alpha=0.7),
            )
        ax.plot(raw[order], range(len(raw)), "o", color=RED, ms=3)
        ax.plot(post[order], range(len(raw)), "o", color=BLUE, ms=3)
        ax.axvline(pooled, color=YELLOW, lw=1.5, ls=":")
        ax.set(title=f"{label}\nshrink {ratio:.0%}", xlabel="accuracy", yticks=[], xlim=(0.3, 1.0))
    axes[0].set_ylabel("participant")
    save(fig, a.out, "fig05b_shrinkage_progression")

    # ---- credible vs confidence: Wilson (no pooling) vs posterior (partial pooling), first 20 trials ----
    # no library draws both interval kinds on one axis, so this one stays hand-made
    df20 = first_n(20)
    idata20 = sample_model(
        binomial_model(df20.assign(condition="standard")),
        rng=np.random.default_rng(RANDOM_SEED),
        draws=1500,
        tune=1500,
        target_accept=0.95,
        prior_draws=10,
    )
    k20 = df20["n_correct"].to_numpy()
    n20 = df20["n_trials"].to_numpy()
    show = np.argsort(k20 / n20)[::3][:12]
    wilson = [stats.binomtest(int(k), int(n)).proportion_ci(0.9, method="wilson") for k, n in zip(k20[show], n20[show])]
    wilson_lo, wilson_hi = zip(*wilson)
    post20 = idata20.posterior["p_participant"]
    post_lo, post_hi = post20.quantile([0.05, 0.95], dim=("chain", "draw")).values
    post_mean = post20.mean(dim=("chain", "draw")).values
    fig, ax = plt.subplots(figsize=(11, 5.5))
    y = np.arange(len(show))
    ax.hlines(y - 0.15, wilson_lo, wilson_hi, color=RED, lw=3, label="Wilson 90% CI (each participant alone)")
    ax.hlines(
        y + 0.15, post_lo[show], post_hi[show], color=BLUE, lw=3, label="90% posterior interval (partial pooling)"
    )
    ax.plot(post_mean[show], y + 0.15, "o", color=BLUE, ms=4)
    ax.set(xlabel="accuracy (first 20 trials)", yticks=[], ylabel="participant")
    ax.legend(loc="upper left")
    save(fig, a.out, "fig06_ci_vs_credible")

    # ---- posterior predictive: rootograms, both models ----
    comparison = two_model_tree(posteriors, observed)
    azp.plot_ppc_rootogram(
        comparison, backend="matplotlib", figure_kwargs={"figsize": (12, 4.5), "sharex": True, "sharey": True}
    )
    save(plt.gcf(), a.out, "fig07_ppc_dist")

    # ---- coverage and PIT, one model per figure ----
    for tag, name, kwargs in [
        ("fig08_coverage_binomial", "session-blind model", {"coverage": True}),
        ("fig09_pit_ecdf", "session-blind model", {}),
        ("fig10_coverage_betabinomial", "session-aware model", {"coverage": True}),
    ]:
        azp.plot_ppc_pit(
            comparison, var_names=[name], backend="matplotlib", figure_kwargs={"figsize": (8, 4.5)}, **kwargs
        )
        save(plt.gcf(), a.out, tag)

    # the numbers the slides quote
    for name, idata in posteriors.items():
        coverage = pit_coverage(
            idata.posterior_predictive["n_correct"].values, observed, probs=(0.5, 0.9), rng=rng, sample_axes=(0, 1)
        )
        print(f"{name}: 50% intervals hold {coverage[0.5]:.0%} of sessions, 90% intervals hold {coverage[0.9]:.0%}")

    # ---- comparison as one input ----
    cmp = azs.compare(posteriors)
    azp.plot_compare(cmp, backend="matplotlib", figure_kwargs={"figsize": (10, 3.8)})
    save(plt.gcf(), a.out, "fig11_compare_panel")
    print(cmp[["elpd", "elpd_diff", "dse"]].round(1))

    print("all figures written to", a.out)


if __name__ == "__main__":
    main()
