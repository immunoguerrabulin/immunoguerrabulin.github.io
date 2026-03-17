#!/usr/bin/env python3
"""Debug DX file reading and FMP calculation"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Import the read function from the main script
import sys
sys.path.insert(0, str(Path(__file__).parent))
from pme_pot_figure import read_dx_grid, kT_over_e, uniform_field_ramp

# Read the DX files
pos_data, (x, y, z), origin, deltas, _ = read_dx_grid(Path('pos.dx'))
neg_data, _, _, _, _ = read_dx_grid(Path('neg.dx'))

print(f"Grid shape: {pos_data.shape}")
print(f"Z range: {z.min()/10:.1f} to {z.max()/10:.1f} nm")
print(f"Origin: {origin}")
print(f"Deltas: {deltas}")

# Convert to Volts
kTe = kT_over_e(303.15)
pos_V = pos_data * kTe
neg_V = neg_data * kTe

# XY-average
pos_z = pos_V.mean(axis=(0, 1))
neg_z = neg_V.mean(axis=(0, 1))

# Check the raw profiles (these should include the ramp)
z_nm = z / 10.0

fig, axes = plt.subplots(2, 1, figsize=(10, 8))

# Plot 1: Raw potentials from PMEpot (should have ramps)
axes[0].plot(z_nm, pos_z * 1e3, 'b-', label='POS (raw from DX)', linewidth=2)
axes[0].plot(z_nm, neg_z * 1e3, 'r-', label='NEG (raw from DX)', linewidth=2)
axes[0].set_xlabel('z (nm)')
axes[0].set_ylabel('Potential (mV)')
axes[0].set_title('Raw potentials from PMEpot DX files (should include linear ramps)')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Plot 2: Difference (this is what we use for FMP)
diff = pos_z - neg_z
axes[1].plot(z_nm, diff * 1e3, 'k-', linewidth=2)
axes[1].set_xlabel('z (nm)')
axes[1].set_ylabel('POS - NEG (mV)')
axes[1].set_title('Difference: POS - NEG (before normalization)')
axes[1].grid(True, alpha=0.3)
axes[1].axhline(0, color='gray', linestyle='--', alpha=0.5)

plt.tight_layout()
plt.savefig('debug_raw_potentials.png', dpi=150)
print("\nSaved: debug_raw_potentials.png")

# Check if the profiles look linear (indicating ramps are present)
print(f"\nPOS potential range: {pos_z.min()*1e3:.1f} to {pos_z.max()*1e3:.1f} mV")
print(f"NEG potential range: {neg_z.min()*1e3:.1f} to {neg_z.max()*1e3:.1f} mV")
print(f"Difference range: {diff.min()*1e3:.1f} to {diff.max()*1e3:.1f} mV")

# Check for linearity (should be mostly linear if ramps dominate)
z_center_idx = len(z) // 2
left_half = diff[:z_center_idx]
right_half = diff[z_center_idx:]

from scipy.stats import linregress
slope, intercept, r_value, _, _ = linregress(z_nm, diff * 1e3)
print(f"\nLinear fit to (POS-NEG): slope={slope:.3f} mV/nm, R²={r_value**2:.4f}")
if r_value**2 > 0.95:
    print("  -> Difference is HIGHLY LINEAR (ramps dominate)")
else:
    print("  -> Difference is NOT very linear (molecular structure visible)")
