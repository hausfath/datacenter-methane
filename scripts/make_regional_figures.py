"""Regional figures (PLAN_regional §7): heatmap of % gap vs the regional grid, and basin-range bars. All numbers from results/regional/."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

ROOT = Path(__file__).resolve().parents[1]
d = pd.read_csv(ROOT / 'results/regional/regional_cases.csv')
J = json.load(open(ROOT / 'data/basin_leak_rates.json'))
INK, INK2, MUTED, GRIDC, SURF = '#0b0b0b', '#52514e', '#8a8984', '#e6e5e1', '#fcfcfb'
CMAP = LinearSegmentedColormap.from_list('bwr_ds', ['#184f95', '#6da7ec', '#f0efec', '#f19a99', '#b8302f'])
REG_ORDER = ['West Texas', 'Texas Panhandle', 'El Paso / S. NM', 'PJM', 'Memphis', 'Central Utah', 'Cheyenne']
REG_LABEL = {'West Texas': 'West Texas (ERCOT)', 'Texas Panhandle': 'Texas Panhandle (SPP)', 'El Paso / S. NM': 'El Paso / S. New Mexico',
             'PJM': 'Ohio, PA, WV, VA (PJM)', 'Memphis': 'Memphis (TVA)', 'Central Utah': 'Central Utah (PacifiCorp)',
             'Cheyenne': 'Cheyenne, WY (WAPA)'}
BASIN_SHORT = {'Permian (Texas)': 'Permian TX', 'Anadarko (high: Permian TX)': 'Anadarko', 'Permian (Delaware, NM+TX)': 'Delaware',
               'Appalachia (Marcellus/Utica)': 'Appalachia', 'Haynesville': 'Haynesville',
               'Rockies via Kern River: GGR central, Uinta/Piceance high': 'Green River',
               'Rockies: DJ central (most BTM-favourable), GGR high': 'Denver-Julesburg'}
CASES = ['Recip engines (lean-burn)', 'Simple-cycle turbines', 'Fuel cells (Bloom SOFC)', 'Combined cycle (on site)']
CASE_LABEL = ['Reciprocating\nengines', 'Simple-cycle\nturbines', 'Fuel cells\n(Bloom)', 'On-site\ncombined cycle']
STATE_TXT = {'Worse': 'worse than grid', 'Tied': 'tied', 'Better': 'better than grid', 'Between (above A)': 'above average,\ntied new gas',
             'Between (above B)': 'tied/below average,\nabove new gas', 'Below A, tied B': 'below average,\ntied new gas',
             'Tied A, below B': 'tied average,\nbelow new gas'}
OUT = ROOT / 'figures'

p = d[(d.pairing == 'matched') & (d.L_level == 'central') & (d.grid_basis == 'EIA-930 consumption 2025') & (d.gwp == 'AR6_100')]
p = p.set_index(['region', 'case'])


def cell_text(row):
    if row.state == 'Worse':
        return 'worse than grid'
    if row.state == 'Tied':
        return 'tied with grid'
    if row.state == 'Better':
        return 'better than grid'
    return f'{row.vA} avg · {row.vB} new gas'

regions = J['regions_R2']

# ------------------------------------------------------------------ heatmap
fig = plt.figure(figsize=(13.33, 7.5), dpi=150, facecolor=SURF)
ax = fig.add_axes([0.255, 0.13, 0.60, 0.635], facecolor=SURF)
M = np.array([[p.loc[(r, c), 'rel_A'] * 100 for c in CASES] for r in REG_ORDER])
norm = TwoSlopeNorm(vmin=-60, vcenter=0, vmax=120)
ax.imshow(M, cmap=CMAP, norm=norm, aspect='auto')
for i, r in enumerate(REG_ORDER):
    for j, c in enumerate(CASES):
        row = p.loc[(r, c)]
        val = row.rel_A * 100
        rgb = CMAP(norm(val))[:3]
        lum = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
        col = SURF if lum < 0.45 else INK
        ax.text(j, i - 0.13, f'{val:+.0f}%', ha='center', va='center', fontsize=15, fontweight='bold', color=col)
        ax.text(j, i + 0.24, cell_text(row), ha='center', va='center', fontsize=9.5, color=col)
for k in range(len(REG_ORDER) + 1):
    ax.axhline(k - 0.5, color=SURF, lw=3)
for k in range(len(CASES) + 1):
    ax.axvline(k - 0.5, color=SURF, lw=3)
ax.set_xticks(range(len(CASES)), CASE_LABEL, fontsize=12, color=INK)
ax.xaxis.tick_top()
ax.set_yticks(range(len(REG_ORDER)), [REG_LABEL[r] for r in REG_ORDER], fontsize=12, color=INK)
ax.tick_params(length=0)
for s in ax.spines.values():
    s.set_visible(False)
# right-side context column
for i, r in enumerate(REG_ORDER):
    row = p.loc[(r, CASES[0])]
    bas = regions[r]['basin']
    ax.text(3.62, i - 0.12, f'grid {row.A:.0f}', ha='left', va='center', fontsize=10.5, color=INK2)
    ax.text(3.62, i + 0.22, f'{BASIN_SHORT[bas]} {row.L_btm * 100:.1f}%', ha='left', va='center', fontsize=9.5, color=MUTED)
ax.text(3.62, -0.88, 'grid kg/MWh\ngas leak rate', ha='left', va='bottom', fontsize=9.5, color=MUTED)

worse_both = [r for r in REG_ORDER if p.loc[(r, CASES[0]), 'state'] == 'Worse' and p.loc[(r, CASES[1]), 'state'] == 'Worse']
fig.text(0.04, 0.955, f'Engines and turbines at data centers emit more than the local grid in {len(worse_both)} of {len(REG_ORDER)} hotspots',
         fontsize=19, fontweight='bold', color=INK, va='top')
eff_tied_B = all(p.loc[(r, c), 'vB'] == 'tied' for r in REG_ORDER for c in CASES[2:])
exc = [REG_LABEL[r].split(' (')[0].split(',')[0] for r in REG_ORDER if r not in worse_both]
fig.text(0.04, 0.898, 'Life-cycle emissions of off-grid gas vs the regional grid average (% difference, 100-year GWP), with each region\'s own gas-basin\n'
         f'leak rate on both sides. The exception is coal-heavy {" and ".join(exc)}.'
         + (' Fuel cells and on-site combined cycle tie a new grid gas plant everywhere.' if eff_tied_B else ''),
         fontsize=12.5, color=INK2, va='top', linespacing=1.4)
fig.text(0.04, 0.03,
         'Grid: EIA-930 2025 consumption-based CO$_2$ intensity by balancing authority, plus upstream gas leaks, coal-mine methane and 3% transmission loss. '
         '"Tied" = within\nthe 90% Monte Carlo range. Leak rates: MacKay et al. 2026, Varon et al. 2026, Bridger 2024, AMI 2026, Sherwin et al. 2024 (corrected). '
         'Wyoming uses DJ-basin gas, the case most\nfavourable to on-site gas; Utah\'s verdict depends on the Green River leak rate (low confidence). SPP uses 2024. Analysis: Zeke Hausfather / The Climate Brink',
         fontsize=9.3, color=MUTED, va='bottom', linespacing=1.45)
fig.savefig(OUT / 'regional_heatmap.png', dpi=150, facecolor=SURF)
plt.close(fig)

# ------------------------------------------------------------------ basin-range bars
C4 = {'Recip engines (lean-burn)': '#e34948', 'Simple-cycle turbines': '#eda100', 'Fuel cells (Bloom SOFC)': '#1baf7a',
      'Combined cycle (on site)': '#2a78d6'}
m = d[(d.pairing == 'matched') & (d.grid_basis == 'EIA-930 consumption 2025') & (d.gwp == 'AR6_100')].set_index(['region', 'case', 'L_level'])
fig, axes = plt.subplots(2, 4, figsize=(13.33, 7.5), dpi=150, facecolor=SURF, sharex=True)
fig.subplots_adjust(left=0.04, right=0.985, top=0.765, bottom=0.17, wspace=0.08, hspace=0.50)
xmax = m.btm.max() * 1.05
for k, (ax, r) in enumerate(zip(axes.flat, REG_ORDER)):
    ax.set_facecolor(SURF)
    a_lo, a_hi = sorted([m.loc[(r, CASES[0], 'low'), 'A'], m.loc[(r, CASES[0], 'high'), 'A']])
    b_lo, b_hi = sorted([m.loc[(r, CASES[0], 'low'), 'B'], m.loc[(r, CASES[0], 'high'), 'B']])
    ax.axvspan(a_lo, a_hi, color=MUTED, alpha=0.28, lw=0)
    ax.axvspan(b_lo, b_hi, facecolor='none', edgecolor=INK2, hatch='///', lw=0, alpha=0.6)
    for j, c in enumerate(CASES):
        y = len(CASES) - 1 - j
        lo, mid, hi = (m.loc[(r, c, lev), 'btm'] for lev in ('low', 'central', 'high'))
        ax.plot([lo, hi], [y, y], color=C4[c], lw=6, solid_capstyle='round', alpha=0.55)
        ax.plot([mid], [y], 'o', ms=8, color=C4[c], mec=SURF, mew=1.5)
    L = J['basins'][regions[r]['basin']]['L']
    ax.set_title(f'{REG_LABEL[r]}\n{BASIN_SHORT[regions[r]["basin"]]} gas, leak {L[0]*100:.1f}–{L[2]*100:.1f}%', fontsize=11, color=INK, loc='left', pad=6)
    ax.set_yticks([])
    ax.set_xlim(250, xmax)
    ax.set_ylim(-0.7, len(CASES) - 0.3)
    ax.xaxis.grid(True, color=GRIDC, lw=0.8)
    ax.set_axisbelow(True)
    for s in ['top', 'right', 'left']:
        ax.spines[s].set_visible(False)
    ax.spines['bottom'].set_color(MUTED)
    ax.tick_params(axis='x', labelsize=10, colors=INK2, labelbottom=True)
# legend panel
lg = axes.flat[-1]
lg.axis('off')
handles = [plt.Line2D([], [], color=C4[c], lw=6, alpha=0.55, marker='o', ms=8, mfc=C4[c], mec=SURF) for c in CASES] + \
          [plt.Rectangle((0, 0), 1, 1, color=MUTED, alpha=0.28), plt.Rectangle((0, 0), 1, 1, facecolor='none', edgecolor=INK2, hatch='///')]
labels = [l.replace('\n', ' ') for l in CASE_LABEL] + ['Regional grid average', 'New grid gas plant']
lg.legend(handles, labels, loc='upper left', bbox_to_anchor=(0.0, 1.02), frameon=False, fontsize=11, labelcolor=INK, handlelength=2.2, borderaxespad=0)
lg.text(0.0, -0.08, 'Bars span the basin\'s low to high leak rate;\ndots mark the central estimate.\nGrid bands use the same leak range.',
        transform=lg.transAxes, fontsize=9.5, color=INK2, va='bottom')
fig.text(0.5, 0.115, 'kg CO$_2$-equivalent per MWh delivered (100-year GWP)', ha='center', fontsize=12, color=INK)
swing = (m.xs('high', level='L_level').btm - m.xs('low', level='L_level').btm)
swing = swing[swing.index.get_level_values('case').isin(CASES)]
r_max, c_max = swing.idxmax()
Lr = J['basins'][regions[r_max]['basin']]['L']
fig.text(0.04, 0.955, f'Gas leak rates swing off-grid power by up to {swing.max():.0f} kg CO$_2$e per MWh', fontsize=19, fontweight='bold', color=INK, va='top')
fig.text(0.04, 0.898, f'Off-grid gas at data-center hotspots across each supply basin\'s measured leak-rate range (largest swing: {REG_LABEL[r_max].split(" (")[0]}, {Lr[0]*100:.1f}–{Lr[2]*100:.1f}%),\nagainst the regional grid average and a new grid gas plant',
         fontsize=12.5, color=INK2, va='top', linespacing=1.4)
fig.text(0.04, 0.03, 'Grid: EIA-930 2025 consumption-based intensity + upstream gas, coal-mine methane, 3% transmission loss. Leak rates: MacKay et al. 2026, Varon et al. 2026, '
         'Bridger 2024,\nAMI 2026, Sherwin et al. 2024 (corrected). Green River 5.2% is low confidence; the Utah low end (1.2%) assumes certified Rockies gas. Analysis: Zeke Hausfather / The Climate Brink',
         fontsize=9.3, color=MUTED, va='bottom', linespacing=1.45)
fig.savefig(OUT / 'regional_basin_ranges.png', dpi=150, facecolor=SURF)
print('worse in', len(worse_both), 'of', len(REG_ORDER))
