"""Do the workshop/talk claims hold across seeds, or was the committed seed lucky?

Run: uv run python scripts/seed_sweep.py --seeds 20 --out sweep_report.md
Exit 1 if any claim holds in fewer than --min-pass seeds.
"""

import argparse
import time
from pathlib import Path

import arviz_stats as azs
import numpy as np
import pandas as pd

from psychsim.checks import pit_coverage, shrinkage_ratio
from psychsim.models import (
    betabinomial_model,
    binomial_model,
    talk_betabinomial_model,
    talk_binomial_model,
)
from psychsim.sampling import convergence_summary, sample_model
from psychsim.simulate import simulate_study


def eti(da, prob=0.9):
    q = da.quantile([(1 - prob) / 2, 1 - (1 - prob) / 2], dim=("chain", "draw"))
    return float(q[0]), float(q[1])


def evaluate(seed, *, n_participants, n_trials, draws, tune):
    study = simulate_study(seed=seed, n_participants=n_participants, n_trials=n_trials)
    s, t = study.sessions, study.truth
    train = s[(s["condition"] == "standard") & (s["session"] <= 4)].reset_index(drop=True)
    both = s[s["session"] <= 4].reset_index(drop=True)
    tr = study.trials
    t20 = tr[(tr["condition"] == "standard") & (tr["session"] == 1) & (tr["trial"] <= 20)]
    s1 = t20.groupby(["participant", "session", "condition"], as_index=False).agg(
        n_trials=("correct", "size"), n_correct=("correct", "sum")
    )
    rng = np.random.default_rng(seed)
    kw = dict(rng=rng, draws=draws, tune=tune, prior_draws=10)
    i1, i2 = sample_model(binomial_model(train), **kw), sample_model(betabinomial_model(train), **kw)
    it = sample_model(talk_binomial_model(both), **kw)
    it2 = sample_model(talk_betabinomial_model(both), **kw)
    is1 = sample_model(binomial_model(s1), rng=rng, draws=draws, tune=tune, prior_draws=10, target_accept=0.95)

    k_lo, k_hi = eti(i2.posterior["kappa"])
    sg_lo, sg_hi = eti(i2.posterior["sigma_participant"])
    b_lo, b_hi = eti(it.posterior["beta"])
    b2_lo, b2_hi = eti(it2.posterior["beta"])
    c1 = pit_coverage(
        i1.posterior_predictive["n_correct"],
        train["n_correct"],
        probs=(0.5, 0.9),
        rng=rng,
        sample_axes=(0, 1),
    )
    c2 = pit_coverage(
        i2.posterior_predictive["n_correct"],
        train["n_correct"],
        probs=(0.5, 0.9),
        rng=rng,
        sample_axes=(0, 1),
    )
    cov1, cov2 = c1[0.9], c2[0.9]
    cmp = azs.compare({"binomial": i1, "betabinomial": i2})
    raw = (s1["n_correct"] / s1["n_trials"]).to_numpy()
    shrink = shrinkage_ratio(raw, is1.posterior["p_participant"].mean(dim=("chain", "draw")).to_numpy(), raw.mean())
    # Cleanliness is judged on the data-rich models the story rests on; the 20-trial shrinkage
    # this posterior is deliberately underpowered and only its posterior means are used.
    clean = all(
        c["divergences"] == 0 and c["max_rhat"] <= 1.01 and c["min_ess"] >= 100 * 4
        for c in (convergence_summary(i) for i in (i1, i2, it, it2))
    )
    claims = {
        "kappa_in_90": k_lo <= t.kappa <= k_hi,
        "sigma_in_90": sg_lo <= t.sigma_participant <= sg_hi,
        "m1_cov90_below_0.85_and_cov50_below_0.42": cov1 < 0.85 and c1[0.5] < 0.42,
        "m2_cov90_in_[0.84,0.97]": 0.84 <= cov2 <= 0.97,
        "loo_prefers_m2": cmp.index[0] == "betabinomial",
        "beta_in_90_expanded_talk_model": b2_lo <= t.beta <= b2_hi,
        "sessionblind_beta_interval_narrower": (b_hi - b_lo) < (b2_hi - b2_lo),
        "shrink_20trials_below_0.75": shrink < 0.75,
        "clean_sampling": clean,
    }
    numbers = {
        "beta_in_90_sessionblind_RATE_ONLY": b_lo <= t.beta <= b_hi,
        "beta_width_blind": b_hi - b_lo,
        "beta_width_expanded": b2_hi - b2_lo,
        "kappa_lo": k_lo,
        "kappa_hi": k_hi,
        "cov1": cov1,
        "cov2": cov2,
        "cov50_1": c1[0.5],
        "cov50_2": c2[0.5],
        "elpd_diff": float(cmp.loc["binomial", "elpd_diff"]),
        "dse": float(cmp.loc["binomial", "dse"]),
        "shrink": shrink,
    }
    return claims, numbers


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--first-seed", type=int, default=1)
    ap.add_argument("--min-pass", type=int, default=18)
    ap.add_argument("--n-participants", type=int, default=40)
    ap.add_argument("--n-trials", type=int, default=100)
    ap.add_argument("--draws", type=int, default=1000)
    ap.add_argument("--tune", type=int, default=1000)
    ap.add_argument("--out", default="sweep_report.md")
    a = ap.parse_args()
    rows = []
    for seed in range(a.first_seed, a.first_seed + a.seeds):
        t0 = time.time()
        claims, numbers = evaluate(
            seed, n_participants=a.n_participants, n_trials=a.n_trials, draws=a.draws, tune=a.tune
        )
        rows.append({"seed": seed, **claims, **numbers, "secs": round(time.time() - t0)})
        print(
            f"seed {seed}: {sum(claims.values())}/{len(claims)} claims  cov1={numbers['cov1']:.2f} cov2={numbers['cov2']:.2f} "
            f"kappa=[{numbers['kappa_lo']:.0f},{numbers['kappa_hi']:.0f}] shrink={numbers['shrink']:.2f} ({rows[-1]['secs']}s)",
            flush=True,
        )
    df = pd.DataFrame(rows)
    claim_cols = [c for c in df.columns if df[c].dtype == bool and "RATE_ONLY" not in c]
    rate_cols = [c for c in df.columns if "RATE_ONLY" in c]
    counts = df[claim_cols].sum()
    lines = [
        f"# Seed sweep — P={a.n_participants}, T={a.n_trials}, {a.seeds} seeds, draws={a.draws}\n",
        "| claim | passes |",
        "|---|---|",
    ]
    lines += [f"| {c} | {int(counts[c])}/{a.seeds} |" for c in claim_cols]
    lines += [f"| {c} (recorded, not a claim) | {int(df[c].sum())}/{a.seeds} |" for c in rate_cols]
    lines += ["", df.round(3).to_markdown(index=False)]
    Path(a.out).write_text("\n".join(lines) + "\n")
    print("\n".join(lines[: 3 + len(claim_cols)]))
    failing = [c for c in claim_cols if counts[c] < a.min_pass]
    print("FAIL:" if failing else "OK:", failing or f"all claims ≥ {a.min_pass}/{a.seeds}")
    raise SystemExit(1 if failing else 0)


if __name__ == "__main__":
    main()
