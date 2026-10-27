"""M1: short-run marginal emission rates from hourly CEMS and EIA-930 demand (PLAN_marginal §M1, v2).

Primary (Holland et al. 2022): Y_t = b*D_t + month-of-sample FE + hour-of-day FE, Newey-West (48 lags).
Y = CO2e on this project's basis, built per fuel from CEMS heat input (supply CO2, upstream CH4 at L, coal-mine CH4,
combustion CH4/N2O). ERCOT: own CEMS on ERCO demand. PJM: Eastern-Interconnection CEMS on PJM demand and rest-of-EI demand.
US: per-interconnection estimates, load-weighted. Delivered = b / (1 - 0.06) (marginal losses).
Envelope (R1 x R2 x R3 x R4), bootstrap, diagnostics D1a-e. Writes results/marginal/srmer_specs.csv, srmer_primary.csv,
diagnostics.json.
"""
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

import emissions as em
from cases import CMM, F_SUPPLY, L_PRIMARY

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'marginal'
OUT = ROOT / 'results' / 'marginal'
OUT.mkdir(parents=True, exist_ok=True)
GWP = em.GWP['AR6_100']
LOSS_SR = 0.06
SEED, NBOOT, BLOCK = 20261026, 2000, 168
WEST_REGIONS, TEX_REGIONS = {'CAL', 'NW', 'SW'}, {'TEX'}
LST = {'ERCOT': 6, 'PJM': 5, 'TX': 6, 'EI': 5, 'WI': 8}     # hours behind UTC for hour-of-day FE
UNMAPPED = {'UNMAPPED_TX': 'ERCO', 'UNMAPPED_LA': 'MISO', 'UNMAPPED_MD': 'PJM', 'UNMAPPED_OH': 'PJM'}   # EIA-860M lookup
WEST_STATES = set('AZ CA CO ID MT NV NM OR UT WA WY'.split())
# per-MMBtu add-ons to CEMS CO2 (kg CO2e/MMBtu): supply CO2, upstream CH4, combustion CH4/N2O (Table C-2; W-7 turbines)
UP_GAS = em.EF_CO2 * F_SUPPLY + em.upstream_ch4(L_PRIMARY) * GWP['ch4']
ADD = {('gas', 'cc'): UP_GAS + 0.004 * GWP['ch4'] + 1e-4 * GWP['n2o'],
       ('gas', 'ct'): UP_GAS + 0.004 * GWP['ch4'] + 1e-4 * GWP['n2o'],
       ('gas', 'boiler_other'): UP_GAS + 0.001 * GWP['ch4'] + 1e-4 * GWP['n2o'],
       ('gas', 'ic'): UP_GAS + 0.522 * GWP['ch4'] + 1e-4 * GWP['n2o'],
       ('coal', None): CMM * GWP['ch4'] + 0.011 * GWP['ch4'] + 0.0016 * GWP['n2o'],
       ('oil', None): 0.003 * GWP['ch4'] + 0.0006 * GWP['n2o'],
       ('other', None): 0.0}
VALID = dict(holland_2019=dict(TX=1.085 * 453.59237, EI=1.407 * 453.59237),      # kg CO2/MWh (lb/kWh x 453.6)
             avert_2023_gen=dict(ERCOT=560.0, PJM=574.0, US=600.0))            # domain review §1.3 (AVERT v4.3, loss-adjusted)


# ---------------------------------------------------------------- data
def ba_regions():
    e = pd.read_parquet(DATA / 'eia930_hourly.parquet', columns=['ba', 'region']).dropna().drop_duplicates('ba')
    return dict(zip(e.ba, e.region))


def interconnect(ba, reg):
    if ba in UNMAPPED:
        ba = UNMAPPED[ba]
    r = reg.get(ba)
    if r is not None:
        return 'TX' if r in TEX_REGIONS else 'WI' if r in WEST_REGIONS else 'EI'
    if ba.startswith('UNMAPPED_'):
        st = ba[-2:]
        return None if st in ('AK', 'HI', 'PR') else 'WI' if st in WEST_STATES else 'EI'
    return None


def cems(year, reg):
    c = pd.read_parquet(DATA / 'campd' / f'campd_{year}.parquet')
    c['ba'] = c['ba'].replace(UNMAPPED)
    c['ic'] = [interconnect(b, reg) for b in c['ba']]
    c['add'] = [ADD.get((f, u), ADD.get((f, None), 0.0)) for f, u in zip(c.fuelc, c.uclass)]
    c['co2e'] = c.co2 + c.hi * c['add']
    for f in ('gas', 'coal', 'oil', 'other'):
        c[f'{f}_hi'] = np.where(c.fuelc == f, c.hi, 0.0)
        c[f'{f}_co2'] = np.where(c.fuelc == f, c.co2, 0.0)
    c['gas_gload'] = np.where(c.fuelc == 'gas', c.gload, 0.0)
    return c


def demand(year):
    d = pd.read_parquet(DATA / 'eia930_hourly.parquet')
    return d[(d.utc > f'{year}-01-01') & (d.utc <= f'{year + 1}-01-01')]


YCOLS = ['co2e', 'co2', 'gas_hi', 'coal_hi', 'oil_hi', 'other_hi', 'gas_co2', 'coal_co2', 'oil_co2', 'other_co2', 'gload', 'gas_gload']


def panel(year):
    """Hourly frame with CEMS sums and demand for each system used in the specs."""
    reg = ba_regions()
    c, d = cems(year, reg), demand(year)
    d = d.assign(ic=[interconnect(b, reg) for b in d.ba])
    systems = {'ERCOT': (c.ba == 'ERCO', d.ba == 'ERCO'), 'PJM': (c.ba == 'PJM', d.ba == 'PJM'),
               'TX': (c.ic == 'TX', d.ic == 'TX'), 'EI': (c.ic == 'EI', d.ic == 'EI'), 'WI': (c.ic == 'WI', d.ic == 'WI'),
               'L48': (c.ic.notna(), d.ic.notna())}
    idx = pd.date_range(f'{year}-01-01 01:00', f'{year + 1}-01-01 00:00', freq='h')
    P = pd.DataFrame(index=idx)
    flags = {}
    for s, (cm, dm) in systems.items():
        cs = c[cm].groupby('utc')[YCOLS].sum().reindex(idx)
        P[[f'{s}_{k}' for k in YCOLS]] = cs.values
        dd = d[dm]
        piv = dd.pivot_table(index='utc', columns='ba', values='demand', aggfunc='sum').reindex(idx)
        imp = dd.pivot_table(index='utc', columns='ba', values='demand_imputed', aggfunc='max').reindex(idx).astype('boolean').fillna(True)
        share = piv.mean() / piv.mean().sum()
        # an hour is bad if BAs carrying >1% of the system's load are missing or imputed; small-BA gaps are interpolated
        bad = ((piv.isna() | imp.astype(bool)) * share).sum(axis=1) > 0.01
        P[f'{s}_D'] = piv.interpolate(limit=3, limit_direction='both').sum(axis=1, min_count=1)
        P[f'{s}_fossil930'] = dd.assign(x=dd[['gen_gas', 'gen_coal', 'gen_oil']].sum(axis=1, min_count=1)).pivot_table(
            index='utc', columns='ba', values='x', aggfunc='sum').reindex(idx).sum(axis=1, min_count=1).values
        for f in ('wind', 'solar'):
            P[f'{s}_{f}'] = dd.pivot_table(index='utc', columns='ba', values=f'gen_{f}', aggfunc='sum').reindex(idx).sum(axis=1).values
        flags[s] = bad
    # align PJM's EIA-930 fuel-mix columns (wind/solar controls) to CEMS time; demand itself is aligned (D1a timestamp check)
    lag = fuel_column_lag(P, 'PJM')
    for f in ('wind', 'solar', 'fossil930'):
        P[f'PJM_{f}'] = P[f'PJM_{f}'].shift(lag)
    flags['_pjm_fuel_lag'] = lag
    P['EIrest_D'] = P['EI_D'] - P['PJM_D']
    P['EIrest_wind'] = P['EI_wind'] - P['PJM_wind']
    P['EIrest_solar'] = P['EI_solar'] - P['PJM_solar']
    return P, flags


def robust_flag(x):
    r = x - x.rolling(25, center=True, min_periods=12).median()
    mad = (r - r.median()).abs().median()
    return (r.abs() > 5 * 1.4826 * mad) | x.isna()


# ---------------------------------------------------------------- estimators
def nw_se(X, e, lags=48):
    n = len(e)
    XtX_inv = np.linalg.pinv(X.T @ X)
    u = X * e[:, None]
    S = u.T @ u
    for l in range(1, lags + 1):
        w = 1 - l / (lags + 1)
        G = u[l:].T @ u[:-l]
        S += w * (G + G.T)
    V = XtX_inv @ S @ XtX_inv
    return np.sqrt(np.diag(V))


def fe_matrix(index, lst, daily=False):
    loc = index - pd.Timedelta(hours=lst)
    parts = [pd.get_dummies(loc.to_period('M').astype(str), drop_first=False, dtype=float)]
    parts.append(pd.get_dummies(loc.dayofweek if daily else loc.hour, prefix='h', drop_first=True, dtype=float))
    return pd.concat(parts, axis=1).values


def fit(y, Xr, F, se=False):
    X = np.hstack([Xr, F])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    if not se:
        return b[:Xr.shape[1]]
    e = y - X @ b
    return b[:Xr.shape[1]], nw_se(X, e)[:Xr.shape[1]]


def season(ix):
    return ((ix.month % 12) // 3)


def binned(dy, dX, ix, lst):
    """Season x hour bins with intercepts; equal-weight mean of the first regressor's bin slopes."""
    loc = ix - pd.Timedelta(hours=lst)
    key = season(loc) * 24 + loc.hour
    bs = []
    for k in np.unique(key):
        m = key == k
        X = np.hstack([dX[m], np.ones((m.sum(), 1))])
        b, *_ = np.linalg.lstsq(X, dy[m], rcond=None)
        bs.append(b[0])
    return float(np.mean(bs))


def estimate(P, keep, y, xcols, lst, est):
    """Return the coefficient on xcols[0] for one estimator."""
    if y == xcols[0]:
        return 1.0   # fossil-load regressor: gross load on itself
    d = P.loc[keep, [y] + xcols].dropna()
    if est == 'levels':
        return float(fit(d[y].values, d[xcols].values, fe_matrix(d.index, lst))[0])
    if est in ('fd', 'd24'):
        lag = 1 if est == 'fd' else 24
        full = P[[y] + xcols].copy()
        full.loc[~keep] = np.nan
        dd = (full - full.shift(lag)).dropna()
        dd = dd[dd.index.isin(full.index[keep]) & dd.index.isin((full.index[keep] + pd.Timedelta(hours=lag)))]
        return binned(dd[y].values, dd[xcols].values, dd.index, lst)
    if est == 'daily':
        full = P[[y] + xcols].copy()
        full.loc[~keep] = np.nan
        loc = full.index - pd.Timedelta(hours=lst)
        g = full.groupby(loc.date)
        day = g.sum(min_count=1)[g.count().min(axis=1) == 24]
        day.index = pd.to_datetime(day.index)
        return float(fit(day[y].values, day[xcols].values, fe_matrix(day.index, 0, daily=True))[0])
    raise ValueError(est)


# ---------------------------------------------------------------- systems and specs
def spec_setup(region, boundary, regressor, renew):
    """(ycol prefix, regressor columns, keep-flag systems, lst) for a region under one R3/R4/R2 choice."""
    if region == 'ERCOT':
        ys, xs, fl = 'ERCOT', ['ERCOT_D'], ['ERCOT']
    elif region == 'PJM':
        if boundary == 'primary':
            ys, xs, fl = 'EI', ['PJM_D', 'EIrest_D'], ['PJM', 'EI']
        else:
            ys, xs, fl = 'PJM', ['PJM_D'], ['PJM']
    else:
        raise ValueError(region)
    if regressor == 'fossil':
        ys, xs, fl = (('PJM', ['PJM_gload'], ['PJM']) if region == 'PJM' else (ys, [f'{ys}_gload'], fl))
    if renew:
        base = xs[0].split('_')[0]
        xs = xs + [f'{base}_wind', f'{base}_solar'] + (['EIrest_wind', 'EIrest_solar'] if 'EIrest_D' in xs else [])
    return ys, xs, fl, LST[region]


def keep_mask(P, flags, systems, ycols):
    """Hours kept: demand not missing/imputed for the systems, and no 5xMAD spike in demand or the screened series.
    region_estimate screens on the system's CO2e for every dependent variable, so fuel equations share one sample."""
    k = pd.Series(True, index=P.index)
    for s in systems:
        k &= ~flags[s]
        k &= ~robust_flag(P[f'{s}_D'])
    for c in ycols:
        k &= ~robust_flag(P[c])
    return k


def region_estimate(P, flags, region, est='levels', boundary='primary', regressor='demand', renew=False, y='co2e'):
    if region == 'US':
        if boundary == 'primary':   # load-weighted mean of the three interconnections
            out, w = 0.0, 0.0
            for s in ('TX', 'EI', 'WI'):
                xs = [f'{s}_gload'] if regressor == 'fossil' else [f'{s}_D']
                if renew:
                    xs += [f'{s}_wind', f'{s}_solar']
                k = keep_mask(P, flags, [s], [f'{s}_co2e'])
                b = estimate(P, k, f'{s}_{y}', xs, LST[s], est)
                load = P[f'{s}_D'].sum()
                out += b * load
                w += load
            return out / w
        xs = ['L48_gload'] if regressor == 'fossil' else ['L48_D']
        if renew:
            xs += ['L48_wind', 'L48_solar']
        k = keep_mask(P, flags, ['L48'], ['L48_co2e'])
        return estimate(P, k, f'L48_{y}', xs, LST['EI'], est)
    ys, xs, fl, lst = spec_setup(region, boundary, regressor, renew)
    k = keep_mask(P, flags, fl, [f'{ys}_co2e'])
    return estimate(P, k, f'{ys}_{y}', xs, lst, est)


def bootstrap(P, flags, region, renew=True, boundary='primary', y='co2e'):
    """Weekly moving-block bootstrap of a levels + FE spec (demand regressor); US = load-weighted interconnections."""
    rng = np.random.default_rng(SEED)
    if region == 'US':
        setups = [(f'{s}_{y}', [f'{s}_D'] + ([f'{s}_wind', f'{s}_solar'] if renew else []), [s], LST[s], P[f'{s}_D'].sum())
                  for s in ('TX', 'EI', 'WI')]
    else:
        ys, xs, fl, lst = spec_setup(region, boundary, 'demand', renew)
        setups = [(f'{ys}_{y}', xs, fl, lst, 1.0)]
    parts = []
    for ycol, xs, fl, lst, load in setups:
        k = keep_mask(P, flags, fl, [ycol])
        d = P.loc[k, [ycol] + xs].dropna()
        parts.append((d.values[:, 0], d.values[:, 1:], fe_matrix(d.index, lst), load))
    n = min(len(p[0]) for p in parts)
    out = []
    for _ in range(NBOOT):
        starts = rng.integers(0, n - BLOCK, n // BLOCK + 1)
        ix = np.concatenate([np.arange(s0, s0 + BLOCK) for s0 in starts])[:n]
        out.append(sum(fit(yv[ix], Xv[ix], F[ix])[0] * L for yv, Xv, F, L in parts) / sum(p[3] for p in parts))
    return np.array(out)


# ---------------------------------------------------------------- diagnostics
def lag_test(P, flags, s, timestamp=False):
    """Month-by-month lag (hours, -2..2) maximizing corr(dA_t, dB_{t-lag}).
    Pre-registered D1a: A = CEMS CO2, B = demand (confounded by solar shifting the net-load ramp in summer).
    Timestamp check: A = CEMS gross load, B = demand, outside Jun-Aug."""
    a, b = (f'{s}_gload', f'{s}_D') if timestamp else (f'{s}_co2', f'{s}_D')
    k = ~flags[s] & ~robust_flag(P[b]) & ~robust_flag(P[a])
    dx = P[[a, b]].where(k).diff()
    if timestamp:
        dx = dx[~dx.index.month.isin([6, 7, 8])]
    peaks = {}
    for m, g in dx.groupby(dx.index.month):
        if g.dropna().shape[0] < 100:   # months without CEMS data (e.g. 2019 Q4)
            continue
        cc = {l: g[a].corr(g[b].shift(l)) for l in range(-2, 3)}
        peaks[int(m)] = max(cc, key=cc.get)
    return peaks


def fuel_column_lag(P, s):
    """Lag of a system's EIA-930 fuel-mix columns relative to CEMS (PJM's are offset by an hour in some years)."""
    dx = P[[f'{s}_gload', f'{s}_fossil930']].diff()
    cc = {l: dx.iloc[:, 0].corr(dx.iloc[:, 1].shift(l)) for l in range(-2, 3)}
    return max(cc, key=cc.get)


def nw_levels(P, flags, sys_y, xcol, lst, y='co2'):
    k = keep_mask(P, flags, [sys_y] if sys_y not in ('PJM_own',) else ['PJM'], [f'{sys_y}_{y}'])
    d = P.loc[k, [f'{sys_y}_{y}', xcol]].dropna()
    b, se = fit(d.values[:, 0], d.values[:, 1:], fe_matrix(d.index, lst), se=True)
    return float(b[0]), float(se[0])


def main():
    diag, specs, prim = {}, [], []
    panels = {}
    for year in (2019, 2023, 2024, 2025):
        cached = DATA / f'srmer_panel_{year}.parquet'   # small, committed: hourly system totals + flags
        if cached.exists():
            P = pd.read_parquet(cached)
            flags = {c[5:]: P.pop(c).astype(bool) for c in [c for c in P.columns if c.startswith('flag_')]}
            flags['_pjm_fuel_lag'] = int(P.pop('pjm_fuel_lag').iloc[0])
        elif (DATA / 'campd' / f'campd_{year}.parquet').exists():
            P, flags = panel(year)
            P.assign(**{f'flag_{k}': v for k, v in flags.items() if not k.startswith('_')},
                     pjm_fuel_lag=flags['_pjm_fuel_lag']).astype('float32', errors='ignore').to_parquet(cached)
        else:
            print('missing CEMS', year)
            continue
        panels[year] = (P, flags)
        diag[f'pjm_fuel_column_lag_{year}'] = int(flags.pop('_pjm_fuel_lag'))
        diag[f'dropped_hours_{year}'] = {s: int(flags[s].sum()) for s in flags}

    # D1a lag test (2019, 2025)
    for year in (2019, 2025):
        if year in panels:
            P, flags = panels[year]
            diag[f'D1a_lag_peaks_{year}'] = {s: lag_test(P, flags, s) for s in ('ERCOT', 'PJM')}
            diag[f'D1a_timestamp_check_{year}'] = {s: lag_test(P, flags, s, timestamp=True) for s in ('ERCOT', 'PJM')}
    # D1b Holland 2019 reproduction (combustion CO2, levels + FE, interconnection demand)
    if 2019 in panels:
        P, flags = panels[2019]
        d1b = {}
        for s in ('TX', 'EI'):
            b, se = nw_levels(P, flags, s, f'{s}_D', LST[s])
            target = VALID['holland_2019'][s]
            tol = max(0.05 * target, 2 * se)
            d1b[s] = dict(ours=b, se=se, holland=target, tol=tol, passed=bool(abs(b - target) <= tol))
            for est in ('fd', 'd24', 'daily'):
                d1b[s][est] = estimate(P, keep_mask(P, flags, [s], [f'{s}_co2']), f'{s}_co2', [f'{s}_D'], LST[s], est)
        diag['D1b_holland_2019'] = d1b
    # D1c AVERT 2023 (combustion CO2, generation level)
    if 2023 in panels:
        P, flags = panels[2023]
        d1c = {}
        for reg in ('ERCOT', 'PJM', 'US'):
            fossil = region_estimate(P, flags, reg, regressor='fossil', boundary='primary' if reg != 'PJM' else 'own', y='co2')
            dem = region_estimate(P, flags, reg, y='co2')
            t = VALID['avert_2023_gen'][reg]
            d1c[reg] = dict(fossil_load=fossil, demand=dem, avert=t, fossil_rel=fossil / t - 1, demand_rel=dem / t - 1,
                            passed=bool(abs(fossil / t - 1) <= 0.10) if reg != 'US' else None)
        diag['D1c_avert_2023'] = d1c

    # 2024, 2025: every spec with D1e diagnostics; primary per the change-log rule; envelope of passing specs; bootstrap
    for year in (2024, 2025):
        if year not in panels:
            continue
        P, flags = panels[year]
        # collinearity of the joint PJM regressors after removing the fixed effects
        F = fe_matrix(P.index, LST['PJM'])
        ok = P[['PJM_D', 'EIrest_D']].notna().all(axis=1).values
        res = {c: P[c].values[ok] - F[ok] @ np.linalg.lstsq(F[ok], P[c].values[ok], rcond=None)[0] for c in ('PJM_D', 'EIrest_D')}
        diag[f'pjm_joint_regressor_corr_after_fe_{year}'] = float(np.corrcoef(res['PJM_D'], res['EIrest_D'])[0, 1])
        for reg in ('ERCOT', 'PJM', 'US'):
            for est, renew, boundary, regressor in itertools.product(('levels', 'fd', 'd24', 'daily'), (False, True),
                                                                     ('primary', 'alt'), ('demand', 'fossil')):
                if reg == 'ERCOT' and boundary == 'alt':
                    continue   # ERCOT has a single boundary
                bnd = boundary if reg != 'PJM' else ('primary' if boundary == 'primary' else 'own')
                kw = dict(est=est, boundary=bnd, regressor=regressor, renew=renew)
                b_ = region_estimate(P, flags, reg, **kw)
                gl = region_estimate(P, flags, reg, y='gload', **kw)
                gh = region_estimate(P, flags, reg, y='gas_hi', **kw)
                gg = region_estimate(P, flags, reg, y='gas_gload', **kw)
                hr = gh / gg if gg else np.nan
                specs.append(dict(year=year, region=reg, estimator=est, renewables=renew, boundary=boundary, regressor=regressor,
                                  beta_gen=b_, srmer_delivered=b_ / (1 - LOSS_SR), fossil_share=gl, gas_hr=hr,
                                  d1e_pass=bool(0.6 <= gl <= 1.05 and 6.5 <= hr <= 11)))
            sr = pd.DataFrame([x for x in specs if x['year'] == year and x['region'] == reg])
            pick = lambda rn, bd: sr[(sr.estimator == 'levels') & (sr.regressor == 'demand') & (sr.renewables == rn) & (sr.boundary == bd)].iloc[0]
            prereg = pick(False, 'primary')
            chosen, bnd_used = pick(True, 'primary'), 'primary'
            if not chosen.d1e_pass and reg != 'ERCOT':
                chosen, bnd_used = pick(True, 'alt'), 'alt'
            bnd = bnd_used if reg != 'PJM' else ('primary' if bnd_used == 'primary' else 'own')
            fb = {y: region_estimate(P, flags, reg, boundary=bnd, renew=True, y=y) for y in YCOLS}
            sysn = {'ERCOT': 'ERCOT', 'PJM': 'EI' if bnd == 'primary' else 'PJM', 'US': 'L48'}[reg]
            ratios = {f: P[f'{sysn}_{f}_co2'].sum() / P[f'{sysn}_{f}_hi'].sum() for f in ('gas', 'coal', 'oil', 'other')
                      if P[f'{sysn}_{f}_hi'].sum() > 0}
            closure = (sum(ratios[f] * fb[f'{f}_hi'] for f in ratios) + (fb['other_co2'] if 'other' not in ratios else 0)) / fb['co2'] - 1
            boot = bootstrap(P, flags, reg, renew=True, boundary=bnd)
            passing = sr[sr.d1e_pass]
            prim.append(dict(year=year, region=reg, spec=f'levels+FE, demand, wind/solar controls, boundary={bnd}',
                             co2e_gen=fb['co2e'], co2_gen=fb['co2'], srmer_delivered=fb['co2e'] / (1 - LOSS_SR),
                             srmer_delivered_3pct=fb['co2e'] / 0.97, d1e_pass=bool(chosen.d1e_pass),
                             ci05=np.percentile(boot, 5) / (1 - LOSS_SR), ci95=np.percentile(boot, 95) / (1 - LOSS_SR),
                             env_min=passing.srmer_delivered.min(), env_max=passing.srmer_delivered.max(),
                             env_median=passing.srmer_delivered.median(), n_pass=len(passing), n_specs=len(sr),
                             prereg_primary=prereg.srmer_delivered, prereg_fossil_share=prereg.fossil_share,
                             gas_hi=fb['gas_hi'], coal_hi=fb['coal_hi'], oil_hi=fb['oil_hi'], fossil_share=fb['gload'],
                             marginal_gas_hr=fb['gas_hi'] / fb['gas_gload'] if fb['gas_gload'] else np.nan, closure=closure))
            print(year, reg, {k: round(v, 3) if isinstance(v, float) else v for k, v in prim[-1].items()}, flush=True)
    sp = pd.DataFrame(specs)
    sp.to_csv(OUT / 'srmer_specs.csv', index=False)
    pr = pd.DataFrame(prim)
    pr.to_csv(OUT / 'srmer_primary.csv', index=False)
    json.dump(diag, open(OUT / 'diagnostics.json', 'w'), indent=1, default=float)
    print(json.dumps(diag, indent=1, default=float)[:4000])
    with pd.option_context('display.width', 250, 'display.max_columns', 30):
        print(pr.round(3).to_string())


if __name__ == '__main__':
    main()
