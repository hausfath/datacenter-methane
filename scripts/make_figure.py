"""Main 16:9 figure: life-cycle kg CO2e per MWh delivered, off-grid gas options vs grid, at matched L = 2.3%, GWP100.

All displayed numbers are computed from results/cases.csv, results/decision_table.csv and data/planned_technology_shares.json.
The small rich-burn genset case (one project, Meta El Paso) stays in cases.csv and METHODS but is not drawn.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
cases = pd.read_csv(ROOT / 'results/cases.csv')
dec = pd.read_csv(ROOT / 'results/decision_table.csv')
L_LABEL = 'National measured (2.3%)'

C = dict(co2_combustion='#2a78d6', co2_supply='#1baf7a', ch4_upstream='#eda100', ch4_slip='#e34948')
LEG = dict(co2_combustion='CO$_2$ from burning fuel', co2_supply='CO$_2$ from producing and moving gas',
           ch4_upstream='Methane leaked upstream (gas wells, pipes, coal mines)', ch4_slip='Methane slipping unburned out of engines')
INK, INK2, MUTED, GRIDC, SURF = '#0b0b0b', '#52514e', '#8a8984', '#e6e5e1', '#fcfcfb'

c100 = cases[(cases.leak == L_LABEL) & (cases.gwp == 'AR6_100')].copy()
c20 = cases[(cases.leak == L_LABEL) & (cases.gwp == 'AR6_20')].copy()
for d in (c100, c20):
    d['ch4_upstream'] = d['ch4_upstream'] + d.get('ch4_coal_mine', 0) + d['ch4_facility']
    d['co2_combustion'] = d['co2_combustion'] + d['n2o']

btm = c100[(c100.kind == 'BTM') & (c100.name != 'Small rich-burn gensets')].sort_values('total', ascending=True)

# share of identified planned BTM capacity by technology (our grouping of Cleanview's equipment data; data file notes)
SHARE = {k: v for k, v in json.load(open(ROOT / 'data/planned_technology_shares.json'))['technology_share'].items() if v > 0}
grid_names = ['US grid average', 'PJM grid average', 'ERCOT grid average', 'New grid NGCC']
grid = c100[c100.kind != 'BTM'].set_index('name').loc[grid_names].reset_index()
LABEL = {'Recip engines (lean-burn)': 'Reciprocating engines (lean-burn)',
         'Simple-cycle turbines': 'Simple-cycle gas turbines',
         'Fuel cells (Bloom SOFC)': 'Solid-oxide fuel cells (Bloom)',
         'Combined cycle (on site)': 'On-site combined-cycle plant',
         'Small rich-burn gensets': 'Small rich-burn gensets',
         'US grid average': 'US grid, 2023 average', 'PJM grid average': 'PJM grid, 2023 average',
         'ERCOT grid average': 'ERCOT grid, 2023 average', 'New grid NGCC': 'New grid combined-cycle gas plant'}

# rows from bottom: grid group, gap, BTM group (highest total at top)
rows = list(grid.itertuples()) + [None] + list(btm.itertuples())
ypos = list(range(len(rows)))

fig = plt.figure(figsize=(13.33, 7.5), dpi=150, facecolor=SURF)
ax = fig.add_axes([0.27, 0.235, 0.68, 0.485], facecolor=SURF)
H = 0.62
for y, r in zip(ypos, rows):
    if r is None:
        continue
    left = 0
    for k in ['co2_combustion', 'co2_supply', 'ch4_upstream', 'ch4_slip']:
        v = getattr(r, k)
        if v < 3:   # turbine slip (~1 kg) would draw as a hairline; still counted in the total label
            continue
        ax.barh(y, v - 1.5, left=left, height=H, color=C[k], edgecolor='none')
        left += v
    t20 = c20.set_index('name').loc[r.name, ['co2_combustion', 'co2_supply', 'ch4_upstream', 'ch4_slip']].sum()
    ax.plot([t20], [y], marker='D', ms=7, mfc=SURF, mec=INK2, mew=1.4, zorder=5)
    ax.text(r.total + 12, y, f'{r.total:,.0f}', va='center', ha='left', fontsize=12, color=INK, fontweight='bold')
    if r.name in SHARE or r.name == 'Combined cycle (on site)':
        sub = f'~{SHARE[r.name] * 100:.0f}% of planned capacity' if r.name in SHARE else 'almost none planned'
        ax.text(-12, y + 0.16, LABEL[r.name], va='center', ha='right', fontsize=12.5, color=INK)
        ax.text(-12, y - 0.30, sub, va='center', ha='right', fontsize=10, color=MUTED)
    else:
        ax.text(-12, y, LABEL[r.name], va='center', ha='right', fontsize=12.5, color=INK)

# grid-average reference band (range of the three averages)
avg = grid[grid.name.str.contains('average')].total
ax.axvspan(avg.min(), avg.max(), color=MUTED, alpha=0.13, lw=0, zorder=0)
ax.text((avg.min() + avg.max()) / 2, ypos[-1] + 0.62, 'grid averages', ha='center', va='bottom', fontsize=10.5, color=INK2)

gap_y = rows.index(None)
ax.text(-12, ypos[-1] + 0.62, 'OFF-GRID GAS AT THE DATA CENTER', ha='right', va='bottom', fontsize=10.5, color=INK2, fontweight='bold')
ax.text(-12, gap_y - 0.45 + 0.1, 'GRID', ha='right', va='bottom', fontsize=10.5, color=INK2, fontweight='bold')
ax.axhline(gap_y, color=GRIDC, lw=1)

xmax = max(c20[c20.name.isin(list(btm.name) + grid_names)][['co2_combustion', 'co2_supply', 'ch4_upstream', 'ch4_slip']].sum(axis=1)) * 1.06
ax.set_xlim(0, xmax)
ax.set_ylim(-0.6, ypos[-1] + 1.2)
ax.set_yticks([])
ax.set_xlabel('kg CO$_2$-equivalent per MWh delivered (100-year GWP)', fontsize=12.5, color=INK, labelpad=8)
ax.tick_params(axis='x', labelsize=11.5, colors=INK2)
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f'{v:,.0f}'))
ax.xaxis.grid(True, color=GRIDC, lw=0.8)
ax.set_axisbelow(True)
for s in ['top', 'right', 'left']:
    ax.spines[s].set_visible(False)
ax.spines['bottom'].set_color(MUTED)

# legend row above the axes
handles = [plt.Rectangle((0, 0), 1, 1, color=C[k]) for k in C] + \
          [plt.Line2D([], [], marker='D', ls='', ms=7, mfc=SURF, mec=INK2, mew=1.4)]
fig.legend(handles, [LEG[k] for k in C] + ['Total with a 20-year GWP'], loc='lower left', bbox_to_anchor=(0.04, 0.735), ncol=3,
           frameon=False, fontsize=11, handlelength=1.2, columnspacing=1.6, labelcolor=INK)

# computed headline numbers
d = dec[(dec.reference == 'A')]
eng = d[d.case.isin(['Recip engines (lean-burn)', 'Simple-cycle turbines'])]
lo, hi = [int(v * 100 + 0.5) for v in (eng.rel_gap_full.min(), eng.rel_gap_full.max())]   # round half up
eff = d[d.case.isin(['Fuel cells (Bloom SOFC)', 'Combined cycle (on site)'])]
elo, ehi = [int(v * 100 + 0.5) for v in (eff.rel_gap_full.min(), eff.rel_gap_full.max())]
fig.text(0.04, 0.955, f'Off-grid gas engines and turbines emit {lo:.0f}–{hi:.0f}% more per MWh than the grid',
         fontsize=19, fontweight='bold', color=INK, va='top')
fig.text(0.04, 0.898, f'Life-cycle emissions of power for a data center. For engines and turbines, methane widens a gap that CO$_2$ alone already sets.\n'
         f'Fuel cells and on-site combined cycle: {elo}–{ehi}% above grid averages (within uncertainty for fuel cells), level with a new grid gas plant.',
         fontsize=12.5, color=INK2, va='top', linespacing=1.4)
fig.text(0.04, 0.035,
         'Same gas supply on both sides: 2.3% of methane production leaked (Alvarez et al. 2018). Grid: EPA eGRID2023 balancing-authority averages,\n'
         'plus upstream gas and coal-mine methane and 3% transmission loss. Engine slip: EPA 40 CFR 98 Table W-7. Heat rates: Cat G3520H, GE LM6000/LM2500,\n'
         'Bloom datasheet midpoint, NETL H-class. Upstream CO$_2$: NETL 2025. GWPs: IPCC AR6. Planned capacity: share of the ~27 GW of off-grid data-center\n'
         'power with identified equipment (Cleanview, mid-2026), by manufacturer, split into technologies by us.   Analysis: Zeke Hausfather / The Climate Brink',
         fontsize=9.5, color=MUTED, va='bottom', linespacing=1.45)
out = ROOT / 'figures'
out.mkdir(exist_ok=True)
fig.savefig(out / 'offgrid_gas_vs_grid.png', dpi=150, facecolor=SURF)
print('saved', lo, hi, elo, ehi)
