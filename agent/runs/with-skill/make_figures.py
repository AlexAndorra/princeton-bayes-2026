"""Two lab-meeting figures: per-participant accuracy by condition (95% CI),
and the posterior of the population-level condition effect."""
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RESULTS_DIR = "accuracy-hierarchical"

BLUE = "#2a78d6"   # standard
ORANGE = "#eb6834"  # hard
GRID = "#d9d9d6"
TEXT = "#3a3a38"

plt.rcParams.update({
    "axes.edgecolor": GRID,
    "axes.labelcolor": TEXT,
    "text.color": TEXT,
    "xtick.color": TEXT,
    "ytick.color": TEXT,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "font.size": 10,
})

# --- Figure 1: per-participant accuracy by condition, sorted by standard accuracy ---
df = pd.read_csv(f"{RESULTS_DIR}/participant_accuracy.csv")
wide = df.pivot(index="participant", columns="condition", values=["accuracy_mean", "hdi_2.5%", "hdi_97.5%"])
order = wide[("accuracy_mean", "standard")].sort_values().index
y = np.arange(len(order))

fig, ax = plt.subplots(figsize=(6.5, 8))
for j, pid in enumerate(order):
    std_mean = wide.loc[pid, ("accuracy_mean", "standard")]
    hard_mean = wide.loc[pid, ("accuracy_mean", "hard")]
    ax.plot([std_mean, hard_mean], [j, j], color=GRID, lw=1, zorder=1)

for cond, color, offset in [("standard", BLUE, 0), ("hard", ORANGE, 0)]:
    means = wide.loc[order, ("accuracy_mean", cond)].to_numpy()
    los = wide.loc[order, ("hdi_2.5%", cond)].to_numpy()
    his = wide.loc[order, ("hdi_97.5%", cond)].to_numpy()
    ax.errorbar(
        means, y, xerr=[means - los, his - means],
        fmt="o", color=color, ecolor=color, elinewidth=1.2, capsize=0,
        markersize=4, label=cond.capitalize(), zorder=2,
    )

ax.set_yticks(y)
ax.set_yticklabels(order, fontsize=6)
ax.set_ylabel("Participant (sorted by standard-condition accuracy)")
ax.set_xlabel("Accuracy (posterior mean, 95% credible interval)")
ax.set_xlim(0.2, 1.0)
ax.legend(loc="lower right", frameon=False)
ax.set_title("Per-participant accuracy by condition", loc="left", fontsize=12)
fig.tight_layout()
fig.savefig(f"{RESULTS_DIR}/fig1_participant_accuracy.png", dpi=150)
plt.close(fig)

# --- Figure 2: posterior of the population-level condition effect ---
import arviz as az
idata = az.from_netcdf(f"{RESULTS_DIR}/inference_data.nc")
post = idata.posterior
pop_standard = 1 / (1 + np.exp(-post["mu_alpha"]))
pop_hard = 1 / (1 + np.exp(-(post["mu_alpha"] + post["mu_beta"])))
diff = (pop_standard - pop_hard).values.flatten()

with open(f"{RESULTS_DIR}/population_effect.json") as f:
    stats = json.load(f)
lo, hi = stats["pop_diff_hdi95"]
mean = stats["pop_diff_mean"]

fig, ax = plt.subplots(figsize=(6.5, 3.5))
ax.hist(diff, bins=40, color=BLUE, alpha=0.85, edgecolor="white", linewidth=0.3)
ax.axvspan(lo, hi, color=ORANGE, alpha=0.15, zorder=0)
ax.axvline(mean, color=ORANGE, lw=2)
ax.set_xlabel("Accuracy-point difference (standard − hard)")
ax.set_ylabel("Posterior draws")
ax.set_title(
    f"Population-level condition effect: {mean*100:.1f} points "
    f"(95% HDI [{lo*100:.1f}, {hi*100:.1f}])",
    loc="left", fontsize=11,
)
ax.set_yticks([])
fig.tight_layout()
fig.savefig(f"{RESULTS_DIR}/fig2_condition_effect.png", dpi=150)
plt.close(fig)

print("Saved fig1_participant_accuracy.png and fig2_condition_effect.png")
