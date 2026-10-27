"""Shareable 16:9 figure: off-grid gas vs the grid under seven ways of counting grid emissions (PLAN_marginal v2).

Small multiples (ERCOT, PJM, US). Rows = grid metrics ordered by horizon; dots = central values; bars = the pre-registered
range (SRMER: specification envelope, with the bootstrap 90% CI as a thicker inner bar; Cambium: 8 scenarios; blend:
w = 0.15-0.35; build margins: definitional variants). Off-grid options are vertical bands. All text is computed from
results/marginal/grid_definitions.csv and verdicts.csv.
"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cases import L_PRIMARY, btm, tot

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / 'results' / 'marginal'
m = pd.read_csv(R / 'grid_definitions.csv')
v = pd.read_csv(R / 'verdicts.csv')

INK, INK2, MUTED, GRIDC, SURF = '#0b0b0b', '#52514e', '#8a8984', '#e6e5e1', '#fcfcfb'
FAM = {'average': '#8a8984', 'srmer': '#d1561e', 'blend': '#8a4fb5', 'cambium': '#2a78d6', 'planned': '#2a78d6',
       'recent': '#2a78d6', 'ngcc': '#7a5a2e'}
ORDER = ['average', 'srmer', 'blend', 'cambium', 'planned', 'recent', 'ngcc']
LABEL = {'average': 'Grid average (used in the post)', 'srmer': 'Short-run marginal (2025 data)',
         'blend': 'Blend: 5 yrs short-run, then long-run', 'cambium': 'Long-run marginal (NREL Cambium)',
         'planned': 'Average of planned additions, 2026–30', 'recent': 'Average of recent additions',
         'ngcc': 'New gas plant built on the grid'}
ENG = [tot(btm(c, L_PRIMARY)) for c in ('Simple-cycle turbines', 'Recip engines (lean-burn)')]
EFF = [tot(btm(c, L_PRIMARY)) for c in ('Fuel cells (Bloom SOFC)', 'Combined cycle (on site)')]
REGIONS = [('ERCOT', 'ERCOT (Texas)'), ('PJM', 'PJM (Mid-Atlantic)'), ('US', 'United States')]

fig = plt.figure(figsize=(13.33, 7.5), dpi=150, facecolor=SURF)
y = {k: len(ORDER) - 1 - i + (0.45 if i < 2 else 0) for i, k in enumerate(ORDER)}   # extra gap below the 'today' rows
xmax = max(950, float(np.nanmax(m[['central', 'hi']].values)) * 1.05)
axes = []
for j, (reg, title) in enumerate(REGIONS):
    ax = fig.add_axes([0.285 + j * 0.238, 0.20, 0.215, 0.535], facecolor=SURF)
    axes.append(ax)
    ax.axvspan(min(ENG), max(ENG), color='#e34948', alpha=0.28, lw=0, zorder=0)
    ax.axvspan(min(EFF), max(EFF), color='#1baf7a', alpha=0.28, lw=0, zorder=0)
    mm = m[m.region == reg].set_index('metric')
    for k in ORDER:
        r = mm.loc[k]
        c = FAM[k]
        if not np.isnan(r.lo):
            ax.plot([r.lo, r.hi], [y[k]] * 2, color=c, lw=2, alpha=0.55, solid_capstyle='round', zorder=2)
        if k == 'srmer' and not np.isnan(r.get('ci05', np.nan)):
            ax.plot([r.ci05, r.ci95], [y[k]] * 2, color=c, lw=5, solid_capstyle='round', zorder=3)
        ax.plot([r.central], [y[k]], marker='o', ms=9, mfc=c, mec=SURF, mew=1.5, zorder=4)
        hi = r.hi if not np.isnan(r.hi) else r.central
        ax.text(hi + 18 if hi < xmax * 0.86 else (r.lo if not np.isnan(r.lo) else r.central) - 18, y[k] + 0.0,
                f'{r.central:,.0f}', va='center', ha='left' if hi < xmax * 0.86 else 'right', fontsize=10, color=INK2)
    ax.axhline(y['srmer'] - 0.62, color=MUTED, lw=0.8, ls=(0, (3, 3)))   # 'today' rows above, 20-year rows below
    ax.set_xlim(0, xmax)
    ax.set_ylim(-0.7, len(ORDER) + 0.2)
    ax.set_yticks([])
    ax.set_title(title, fontsize=13, color=INK, fontweight='bold', loc='left', pad=8)
    ax.tick_params(axis='x', labelsize=10.5, colors=INK2)
    ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(250))
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda val, _: f'{val:,.0f}'))
    ax.xaxis.grid(True, color=GRIDC, lw=0.8)
    ax.set_axisbelow(True)
    for s in ['top', 'right', 'left']:
        ax.spines[s].set_visible(False)
    ax.spines['bottom'].set_color(MUTED)
for k in ORDER:
    axes[0].text(-0.06 * xmax, y[k], LABEL[k], ha='right', va='center', fontsize=11.5, color=INK, transform=axes[0].transData)
axes[0].text(-0.06 * xmax, y['average'] + 0.45, 'GRID TODAY', ha='right', va='bottom', fontsize=9.5, color=INK2, fontweight='bold')
axes[0].text(-0.06 * xmax, y['srmer'] - 0.7, 'GRID OVER A 20-YEAR DATA-CENTER LIFE', ha='right', va='top', fontsize=9.5, color=INK2, fontweight='bold')
fig.text(0.285 + 0.238 + 0.1075, 0.135, 'kg CO$_2$-equivalent per MWh delivered (100-year GWP, 2.3% methane leakage on both sides)',
         ha='center', fontsize=11.5, color=INK)

# legend for the off-grid bands
h = [plt.Rectangle((0, 0), 1, 1, color='#e34948', alpha=0.45), plt.Rectangle((0, 0), 1, 1, color='#1baf7a', alpha=0.45)]
fig.legend(h, [f'Off-grid gas engines and turbines ({min(ENG):,.0f}–{max(ENG):,.0f})',
               f'Off-grid fuel cells and combined cycle ({min(EFF):,.0f}–{max(EFF):,.0f})'],
           loc='lower left', bbox_to_anchor=(0.285, 0.77), ncol=2, frameon=False, fontsize=11, handlelength=1.4, labelcolor=INK)

# computed headline and subtitle from the verdicts
NAME = {'ERCOT': 'ERCOT', 'PJM': 'PJM', 'US': 'the US'}
WORD = {'worse': 'dirtier than', 'tie': 'level with', 'better': 'cleaner than'}
SHORT = {'worse': 'dirtier', 'tie': 'level', 'better': 'cleaner'}


def by_verdict(opts, metric):
    """{verdict: [regions]} if every option in opts shares a verdict within each region, else None."""
    out = {}
    for reg, _ in REGIONS:
        vs = set(v[(v.region == reg) & (v.metric == metric) & v.option.isin(opts)].verdict)
        if len(vs) != 1:
            return None
        out.setdefault(vs.pop(), []).append(NAME[reg])
    return out


def phrase(groups, first='the grid'):
    parts = [f"{WORD[k]} {first} in {' and '.join(rs)}" if i == 0 else f"{SHORT[k]} in {' and '.join(rs)}"
             for i, (k, rs) in enumerate(groups.items())]
    return ', '.join(parts[:-1]) + (' and ' if len(parts) > 1 else '') + parts[-1]


ENGS = ['Recip engines (lean-burn)', 'Simple-cycle turbines']
EFFS = ['Fuel cells (Bloom SOFC)', 'Combined cycle (on site)']
lr = v[v.option.isin(ENGS) & v.metric.isin(['blend', 'cambium', 'planned', 'recent', 'ngcc'])]
assert (lr.verdict == 'worse').all(), 'title assumes engines/turbines are worse on every long-run metric'
lr_min = np.floor(lr.ratio.min() * 10) / 10
title = f"Off-grid engines and turbines emit {lr_min:.1f}× or more than the grid on any long-run measure"
sre = v[v.option.isin(ENGS) & (v.metric == 'srmer')].ratio
srf = v[v.option.isin(EFFS) & (v.metric == 'srmer')].ratio
r1 = lambda x: f'{x:.1f}'
sub = (f"Against today's short-run marginal grid the comparison is much closer: engines and turbines emit {r1(sre.min())}–{r1(sre.max())}× as much as the grid\n"
       f"across ERCOT, PJM and the US, and fuel cells and on-site combined cycle {r1(srf.min())}–{r1(srf.max())}×.\n"
       f"Dots: central estimates. Bars: range across methods or scenarios.")
fig.text(0.04, 0.955, title, fontsize=17.5, fontweight='bold', color=INK, va='top')
fig.text(0.04, 0.903, sub, fontsize=12, color=INK2, va='top', linespacing=1.45)
fig.text(0.04, 0.03,
         "Short-run: EPA CEMS hourly emissions regressed on EIA-930 demand with wind/solar controls, 2025 (Holland et al. 2022 method, reproduced for Jan–Sep 2019), 6% marginal\n"
         "losses; thick bar = 90% CI. Long-run: NREL Cambium 2024 High Demand Growth, 2027–46, with Aug 2024 policies (before OBBBA and EPA's 2026 partial repeal of its\n"
         "power-plant rule), so likely too low. "
         "Blend: Gagnon & O'Shaughnessy 2024, weight 0.25 on short-run (0.15–0.35). Additions: EIA-860M Sep 2026 and EIA-923 2025; annual energy, not hourly.\n"
         "All grid values add upstream gas and coal-mine methane at the same leak rate as the off-grid side.   Analysis: Zeke Hausfather / The Climate Brink",
         fontsize=9.2, color=MUTED, va='bottom', linespacing=1.45)
out = ROOT / 'figures' / 'marginal_vs_average.png'
fig.savefig(out, dpi=150, facecolor=SURF)
print('saved', out.name, '|', title, '|', sub)
