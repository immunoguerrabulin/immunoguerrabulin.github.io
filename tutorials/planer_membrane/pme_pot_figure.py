"""
Compute fractional membrane potential (FMP) from PMEpot DX files.

This script processes PMEpot output from two simulations (±V) to:
  1. Remove the linear field ramp from POS/NEG potentials
  2. Generate XY-averaged z-profiles
  3. Compute the combined membrane potential
  4. Calculate the fractional membrane potential (FMP)
  5. Generate visualization plots and output files

Theory: phi_mp(r) = [phi_tot(r;+V) - phi_tot(r;-V)] / (2V)
"""

import re
import csv
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

# Try to apply prettypyplot styling if available; fall back otherwise.
# We also attempt to obtain a preferred background color from prettypyplot
# and expose it as `BG_COLOR` for consistent figure saving.
PRETTY_IMPORTED = False
BG_COLOR = "#fafafa"  # default light background for saved figures
try:
    import prettypyplot as ppp

    PRETTY_IMPORTED = True
    # apply common initialization hooks if available
    if hasattr(ppp, "use_style"):
        ppp.use_style()
    elif hasattr(ppp, "set_style"):
        ppp.set_style()
    elif hasattr(ppp, "set"):
        ppp.set()
    elif hasattr(ppp, "style") and hasattr(ppp.style, "use"):
        ppp.style.use()

    # try to extract a background color from the module if exposed
    bg = None
    for attr in ("background", "bg", "get_background", "get_bg", "background_color"):
        if hasattr(ppp, attr):
            val = getattr(ppp, attr)
            try:
                bg = val() if callable(val) else val
            except Exception:
                bg = val
            if isinstance(bg, str) and bg:
                BG_COLOR = bg
                break
except Exception:
    PRETTY_IMPORTED = False
    BG_COLOR = "#fafafa"

# ============================================================================
# Configuration
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent
POS_DX = BASE_DIR / "pos.dx"
NEG_DX = BASE_DIR / "neg.dx"
OUT_DIR = BASE_DIR / "pme_pot_outputs"

# Simulation parameters
TEMPERATURE_K = 303.15      # simulation temperature (K)
FMP_CLIP_01 = False         # clip FMP to [0, 1] after normalization

# Electric field parameters
E_MAG = 0.00471959982                 # applied field magnitude (kcal/(mol·e·Å))
KCAL_PER_MOL_E_TO_V = 1.0 / 23.06055  # conversion: (kcal/mol/e) to V
BOX_Z_ANGSTROM = 439.38740475         # box z-dimension from .xsc file (Å)

# Physical constants
KB_J_PER_K = 1.380649e-23      # Boltzmann constant (J/K)
E_COULOMB = 1.602176634e-19    # elementary charge (C)

# ============================================================================
# DX file I/O
# ============================================================================

def read_dx_grid(path: Path):
    """
    Read OpenDX grid file and extract 3D array plus metadata.
    
    Returns:
        tuple: (data_array, (x, y, z), origin, deltas, field_name)
    """
    text = path.read_text()
    m = re.search(r"class gridpositions counts\s+(\d+)\s+(\d+)\s+(\d+)", text)
    if not m:
        raise ValueError(f"Missing gridpositions in {path}")
    nx, ny, nz = map(int, m.groups())
    mo = re.search(r"origin\s+([-\d\.Ee+]+)\s+([-\d\.Ee+]+)\s+([-\d\.Ee+]+)", text)
    if not mo:
        raise ValueError(f"Missing origin in {path}")
    ox, oy, oz = map(float, mo.groups())
    deltas = re.findall(r"delta\s+([-\d\.Ee+]+)\s+([-\d\.Ee+]+)\s+([-\d\.Ee+]+)", text)
    if len(deltas) < 3:
        raise ValueError(f"Missing delta lines in {path}")
    dx = float(deltas[0][0])
    dy = float(deltas[1][1])
    dz = float(deltas[2][2])
    field_match = re.search(r'object\s+"([^"]+)"\s+class field', text)
    field_name = field_match.group(1) if field_match else "PME potential (kT/e, T=300K)"

    start = text.find("data follows")
    if start < 0:
        raise ValueError(f"Missing data section in {path}")
    toks = re.findall(
        r"[-+]?\d*\.\d+(?:[Ee][+-]?\d+)?|[-+]?\d+(?:[Ee][+-]?\d+)?",
        text[start:],
    )
    vals = np.array(list(map(float, toks[: nx * ny * nz])), dtype=float)
    if vals.size != nx * ny * nz:
        raise ValueError(f"Expected {nx * ny * nz} values in {path}, got {vals.size}")
    arr = vals.reshape((nx, ny, nz), order="C")  # x-fastest
    x = ox + np.arange(nx) * dx
    y = oy + np.arange(ny) * dy
    z = oz + np.arange(nz) * dz
    return arr, (x, y, z), (ox, oy, oz), (dx, dy, dz), field_name


def write_dx_grid(path: Path, data, origin, deltas, field_name, comment=None):
    """
    Write 3D grid data to OpenDX format.
    
    Args:
        path: output file path
        data: 3D numpy array (nx, ny, nz)
        origin: (ox, oy, oz) grid origin
        deltas: (dx, dy, dz) grid spacing
        field_name: field identifier string
        comment: optional header comment
    """
    nx, ny, nz = data.shape
    total = nx * ny * nz
    header_comment = comment or field_name
    with path.open("w") as f:
        if header_comment:
            f.write(f"# {header_comment}\n")
        f.write(f"object 1 class gridpositions counts {nx} {ny} {nz}\n")
        f.write(f"origin {origin[0]:.6g} {origin[1]:.6g} {origin[2]:.6g}\n")
        f.write(f"delta {deltas[0]:.6g} 0 0\n")
        f.write(f"delta 0 {deltas[1]:.6g} 0\n")
        f.write(f"delta 0 0 {deltas[2]:.6g}\n")
        f.write(f"object 2 class gridconnections counts {nx} {ny} {nz}\n")
        f.write(f"object 3 class array type double rank 0 items {total} data follows\n")
        vals = data.reshape(-1, order="C")
        for i in range(0, len(vals), 3):
            chunk = vals[i : i + 3]
            f.write(" ".join(f"{v:.6g}" for v in chunk) + "\n")
        f.write('attribute "dep" string "positions"\n')
        f.write(f'object "{field_name}" class field\n')
        f.write('component "positions" value 1\n')
        f.write('component "connections" value 2\n')
        f.write('component "data" value 3\n')


# Physical calculations

def kT_over_e(T=300.0):
    """Thermal voltage: kT/e in Volts."""
    return (KB_J_PER_K * T) / E_COULOMB


def uniform_field_ramp(zA, sign, e_v_per_a):
    """
    Linear field ramp: -sign * E * z.
    
    Args:
        zA: z-coordinates (broadcast-compatible array)
        sign: +1 for POS, -1 for NEG
        e_v_per_a: electric field in V/Angstrom
    """
    return -sign * e_v_per_a * zA


def z_profile(phi_volts):
    """XY-average to get z-profile (1D array along Z)."""
    return phi_volts.mean(axis=(0, 1))


def xy_average(phi_volts):
    """
    Average over all X and Y values to get 1D profile along Z.
    
    This is an alias for z_profile() with a more descriptive name.
    Useful for creating 1D plots of potential vs. z-coordinate.
    
    Args:
        phi_volts: 3D array (nx, ny, nz)
    
    Returns:
        1D array of length nz
    """
    return phi_volts.mean(axis=(0, 1))


def yz_profile(phi_volts):
    """X-average to get y-z slice."""
    return phi_volts.mean(axis=0)


def clip_01(field):
    """Clip array to [0, 1]."""
    return np.clip(field, 0.0, 1.0)


def plot_1d_profile(z_vals, profile, title, ylabel, out_path, z_unit="nm", convert_to_mV=False):
    """
    Plot 1D profile along z-axis.
    
    Args:
        z_vals: z-coordinate array
        profile: 1D array of values to plot
        title: plot title
        ylabel: y-axis label
        out_path: output file path
        z_unit: unit for z-axis (default: "nm")
        convert_to_mV: if True, multiply profile by 1000
    """
    fig, ax = plt.subplots(figsize=(8, 5))
    # set figure background (visible in saved images)
    try:
        fig.patch.set_facecolor(BG_COLOR)
        ax.set_facecolor(BG_COLOR)
    except Exception:
        pass
    data = profile * 1e3 if convert_to_mV else profile
    ax.plot(z_vals, data, linewidth=2, color='black')
    ax.set_xlabel(f'z ({z_unit})', fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=13)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=170, facecolor=BG_COLOR)
    plt.close(fig)



# ============================================================================
# Main processing
# ============================================================================

OUT_DIR.mkdir(exist_ok=True)

# Load DX grids and convert to Volts
gpos_kTe, (x, y, z), origin, deltas, field_name_pos = read_dx_grid(POS_DX)
gneg_kTe, (x2, y2, z2), origin2, deltas2, field_name_neg = read_dx_grid(NEG_DX)

# Verify grids match
if gpos_kTe.shape != gneg_kTe.shape:
    raise ValueError("POS/NEG grid shapes do not match")
if not (np.allclose(x, x2) and np.allclose(y, y2) and np.allclose(z, z2)):
    raise ValueError("POS/NEG grid coordinates do not match")

# Convert from kT/e to Volts
kTe = kT_over_e(TEMPERATURE_K)
phi_pos_raw = gpos_kTe * kTe
phi_neg_raw = gneg_kTe * kTe

# Calculate field ramp contributions
E_V_per_A = E_MAG * KCAL_PER_MOL_E_TO_V  # V/Angstrom
zA = z.reshape(1, 1, -1)
ramp_pos = uniform_field_ramp(zA, +1, E_V_per_A)
ramp_neg = uniform_field_ramp(zA, -1, E_V_per_A)

# VMD PMEpot outputs molecular potentials WITHOUT ramps
# Add the ramps back to get total potentials
phi_pos_no_ramp = phi_pos_raw
phi_neg_no_ramp = phi_neg_raw
phi_pos_with_ramp = phi_pos_raw + ramp_pos
phi_neg_with_ramp = phi_neg_raw + ramp_neg

# ============================================================================
# Save corrected DX files
# ============================================================================

# Save ramp-removed potentials (in kT/e units)
pos_no_ramp_dx = OUT_DIR / "pos_no_ramp.dx"
neg_no_ramp_dx = OUT_DIR / "neg_no_ramp.dx"
write_dx_grid(pos_no_ramp_dx, phi_pos_no_ramp / kTe, origin, deltas, field_name_pos)
write_dx_grid(neg_no_ramp_dx, phi_neg_no_ramp / kTe, origin2, deltas2, field_name_neg)

# Save with-ramp potentials (in kT/e units)
pos_with_ramp_dx = OUT_DIR / "pos_with_ramp.dx"
neg_with_ramp_dx = OUT_DIR / "neg_with_ramp.dx"
write_dx_grid(pos_with_ramp_dx, phi_pos_with_ramp / kTe, origin, deltas, field_name_pos)
write_dx_grid(neg_with_ramp_dx, phi_neg_with_ramp / kTe, origin2, deltas2, field_name_neg)

# ============================================================================
# Compute spatial profiles
# ============================================================================

# XY-averaged z-profiles (in Volts)
phi_z_pos_with_ramp = z_profile(phi_pos_with_ramp)
phi_z_pos_no_ramp = z_profile(phi_pos_no_ramp)
phi_z_neg_with_ramp = z_profile(phi_neg_with_ramp)
phi_z_neg_no_ramp = z_profile(phi_neg_no_ramp)

# Combined membrane potential (average of POS and NEG ramp-removed profiles)
phi_z_membrane = 0.5 * (phi_z_pos_no_ramp + phi_z_neg_no_ramp)

# ============================================================================
# Calculate fractional membrane potential (FMP)
# ============================================================================

# FMP = [phi(+V) - phi(-V)] / (2*DeltaV)
# The factor of 2 accounts for the voltage difference between +V and -V simulations
# 
# For WITH-RAMP: potentials include opposite linear ramps, normalize and shift
# For NO-RAMP: normalize based on bulk region values to get 0→1 transition

# Calculate voltage span
fmp_delta_v = E_V_per_A * BOX_Z_ANGSTROM  # voltage per simulation (V)
print(f"Calculated voltage per simulation: {fmp_delta_v * 1e3:.2f} mV")

total_voltage_span = 2.0 * fmp_delta_v  # total difference between ±V
if total_voltage_span == 0.0:
    raise ValueError("Total voltage span must be non-zero")

# Compute FMP with ramp (linear ramp correction + shift)
fmp_with_ramp_3d = (phi_pos_with_ramp - phi_neg_with_ramp) / total_voltage_span + 0.5

# Compute FMP without ramp (normalize based on bulk values)
# Use the difference between POS and NEG (both are molecular potentials without ramps)
phi_diff_no_ramp = phi_pos_no_ramp - phi_neg_no_ramp
phi_diff_z = phi_diff_no_ramp.mean(axis=(0, 1))  # XY-averaged z-profile

# For a membrane centered at origin with bulk water at edges:
# Use the extremes (edges) as the two bulk reference points
z_nm_temp = z / 10.0

# Use outer regions as bulk (furthest from membrane at z=0)
edge_fraction = 0.12  # use outer 12% on each side
n_edge = int(len(z) * edge_fraction)

left_bulk = phi_diff_z[:n_edge].mean()
right_bulk = phi_diff_z[-n_edge:].mean()

print(f"Membrane at z=0, bulk water at edges")
print(f"Left bulk (z ≈ {z_nm_temp[:n_edge].mean():.1f} nm): {left_bulk * 1e3:.2f} mV")
print(f"Right bulk (z ≈ {z_nm_temp[-n_edge:].mean():.1f} nm): {right_bulk * 1e3:.2f} mV")
print(f"Bulk-to-bulk span: {(right_bulk - left_bulk) * 1e3:.2f} mV")

# Normalize: left bulk = 0, right bulk = 1
bulk_span = right_bulk - left_bulk
if abs(bulk_span) < 1e-6:
    print("Warning: Bulk span is very small, FMP may not be meaningful")
    fmp_no_ramp_3d = phi_diff_no_ramp * 0.0
else:
    fmp_no_ramp_3d = (phi_diff_no_ramp - left_bulk) / bulk_span

# Optional: clip to [0, 1] range
if FMP_CLIP_01:
    fmp_with_ramp_3d = clip_01(fmp_with_ramp_3d)
    fmp_no_ramp_3d = clip_01(fmp_no_ramp_3d)

# Compute z-profiles and y-z slices of FMP (only with-ramp retained)
fmp_z_with_ramp = z_profile(fmp_with_ramp_3d)
fmp_yz_with_ramp = yz_profile(fmp_with_ramp_3d)

# Convert coordinates to nm for plotting
z_nm = z / 10.0
y_nm = y / 10.0

# ============================================================================
# Save CSV output
# ============================================================================

csv_path = OUT_DIR / "z_profiles_pos_neg_membrane.csv"
with csv_path.open("w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(
        [
            "z_nm",
            "pos_with_ramp_mV",
            "pos_no_ramp_mV",
            "neg_with_ramp_mV",
            "neg_no_ramp_mV",
            "membrane_mV",
            "fmp_z_with_ramp",
        ]
    )
    writer.writerows(
        zip(
            z_nm,
            phi_z_pos_with_ramp * 1e3,
            phi_z_pos_no_ramp * 1e3,
            phi_z_neg_with_ramp * 1e3,
            phi_z_neg_no_ramp * 1e3,
            phi_z_membrane * 1e3,
            fmp_z_with_ramp,
        )
    )

# ============================================================================
# Generate plots
# ============================================================================

# Figure 1: POS/NEG ramp comparison
fig, axes = plt.subplots(2, 1, figsize=(7.0, 6.2), sharex=True)
try:
    fig.patch.set_facecolor(BG_COLOR)
    for ax in axes:
        ax.set_facecolor(BG_COLOR)
except Exception:
    pass

axes[0].plot(z_nm, phi_z_pos_with_ramp * 1e3, label="POS with ramp (VMD)")
axes[0].plot(z_nm, phi_z_pos_no_ramp * 1e3, label="POS without ramp")
axes[0].set_ylabel("Potential (mV)")
axes[0].set_title("POS: VMD potential vs ramp removed")
axes[0].legend()

axes[1].plot(z_nm, phi_z_neg_with_ramp * 1e3, label="NEG with ramp (VMD)")
axes[1].plot(z_nm, phi_z_neg_no_ramp * 1e3, label="NEG without ramp")
axes[1].set_xlabel("z (nm)")
axes[1].set_ylabel("Potential (mV)")
axes[1].set_title("NEG: VMD potential vs ramp removed")
axes[1].legend()

out_ramp_demo = OUT_DIR / "pos_neg_ramp_demo.png"
fig.tight_layout()
fig.savefig(out_ramp_demo, dpi=170, facecolor=BG_COLOR)
plt.close(fig)

# Figure 2: Combined membrane potential
plt.figure(figsize=(7.0, 4.0))
plt.plot(z_nm, phi_z_pos_no_ramp * 1e3, label="POS no ramp", alpha=0.7)
plt.plot(z_nm, phi_z_neg_no_ramp * 1e3, label="NEG no ramp", alpha=0.7)
plt.plot(z_nm, phi_z_membrane * 1e3, label="Combined (membrane potential)", linewidth=2.0)
plt.xlabel("z (nm)")
plt.ylabel("Potential (mV)")
plt.title("Membrane potential from POS/NEG combination")
plt.legend()
out_membrane = OUT_DIR / "membrane_potential.png"
plt.tight_layout()
plt.savefig(out_membrane, dpi=170, facecolor=BG_COLOR)
plt.close()

# Figure 2b: 1D FMP profile (XY-averaged)
plt.figure(figsize=(7.0, 4.0))
plt.plot(z_nm, fmp_z_with_ramp, linewidth=2.0, color='C0')
plt.xlabel("z (nm)")
plt.ylabel("FMP (unitless)")
plt.title("Fractional membrane potential (XY-averaged)")
plt.axhline(0, color='gray', linestyle=':', alpha=0.5)
plt.axhline(1, color='gray', linestyle=':', alpha=0.5)
plt.ylim(-0.2, 1.2)
plt.grid(True, alpha=0.3)
out_fmp_1d = OUT_DIR / "fmp_z_profile.png"
plt.tight_layout()
plt.savefig(out_fmp_1d, dpi=170, facecolor=BG_COLOR)
plt.close()

# ============================================================================
# FMP heatmap plotting function
# ============================================================================

def plot_yz_heatmap(
    field,
    y_nm_vals,
    z_nm_vals,
    title,
    out_path,
    scale=1e3,
    cbar_label="Potential (mV)",
):
    """Plot y-z heatmap of field data."""
    data = field * scale
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    # ensure background color is applied to saved figure and axes
    try:
        fig.patch.set_facecolor(BG_COLOR)
        ax.set_facecolor(BG_COLOR)
    except Exception:
        pass
    extent = [z_nm_vals[0], z_nm_vals[-1], y_nm_vals[0], y_nm_vals[-1]]
    im = ax.imshow(
        data,
        origin="lower",
        aspect="auto",
        extent=extent,
        cmap="coolwarm",
    )
    ax.set_xlabel("z (nm)")
    ax.set_ylabel("y (nm)")
    ax.set_title(title)
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label(cbar_label)
    fig.tight_layout()
    fig.savefig(out_path, dpi=170, facecolor=BG_COLOR)
    plt.close(fig)


# Figure 3: FMP heatmaps
fmp_label_with = f"FMP (ΔV={2*fmp_delta_v*1e3:.0f} mV total, with ramp)"

out_fmp_heat_with = OUT_DIR / "fmp_yz_heatmap_with_ramp.png"

plot_yz_heatmap(
    fmp_yz_with_ramp,
    y_nm,
    z_nm,
    "FMP (y-z heat map, with ramp)",
    out_fmp_heat_with,
    scale=1.0,
    cbar_label=fmp_label_with,
)

# ============================================================================
# Summary
# ============================================================================

print("\n" + "="*60)
print("Analysis complete!")
print("="*60)
print(f"\nOutput directory: {OUT_DIR}/\n")
print("DX files:")
print(f"  - {pos_no_ramp_dx.name}")
print(f"  - {neg_no_ramp_dx.name}")
print(f"  - {pos_with_ramp_dx.name}")
print(f"  - {neg_with_ramp_dx.name}\n")
print("Figures:")
print(f"  - {out_ramp_demo.name}")
print(f"  - {out_membrane.name}")
print(f"  - {out_fmp_1d.name}")
print(f"  - {out_fmp_heat_with.name}\n")
print(f"CSV data: {csv_path.name}\n")
print("="*60)
