"""Regenerate data/ from the committed seed. Run: uv run python scripts/make_data.py"""

from pathlib import Path

from psychsim.simulate import simulate_study, write_study

if __name__ == "__main__":
    study = simulate_study()
    out = Path(__file__).resolve().parents[1] / "data"
    write_study(study, out)
    t = study.truth
    print(f"wrote {out}: {len(study.sessions)} session rows, {len(study.trials)} trial rows")
    print(
        f"truth: mu={t.mu:.3f} beta={t.beta} sigma_participant={t.sigma_participant} kappa={t.kappa} "
        f"sd_between_sessions={t.sd_between_sessions:.4f} seed={t.seed}"
    )
