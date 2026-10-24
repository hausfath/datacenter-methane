"""FaIR 2.2.2 + calibration v1.5.1 (updated-2023, Zenodo 17424050) paired perturbation runs.

Each run is a single SSP background with 841 constrained members. Perturbations add CO2 FFI (Gt CO2/yr) and
CH4 (Mt CH4/yr) to the background; the response is perturbed minus baseline, member by member.
FaIR 2.2.2 does not oxidize CH4 to CO2 (oxidation_matrix is commented out in fair.py), so oxidation CO2 is
added explicitly by `with_oxidation`.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from fair import FAIR
from fair.interface import fill, initialise
from fair.io import read_properties

CAL = Path(__file__).resolve().parents[1] / 'data' / 'fair_calib'
PARAMS = CAL / 'calibrated_constrained_parameters.csv'
SPECIES = CAL / 'species_configs_properties.csv'
START, END = 1750, 2150
CO2_PER_CH4 = 44.009 / 16.043
CH4_PERT_LIFETIME = 12.0   # yr, AR6 CH4 perturbation lifetime (approx) for oxidation lag


def with_oxidation(years, ch4_mt):
    """Gt CO2/yr from oxidation of fossil CH4 emitted as ch4_mt (Mt/yr), released with an e-folding lag."""
    out = np.zeros_like(ch4_mt, dtype=float)
    burden = 0.0
    k = 1 - np.exp(-1 / CH4_PERT_LIFETIME)
    for i in range(len(years)):
        burden += ch4_mt[i]
        ox = burden * k
        burden -= ox
        out[i] = ox * CO2_PER_CH4 / 1000.0
    return out


def run(ssp, co2_gt=None, ch4_mt=None, return_obj=False):
    """Return GSAT anomaly array (timebounds x configs) for one background with optional added emissions.

    co2_gt, ch4_mt: arrays on timepoints START+0.5 .. END-0.5 (length END-START), added to CO2 FFI and CH4.
    """
    df = pd.read_csv(PARAMS, index_col=0)
    f = FAIR(ch4_method='Thornhill2021')
    f.define_time(START, END, 1)
    f.define_scenarios([ssp])
    f.define_configs(df.index)
    species, properties = read_properties(filename=SPECIES)
    f.define_species(species, properties)
    f.allocate()
    f.fill_from_rcmip()

    sol = pd.read_csv(CAL / 'solar_erf_timebounds_cmip6.csv', index_col='year')['erf']
    vol = pd.read_csv(CAL / 'volcanic_erf_timebounds_cmip6.csv', index_col='year')['erf']
    tb = np.arange(START, END + 1)
    sol = sol.reindex(tb).ffill().values
    vol = vol.reindex(tb).fillna(0.0).values
    fill(f.forcing, sol[:, None, None] * df['forcing_scale[Solar]'].values[None, None, :], specie='Solar')
    fill(f.forcing, vol[:, None, None] * df['forcing_scale[Volcanic]'].values[None, None, :], specie='Volcanic')

    f.fill_species_configs(SPECIES)
    f.override_defaults(PARAMS)
    fill(f.climate_configs['stochastic_run'], False)   # deterministic: paired differences are exact

    if co2_gt is not None:
        e = f.emissions.loc[dict(specie='CO2 FFI', scenario=ssp)]
        fill(f.emissions, e + co2_gt[:, None], specie='CO2 FFI', scenario=ssp)
    if ch4_mt is not None:
        e = f.emissions.loc[dict(specie='CH4', scenario=ssp)]
        fill(f.emissions, e + ch4_mt[:, None], specie='CH4', scenario=ssp)

    initialise(f.concentration, f.species_configs['baseline_concentration'])
    initialise(f.forcing, 0)
    initialise(f.temperature, 0)
    initialise(f.cumulative_emissions, 0)
    initialise(f.airborne_emissions, 0)
    initialise(f.ocean_heat_content_change, 0)
    f.run(progress=False)
    if return_obj:
        return f
    T = f.temperature.loc[dict(scenario=ssp, layer=0)].values
    F = f.forcing_sum.loc[dict(scenario=ssp)].values
    return T, F


def timepoints():
    return np.arange(START, END) + 0.5
