"""V1: reproduce NETL Rev1 (DOE/NETL-2025/4933) NGCC-F life-cycle GHG, 394.7 kg CO2e/MWh generated."""
import emissions as em

NETL_GENERATED = 394.7
NETL_UPSTREAM_CH4 = 21.0       # g/kWh CH4 term in the NETL total
L_KG_PER_KG_NG = 0.0055        # NETL leak definition: kg CH4 per kg NG delivered
L = L_KG_PER_KG_NG / em.CH4_MASS_FRAC   # -> share of CH4 (approx; ignores the loss in the denominator)

hr = em.hr_from_eff(0.536)
parts = em.intensity(hr, slip=0.004, L=L, parts=True)
tot = sum(parts.values())
for k, v in parts.items():
    print(f'{k:16s} {v:7.1f}')
print(f'total {tot:.1f} vs NETL {NETL_GENERATED} ({(tot / NETL_GENERATED - 1) * 100:+.1f}%)')
NETL_COMBUSTION = 50.3 * 3.6 / 0.536   # 50.3 g/MJ HHV x 6.713 MJ/kWh = 337.6
print(f'combustion {parts["co2_combustion"]:.1f} vs NETL {NETL_COMBUSTION:.1f}')
print(f'upstream CH4 term {parts["ch4_upstream"]:.1f} vs NETL {NETL_UPSTREAM_CH4}')
assert abs(parts['co2_combustion'] / NETL_COMBUSTION - 1) < 0.01
assert abs(parts['ch4_upstream'] / NETL_UPSTREAM_CH4 - 1) < 0.10
assert abs(tot / NETL_GENERATED - 1) < 0.02
