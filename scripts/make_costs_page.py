"""Build the shareable cost page (docs/costs/index.html, served by GitHub Pages) from results/costs/*.csv and costs.py.

Every number on the page is read from the results files or the costs.py inputs. Run after costs.py.
"""
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'scripts'))
import costs as C  # noqa: E402

R = REPO / 'results/costs'
OUT = REPO / 'docs/costs/index.html'

main = pd.read_csv(R / 'lcoe_main.csv')
sens = pd.read_csv(R / 'lcoe_sensitivities.csv')
grid = pd.read_csv(R / 'grid_references.csv')
bridge = pd.read_csv(R / 'bridge_lease.csv')
laz = pd.read_csv(R / 'lazard_reproduction.csv')

SHORT = {'Recip engines (lean-burn)': 'Engines', 'Simple-cycle turbines': 'Turbines',
         'Fuel cells (Bloom SOFC)': 'Fuel cells', 'Combined cycle (on site)': 'On-site CC'}
LONG = {'Recip engines (lean-burn)': 'Reciprocating engines', 'Simple-cycle turbines': 'Simple-cycle turbines',
        'Fuel cells (Bloom SOFC)': 'Solid oxide fuel cells', 'Combined cycle (on site)': 'On-site combined cycle'}
r0 = lambda x: int(round(float(x)))


def row(tech, site=300, basis='system (N+k)'):
    return main[(main.tech == tech) & (main.site_mw == site) & (main.basis == basis)].iloc[0]


techs = list(C.TECH)
bars = []
for t in techs:
    s, b = row(t), row(t, basis='bare')
    use = b if t.startswith('Combined') else s
    bars.append(dict(key=t, name=SHORT[t], long=LONG[t], cc=t.startswith('Combined'),
                     parts=[round(use[k], 1) for k in ('capital', 'fixed_om', 'var_om', 'fuel')],
                     total=round(use.lcoe, 1), lo=round(use.lcoe_capex_low, 1), hi=round(use.lcoe_capex_high, 1),
                     bare=round(b.lcoe, 1), system=round(s.lcoe, 1), n=int(s.n_units), m=int(s.m_units),
                     over=round(s.overbuild, 2)))

g = grid.set_index('reference')
pjm_lo = g.loc['PJM wholesale + transmission, 2025 (IMM total price)', 'levelized_gas_indexed']
pjm_hi = g.loc['PJM same, capacity at 2026/27 BRA, 80% LF', 'levelized_gas_indexed']
ercot_w = g.loc['ERCOT wholesale all-in, 2025 (IMM: 2024 $34 x 1.138)', 'levelized_gas_indexed']
tx_ret = g.loc['EIA industrial retail, Jan-Aug 2026: Texas', 'levelized_inflation_only']
refs = dict(pjm_lo=round(pjm_lo, 1), pjm_hi=round(pjm_hi, 1), ercot=round(ercot_w, 1), tx=round(tx_ret, 1))

# tornado: engines and turbines, selected tests
PICK = ['bare plant (no spares)', 'capex low', 'capex high', 'gas: Waha (Permian) basis', 'gas: AEO2026 path',
        'gas: strip, then inflation only', 'WACC 6% / 10% (after tax)', '100% bonus depreciation (OBBBA)',
        'carrying cost as Brattle CT (installed/overnight 1.28)', 'property tax + insurance 1.5%/yr of capex',
        'BESS 0.25 MW per MW peak', 'load factor 0.70', 'load factor 0.90', 'reliability 99.9%',
        'bridge: 10-yr write-off', 'bridge: 5-yr write-off']
LABEL = {'bare plant (no spares)': 'No spare units', 'capex low': 'Capex low (pre-boom / AEO2026)',
         'capex high': 'Capex high (AEO2026 × 1.51)', 'gas: Waha (Permian) basis': 'Gas at Waha (Permian)',
         'gas: AEO2026 path': 'Gas on AEO2026 path', 'gas: strip, then inflation only': 'Gas strip, then inflation only',
         'WACC 6% / 10% (after tax)': 'WACC 6% / 10%', '100% bonus depreciation (OBBBA)': '100% bonus depreciation',
         'carrying cost as Brattle CT (installed/overnight 1.28)': 'Brattle carrying cost (×1.28)',
         'property tax + insurance 1.5%/yr of capex': 'Property tax + insurance',
         'BESS 0.25 MW per MW peak': 'Batteries, 0.25 MW per MW', 'load factor 0.70': 'Load factor 0.70',
         'load factor 0.90': 'Load factor 0.90', 'reliability 99.9%': 'Reliability target 99.9%',
         'bridge: 10-yr write-off': 'Written off after 10 yr', 'bridge: 5-yr write-off': 'Written off after 5 yr'}
tornado = {}
for t in techs[:2]:
    base = float(sens[(sens.tech == t) & (sens.test == 'central')].lcoe.iloc[0])
    items = []
    for name in PICK:
        rr = sens[(sens.tech == t) & (sens.test == name)].iloc[0]
        if '/' in str(rr.delta):
            a, b = [float(x) for x in str(rr.delta).split('/')]
            items.append(dict(label='WACC 6%', d=a))
            items.append(dict(label='WACC 10%', d=b))
        else:
            items.append(dict(label=LABEL[name], d=float(rr.delta)))
    tornado[SHORT[t]] = dict(base=base, items=items)

sizes = []
for t in techs[:3]:
    sizes.append(dict(name=LONG[t], unit=C.TECH[t]['unit_mw'],
                      cells=[dict(site=s, lcoe=r0(row(t, s).lcoe), n=int(row(t, s).n_units), m=int(row(t, s).m_units))
                             for s in (100, 300, 1000)]))

br = bridge.set_index('basis')
gas_lev = {c: round(C.level(list(C.gas_path(c).values())[:C.LIFE], C.FIN_CENTRAL['wacc']), 2)
           for c in ('central', 'strip_flat', 'aeo2026', 'waha')}
gp = C.gas_path('central')
lz = laz[(laz.macrs == 15) & (laz.om_esc == 0)]

E, T, F, CC = bars
data = dict(bars=bars, refs=refs, tornado=tornado)

# ---------------------------------------------------------------- copy, with numbers bound to the data
fmt = lambda x: f'{x:,.0f}'
tech_rows = ''
SRC = {
    'Recip engines (lean-burn)': 'Central: Brattle, “approach or exceed $3,000/kW.” Low: EIA AEO2023 engine, $2,240 (2022$), pre-boom. High: AEO2026 aeroderivative × 1.51 escalation.',
    'Simple-cycle turbines': 'Central: Brattle. Low: EIA AEO2026 aeroderivative, $2,275 (2025$). High: AEO2026 × 1.51, the frame-CT rise since the 2025 PJM study.',
    'Fuel cells (Bloom SOFC)': 'Central: AEP’s $4B, 702 MW Bloom plant for Google. High: EIA AEO2026 fuel cell. Low: ~$3,000 (unverified). Stack replacement of 15% of capex every 5 years is our assumption.',
    'Combined cycle (on site)': 'Lazard 2026 range tops at $2,100; its CCGT market quotes are $2,400–2,600.',
}
for t in techs:
    p = C.TECH[t]
    r10 = lambda v: fmt(round(v, -1))
    tech_rows += (f'<tr class="main"><th scope="row">{LONG[t]}</th><td class="num">{r10(p["capex"][0])}</td>'
                  f'<td class="num">{r10(p["capex"][1])}–{r10(p["capex"][2])}</td><td class="num">{p["fom"]:.1f}</td>'
                  f'<td class="num">{p["vom"]:.1f}</td><td class="num">{C.CASES[t][0]:.2f}</td>'
                  f'<td class="num">{p["unit_mw"]:g}</td></tr><tr class="srcrow"><td colspan="7">{SRC[t]}</td></tr>')

grid_rows = ''
GLABEL = [('PJM wholesale + transmission, 2025 (IMM total price)', 'PJM wholesale + transmission (2025 IMM total)'),
          ('PJM same, capacity at 2026/27 BRA, 80% LF', 'Same, capacity at 2026/27 auction price'),
          ('ERCOT wholesale all-in, 2025 (IMM: 2024 $34 x 1.138)', 'ERCOT wholesale all-in (excludes transmission)'),
          ('EIA industrial retail, Jan-Aug 2026: Texas', 'Industrial retail, Texas'),
          ('EIA industrial retail, Jan-Aug 2026: US', 'Industrial retail, US'),
          ('EIA industrial retail, Jan-Aug 2026: Virginia', 'Industrial retail, Virginia'),
          ('EIA industrial retail, Jan-Aug 2026: Ohio', 'Industrial retail, Ohio'),
          ('EIA industrial retail, Jan-Aug 2026: Pennsylvania', 'Industrial retail, Pennsylvania')]
for k, lab in GLABEL:
    x = g.loc[k]
    gi = '—' if pd.isna(x.levelized_gas_indexed) else fmt(x.levelized_gas_indexed)
    grid_rows += (f'<tr><th scope="row">{lab}</th><td class="num">{x.observed:.1f}</td>'
                  f'<td class="num">{fmt(x.levelized_inflation_only)}</td><td class="num">{gi}</td></tr>')

size_rows = ''
for s in sizes:
    cells = ''.join(f'<td class="num">{c["lcoe"]}<span class="sub">{c["m"]} units for {c["n"]}</span></td>' for c in s['cells'])
    size_rows += f'<tr><th scope="row">{s["name"]}<span class="sub">{s["unit"]:g} MW units</span></th>{cells}</tr>'

comp_rows = ''
for b in bars:
    comp_rows += (f'<tr><th scope="row">{b["long"]}{" (bare plant)" if b["cc"] else ""}</th>'
                  + ''.join(f'<td class="num">{v:.0f}</td>' for v in b['parts'])
                  + f'<td class="num strong">{b["total"]:.0f}</td><td class="num">{b["lo"]:.0f}–{b["hi"]:.0f}</td>'
                  + f'<td class="num">{b["bare"]:.0f}</td></tr>')

laz_rows = ''.join(f'<tr><th scope="row">{r.row}</th><td class="num">{r.published:.0f}</td><td class="num">{r.ours:.1f}</td>'
                   f'<td class="num">{r.err_pct:+.1f}%</td></tr>' for r in lz.itertuples())

pct = lambda a, b: round(100 * (a / b - 1))
html = (REPO / 'scripts/costs_page_template.html').read_text()
subs = {
    '__DATA__': json.dumps(data),
    '__E__': fmt(E['system']), '__T__': fmt(T['system']), '__F__': fmt(F['system']),
    '__F_ITC__': fmt(float(sens[(sens.tech == F['key']) & (sens.test.str.contains('ITC'))].lcoe.iloc[0])),
    '__E_LO__': fmt(E['lo']), '__E_HI__': fmt(E['hi']), '__T_LO__': fmt(T['lo']), '__T_HI__': fmt(T['hi']),
    '__PJM_LO__': fmt(refs['pjm_lo']), '__PJM_HI__': fmt(refs['pjm_hi']), '__TX__': fmt(refs['tx']), '__ERCOT__': fmt(refs['ercot']),
    '__E_PJM__': f'{pct(E["system"], refs["pjm_hi"])}–{pct(E["system"], refs["pjm_lo"])}%',
    '__T_PJM__': f'{pct(T["system"], refs["pjm_hi"])}–{pct(T["system"], refs["pjm_lo"])}%',
    '__TX_X__': f'{E["system"] / refs["tx"]:.1f}–{T["system"] / refs["tx"]:.1f}×',
    '__CC_BARE__': fmt(CC['bare']), '__CC_SYS__': fmt(CC['system']),
    '__E_N__': str(E['n']), '__E_M__': str(E['m']), '__T_N__': str(T['n']), '__T_M__': str(T['m']),
    '__E_OVER__': f'{100 * (E["over"] - 1):.0f}%', '__T_OVER__': f'{100 * (T["over"] - 1):.0f}%',
    '__LEASE_KW__': f'{br.loc["leased MW = peak", "lease_kw_month"]:.0f}',
    '__LEASE_1__': fmt(br.loc['leased MW = peak', 'total']), '__LEASE_2__': fmt(br.loc['leased MW = peak x N+k', 'total']),
    '__GAS_C__': f'{gas_lev["central"]:.2f}', '__GAS_S__': f'{gas_lev["strip_flat"]:.2f}',
    '__GAS_A__': f'{gas_lev["aeo2026"]:.2f}', '__GAS_W__': f'{gas_lev["waha"]:.2f}',
    '__GAS_2027__': f'{gp[2027]:.2f}', '__GAS_2040__': f'{gp[2040]:.2f}',
    '__WACC__': f'{100 * C.FIN_CENTRAL["wacc"]:.1f}', '__TECH_ROWS__': tech_rows, '__GRID_ROWS__': grid_rows,
    '__SIZE_ROWS__': size_rows, '__COMP_ROWS__': comp_rows, '__LAZ_ROWS__': laz_rows,
    '__LAZ_MIN__': f'{lz.err_pct.min():+.1f}', '__LAZ_MAX__': f'{lz.err_pct.max():+.1f}',
}
for k, v in subs.items():
    html = html.replace(k, v)
assert '__' not in html.replace('__proto__', ''), [l for l in html.splitlines() if '__' in l][:3]
HEAD = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<meta name="description" content="Levelized cost of islanded gas power for US data centers at current equipment prices, '
        'compared with PJM and Texas grid supply.">\n<style>body{margin:0}</style>\n')
# template opens with <title>/<link>/<style>; everything from the first <div> on is body content
html = html.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', '')
i = html.index('<div class="wrap">')
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(HEAD + html[:i] + '</head>\n<body>\n' + html[i:] + '\n</body>\n</html>\n')
print('wrote', OUT, len(html))
