"""One synthetic world, shared by the talk and the workshop.

Generative story (accuracy on a repeated-measures task):

    population  ->  participant ability theta_i ~ Normal(mu, sigma_participant)  (logit scale)
    condition   ->  logit p_ic = theta_i + beta * [c == "hard"]
    session     ->  p_isc ~ Beta(mean = p_ic, concentration = kappa)          (the "wobble")
    trial       ->  correct ~ Bernoulli(p_isc), n_trials per session per condition

`kappa` sets the between-session variability; `sd_from_kappa` / `kappa_from_sd` translate it to
the probability scale so a prior can be elicited as "session-to-session swings of X accuracy points".
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit, logit

RANDOM_SEED = sum(map(ord, "real-or-noise"))
MU = float(logit(0.70))


def sd_from_kappa(kappa, p=0.7):
    """Between-session SD of accuracy for a participant with mean accuracy p and concentration kappa."""
    return np.sqrt(p * (1 - p) / (kappa + 1))


def kappa_from_sd(sd, p=0.7):
    """Concentration kappa that gives between-session SD `sd` for a participant with mean accuracy p."""
    return p * (1 - p) / sd**2 - 1


def simulate_sessions(
    *, n_participants, n_sessions, n_trials, kappa, rng, theta=None, mu=MU, sigma_participant=0.4, condition="standard"
):
    """The generative story, executable. Returns (sessions, trials, theta, p_session)."""
    if theta is None:
        theta = rng.normal(mu, sigma_participant, n_participants)  # each participant's ability, logit scale

    p = expit(theta)
    p_session = rng.beta(p[:, None] * kappa, (1 - p[:, None]) * kappa, (n_participants, n_sessions))  # the wobble
    correct = rng.binomial(1, p_session[:, :, None], size=(n_participants, n_sessions, n_trials))

    index = pd.MultiIndex.from_product(
        [range(1, n_participants + 1), range(1, n_sessions + 1), range(1, n_trials + 1)],
        names=["participant", "session", "trial"],
    )
    trials = pd.DataFrame({"correct": correct.ravel()}, index=index).reset_index().assign(condition=condition)
    sessions = trials.groupby(["participant", "session", "condition"], sort=False, as_index=False).agg(
        n_trials=("correct", "size"), n_correct=("correct", "sum")
    )

    return sessions, trials, theta, p_session


@dataclass(frozen=True)
class Truth:
    mu: float
    beta: float
    sigma_participant: float
    kappa: float
    theta: np.ndarray  # (P,)
    p_session: np.ndarray  # (P, S, C)
    seed: int
    n_participants: int
    n_sessions: int
    n_trials: int
    conditions: tuple[str, ...]

    @property
    def sd_between_sessions(self) -> float:
        return sd_from_kappa(self.kappa, p=float(expit(self.mu)))

    def scalars(self) -> dict:
        return {
            "mu": self.mu,
            "beta": self.beta,
            "sigma_participant": self.sigma_participant,
            "kappa": self.kappa,
            "sd_between_sessions": self.sd_between_sessions,
            "seed": self.seed,
            "n_participants": self.n_participants,
            "n_sessions": self.n_sessions,
            "n_trials": self.n_trials,
            "conditions": list(self.conditions),
        }


@dataclass(frozen=True)
class SimulatedStudy:
    sessions: pd.DataFrame
    trials: pd.DataFrame
    truth: Truth


def simulate_study(
    *,
    n_participants: int = 40,
    n_sessions: int = 5,
    n_trials: int = 100,
    conditions: tuple[str, ...] = ("standard", "hard"),
    mu: float = MU,
    beta: float = -0.5,
    sigma_participant: float = 0.4,
    kappa: float = 42.0,
    seed: int = RANDOM_SEED,
) -> SimulatedStudy:
    """Full study: one participant-ability draw, then one `simulate_sessions` call per condition."""
    rng = np.random.default_rng(seed)
    theta = rng.normal(mu, sigma_participant, size=n_participants)
    sessions, trials, p_sessions = [], [], []
    for cond in conditions:
        shift = 0.0 if cond == conditions[0] else beta
        s, t, _, ps = simulate_sessions(
            n_participants=n_participants,
            n_sessions=n_sessions,
            n_trials=n_trials,
            kappa=kappa,
            rng=rng,
            theta=theta + shift,
            condition=cond,
        )
        sessions.append(s)
        trials.append(t)
        p_sessions.append(ps)
    sort_keys = ["participant", "session"]
    sessions_df = pd.concat(sessions).sort_values(sort_keys, kind="stable").reset_index(drop=True)
    trials_df = pd.concat(trials).sort_values(sort_keys, kind="stable").reset_index(drop=True)
    truth = Truth(
        mu=mu,
        beta=beta,
        sigma_participant=sigma_participant,
        kappa=kappa,
        theta=theta,
        p_session=np.stack(p_sessions, axis=-1),
        seed=seed,
        n_participants=n_participants,
        n_sessions=n_sessions,
        n_trials=n_trials,
        conditions=tuple(conditions),
    )
    return SimulatedStudy(sessions=sessions_df, trials=trials_df, truth=truth)


def variance_ratio(sessions):
    """Observed variance of session accuracy / the variance a stable ability would produce (1 = noise alone)."""

    def ratio(group):
        p = group["n_correct"].sum() / group["n_trials"].sum()
        return (group["n_correct"] / group["n_trials"]).var(ddof=1) / (p * (1 - p) / group["n_trials"]).mean()

    return sessions.groupby(["participant", "condition"]).apply(ratio, include_groups=False)


def write_study(study: SimulatedStudy, data_dir: Path | str) -> None:
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    t = study.truth
    study.sessions.to_csv(data_dir / "sessions.csv", index=False)
    study.trials.to_csv(data_dir / "trials.csv", index=False)
    (data_dir / "truth.json").write_text(json.dumps(t.scalars(), indent=2) + "\n")
    participants = pd.DataFrame({"participant": np.arange(1, t.n_participants + 1), "theta": t.theta})
    for c_idx, cond in enumerate(t.conditions):
        shift = 0.0 if c_idx == 0 else t.beta
        participants[f"p_{cond}"] = expit(t.theta + shift)
    participants.to_csv(data_dir / "truth_participants.csv", index=False)
    pid, sid, cid = np.meshgrid(
        np.arange(1, t.n_participants + 1),
        np.arange(1, t.n_sessions + 1),
        np.arange(len(t.conditions)),
        indexing="ij",
    )
    pd.DataFrame(
        {
            "participant": pid.ravel(),
            "session": sid.ravel(),
            "condition": np.array(t.conditions)[cid.ravel()],
            "p_true": t.p_session.ravel(),
        }
    ).to_csv(data_dir / "truth_sessions.csv", index=False)
