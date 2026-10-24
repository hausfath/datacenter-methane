"""Per-MWh CO2e of gas-fired electricity, with engine slip and upstream methane.

All fuel quantities are HHV. Units: MMBtu, kg, MWh.
"""

# 40 CFR 98 Table C-1, natural gas
EF_CO2 = 53.06            # kg CO2 / MMBtu HHV
HHV_PER_LHV = 1.108       # pipeline gas, HHV/LHV ratio
BTU_PER_KWH = 3412.14

# Delivered gas: NETL Rev1 F-class feed 128 kg NG/MWh at 53.6% HHV -> 20.1 kg NG/MMBtu; CH4 mass fraction 0.93 (0.884-0.970)
KG_NG_PER_MMBTU = 128.0 / (BTU_PER_KWH / 1000 / 0.536)
CH4_MASS_FRAC = 0.93

GWP = {
    'AR6_100': dict(ch4=29.8, n2o=273.0),
    'AR6_20': dict(ch4=82.5, n2o=273.0),
    'AR5_100': dict(ch4=28.0, n2o=265.0),
    'AR5_20': dict(ch4=84.0, n2o=264.0),
}


def hr_from_eff(eff, basis='HHV'):
    """Heat rate (MMBtu HHV per MWh) from a net electrical efficiency."""
    eff_hhv = eff / HHV_PER_LHV if basis == 'LHV' else eff
    return BTU_PER_KWH / 1000 / eff_hhv


def ch4_content(mass_frac=CH4_MASS_FRAC):
    """kg CH4 per MMBtu of delivered gas."""
    return KG_NG_PER_MMBTU * mass_frac


def upstream_ch4(L, mass_frac=CH4_MASS_FRAC):
    """kg CH4 lost upstream per MMBtu delivered; L = loss as a share of CH4 produced (0-1)."""
    return ch4_content(mass_frac) * L / (1 - L)


def intensity(hr, slip, L, gwp='AR6_100', supply_co2_frac=0.093, fac=0.0, n2o=1e-4,
              mass_frac=CH4_MASS_FRAC, parts=False):
    """kg CO2e per MWh net.

    hr: MMBtu HHV/MWh. slip: kg CH4/MMBtu from the prime mover. L: upstream CH4 loss share of production.
    supply_co2_frac: supply-chain CO2 (processing, compression fuel, flaring) as a share of combustion CO2;
        0.093 = NETL Rev1 upstream 7.8 g/MJ less the 21.0 kg/MWh CH4 term, over 337.6 combustion (NGCC-F).
    fac: on-site/transmission leak as a share of delivered CH4. n2o: kg N2O/MMBtu (40 CFR 98 Table C-2).
    """
    g = GWP[gwp]
    c = ch4_content(mass_frac)
    out = dict(
        co2_combustion=hr * EF_CO2,
        co2_supply=hr * EF_CO2 * supply_co2_frac,
        ch4_slip=hr * slip * g['ch4'],
        ch4_upstream=hr * upstream_ch4(L, mass_frac) * g['ch4'],
        ch4_facility=hr * c * fac * g['ch4'],
        n2o=hr * n2o * g['n2o'],
    )
    return out if parts else sum(out.values())
