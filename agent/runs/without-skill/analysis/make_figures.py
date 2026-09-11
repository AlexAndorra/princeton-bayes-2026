"""Builds the two report figures from the Part 1 (participant_accuracy.csv) and
Part 2 (inference_data.zarr) outputs. Colors are the first two slots of the
validated categorical palette from the dataviz skill (CVD-safe, fixed order):
blue = standard (#2a78d6), orange = hard (#eb6834).
"""

import arviz as az
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

BLUE = "#2a78d6"      # standard
ORANGE = "#eb6834"    # hard
INK = "#0b0b0b"
MUTED = "#898781"
GRID = "#e1e0d9"
SURFACE = "#fcfcfb"

plt.rcParams.update({
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "axes.edgecolor": MUTED,
    "text.color": INK,
    "axes.labelcolor": INK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "font.family": "sans-serif",
    "axes.grid": False,
})

# ---------------------------------------------------------------------------
# Figure 1: per-participant accuracy, standard vs. hard, with 95% CIs
# ---------------------------------------------------------------------------
acc = pd.read_csv("analysis/participant_accuracy.csv")
wide = acc.pivot(index="participant", columns="condition",
                  values=["accuracy", "ci95_low", "ci95_high"])
order = wide[("accuracy", "standard")].sort_values(ascending=True).index
wide = wide.loc[order]
y = np.arange(len(wide))

fig, ax = plt.subplots(figsize=(7.5, 10))

for cond, color, offset in [("standard", BLUE, 0.14), ("hard", ORANGE, -0.14)]:
    yy = y + offset
    x = wide[("accuracy", cond)].to_numpy()
    lo = wide[("ci95_low", cond)].to_numpy()
    hi = wide[("ci95_high", cond)].to_numpy()
    ax.hlines(yy, lo, hi, color=color, linewidth=2, alpha=0.9, zorder=2)
    ax.scatter(x, yy, s=26, color=color, label=cond.capitalize(), zorder=3,
               edgecolors=SURFACE, linewidths=0.5)

# connect each participant's two condition means to make the paired contrast readable
for i, p in enumerate(wide.index):
    xs = wide.loc[p, ("accuracy", "standard")], wide.loc[p, ("accuracy", "hard")]
    ax.plot(xs, [y[i] + 0.14, y[i] - 0.14], color=GRID, linewidth=1, zorder=1)

ax.set_yticks(y)
ax.set_yticklabels(wide.index, fontsize=7)
ax.set_ylabel("Participant (sorted by standard-condition accuracy)")
ax.set_xlabel("Accuracy (95% credible interval)")
ax.set_xlim(0.2, 1.0)
ax.set_title("Per-participant accuracy by condition", loc="left", fontweight="bold")
ax.spines[["top", "right"]].set_visible(False)
ax.tick_params(axis="y", length=0)
ax.xaxis.grid(True, color=GRID, linewidth=0.8, zorder=0)
ax.legend(loc="lower right", frameon=False)
fig.tight_layout()
fig.savefig("figures/fig1_participant_accuracy.png", dpi=200, facecolor=SURFACE)
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure 2: population-level condition effect (posterior of accuracy difference)
# ---------------------------------------------------------------------------
idata = xr.open_datatree("analysis/inference_data.zarr", engine="zarr")
post = idata["posterior"].ds

acc_standard = 1 / (1 + np.exp(-post["mu_intercept"]))
acc_hard = 1 / (1 + np.exp(-(post["mu_intercept"] + post["mu_slope"])))
diff_da = (acc_hard - acc_standard) * 100  # percentage points, keeps chain/draw dims
diff_pp = diff_da.to_numpy().ravel()

hdi = az.hdi(diff_da, prob=0.95).to_numpy()
mean_diff = diff_pp.mean()

fig, ax = plt.subplots(figsize=(7.5, 4))
ax.hist(diff_pp, bins=60, color=ORANGE, alpha=0.85, density=True)
ax.axvline(0, color=INK, linewidth=1.2, linestyle="--", zorder=3)
ax.axvline(mean_diff, color=INK, linewidth=1.5, zorder=3)
ax.axvspan(hdi[0], hdi[1], color=ORANGE, alpha=0.12, zorder=0)

ax.set_xlabel("Accuracy difference, hard − standard (percentage points)")
ax.set_ylabel("Posterior density")
ax.set_title(
    "Population-level effect of condition on accuracy\n"
    f"mean = {mean_diff:.1f} pp, 95% HDI [{hdi[0]:.1f}, {hdi[1]:.1f}] pp",
    loc="left", fontweight="bold", fontsize=11,
)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.set_yticks([])
ax.tick_params(axis="y", length=0)
fig.tight_layout()
fig.savefig("figures/fig2_condition_effect.png", dpi=200, facecolor=SURFACE)
plt.close(fig)

print(f"Fig 2 numbers: mean={mean_diff:.2f} pp, 95% HDI=[{hdi[0]:.2f}, {hdi[1]:.2f}] pp")
print("Saved figures/fig1_participant_accuracy.png and figures/fig2_condition_effect.png")
