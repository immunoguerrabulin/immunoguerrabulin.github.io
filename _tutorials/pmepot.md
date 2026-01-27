---
layout: page
title: Computing Fractional Membrane Potential
description: Separate the uniform field ramp and combine POS/NEG PME potentials.
img: tutorials/planer_membrane/neg_only_map_6.dat_center_45.bmp
importance: 1
category: analysis
---

<!-- prettier-ignore-start -->
> **📋 Tutorial Summary**  
> Learn how to compute the fractional membrane potential from PMEpot output. This method separates voltage-dependent contributions from the reaction-field potential, enabling quantitative analysis of transmembrane electric fields in MD simulations.
{: .block-tip }
<!-- prettier-ignore-end -->

---

## Overview

This tutorial walks through generating the **fractional membrane potential** of a planar membrane system. We cover:

1. The underlying theory (linear-response decomposition)
2. Setting up NAMD simulations with applied electric fields
3. Computing PMEpot maps in VMD
4. Post-processing to extract the membrane potential

---

## Inputs

| File                               | Description                         |
| ---------------------------------- | ----------------------------------- |
| `tutorials/planer_membrane/pos.dx` | PMEpot output for **+V** simulation |
| `tutorials/planer_membrane/neg.dx` | PMEpot output for **−V** simulation |

---

### Toy system

<figure style="text-align:center;margin:0.8rem 0 1.2rem 0">
  <span style="display:inline-block;width:420px;height:300px;overflow:hidden;border-radius:6px;box-shadow:0 3px 8px rgba(0,0,0,0.08)">
    <img src="/tutorials/planer_membrane/neg_only_map_4.dat.bmp" alt="Toy system snapshot" style="width:100%;height:100%;object-fit:cover;object-position:center;transform:scale(1.35);transform-origin:center;display:block" />
  </span>
  <figcaption style="margin-top:0.4rem;font-size:0.95em;color:#444">lipid bilayer with counterions in a box</figcaption>
</figure>

## Background

Biological membranes are essentially **electrical circuits**. The same physics from introductory electromagnetism applies—and this perspective lets us study membrane proteins quantitatively. Electrophysiology experiments measure ionic conductance through membranes; we can compute analogous quantities _in silico_ using methods developed since the 1990s.

This tutorial uses **linear-response theory** to generate a membrane potential map.

### 📚 Suggested Reading

<!-- prettier-ignore-start -->
> **Key References**
>
> 1. Roux, B. *"Influence of the membrane potential on the free energy of an intrinsic protein."*  
>    Biophys. J. **73**, 2980–2989 (1997). [PMC1181204](https://pmc.ncbi.nlm.nih.gov/articles/PMC1181204/)
>
> 2. Roux, B. *"The membrane potential and its representation by a constant electric field in computer simulations."*  
>    Biophys. J. **95**, 4205–4216 (2008). [PMC2567939](https://pmc.ncbi.nlm.nih.gov/articles/PMC2567939/)
{: .block-tip }
<!-- prettier-ignore-end -->

A brief review of the theory is presented below. The solution of the linearized Poisson–Boltzmann equation developed by Roux (1997) shows that the total electrostatic potential can be decomposed as

{% raw %}

$$
\phi_{\mathrm{tot}}(\mathbf{r}; V) = \phi_{\mathrm{rf}}(\mathbf{r}) + V\,\phi_{\mathrm{mp}}(\mathbf{r})
$$

{% endraw %}

In simple terms, this expression states that the total electrostatic potential $\phi_{\mathrm{tot}}(\mathbf{r};V)$ at position $\mathbf{r}$ in the presence of a transmembrane voltage $V$ can be written as the sum of two contributions. The first term, $\phi_{\mathrm{rf}}(\mathbf{r})$, is the reaction-field potential, which arises from the protein's fixed charges together with the polarization and ionic screening of the surrounding environment in the absence of an applied voltage. The second term describes the effect of the applied membrane voltage: $\phi_{\mathrm{mp}}(\mathbf{r})$ is a dimensionless function that represents the fraction of the membrane potential experienced at position $\mathbf{r}$, so that multiplying it by $V$ gives the voltage-dependent contribution to the electrostatic potential.

Now, using the previous linearized equation, we extend it to the use of PMEpot and the external field. If we take two simulations at opposite voltages, we can isolate the voltage-dependent part (central difference):

{% raw %}

$$
\phi_{\mathrm{tot}}(\mathbf{r}; -V) = \phi_{\mathrm{rf}}(\mathbf{r}) + (-V)\,\phi_{\mathrm{mp}}(\mathbf{r})
$$

{% endraw %}

and

{% raw %}

$$
\phi_{\mathrm{tot}}(\mathbf{r}; +V) = \phi_{\mathrm{rf}}(\mathbf{r}) + (+V)\,\phi_{\mathrm{mp}}(\mathbf{r})
$$

{% endraw %}

Combining them gives:

{% raw %}

$$
\begin{aligned}
\phi_{\mathrm{tot}}(\mathbf{r}; +V) - \phi_{\mathrm{tot}}(\mathbf{r}; -V)
&= \bigl[\phi_{\mathrm{rf}}(\mathbf{r}) + (+V)\,\phi_{\mathrm{mp}}(\mathbf{r})\bigr] - \bigl[\phi_{\mathrm{rf}}(\mathbf{r}) + (-V)\,\phi_{\mathrm{mp}}(\mathbf{r})\bigr] \\
&= (+V)\,\phi_{\mathrm{mp}}(\mathbf{r}) - (-V)\,\phi_{\mathrm{mp}}(\mathbf{r}) \\
&= 2V\,\phi_{\mathrm{mp}}(\mathbf{r})
\end{aligned}
$$

{% endraw %}

Now solving for $\phi_{\mathrm{mp}}$ gives:

{% raw %}

$$
\phi_{\mathrm{mp}}(\mathbf{r}) = \frac{\phi_{\mathrm{tot}}(\mathbf{r};+V) - \phi_{\mathrm{tot}}(\mathbf{r};-V)}{2V}
$$

{% endraw %}

---

### Implementation

We now implement this using **molecular dynamics**. This tutorial uses NAMD with the `eField` keyword, but most MD packages support applied electric fields.

<!-- prettier-ignore-start -->
> ⚠️ **Use NVT, not NPT**  
> NPT ensembles with external fields can introduce artifacts in the box dimensions. Run production with **NVT** for reliable membrane potential calculations.
{: .block-warning }
<!-- prettier-ignore-end -->

---

## Setting a Transmembrane Voltage in NAMD

To simulate a specific voltage across your simulation box (e.g., a transmembrane potential), you must apply a constant electric field. NAMD uses specific internal units, so you cannot simply enter the voltage in Volts.

### 1. The NAMD Configuration

Add the following lines to your production script (`.inp`):

```tcl
eField on
eField 0 0 {EZ_Value}
```

Where `{EZ_Value}` is the electric field vector component in the Z-direction.

### 2. Calculating `{EZ_Value}` using the 0.0434 Factor

A useful shortcut for this calculation is the direct unit equivalence:

> 1 Unit $\left(\frac{\text{kcal}}{\text{mol} \cdot \text{Å} \cdot e}\right)$ is equivalent to $0.0434\,\text{V}/\text{Å}$.

Using this equivalence, the formula becomes:

{% raw %}

$$
E_{\text{NAMD}} = \frac{V_{\text{target}}}{L_z \times 0.0434}
$$

{% endraw %}

Where:

- $V_{\text{target}}$ is the voltage in Volts.
- $L_z$ is the box length in Angstroms (Å).
- $0.0434$ is the conversion factor representing $\text{V}/\text{Å}$ per NAMD unit.

### Example Calculation: +90 mV

**Scenario:** You want +90 mV across a box length ($L_z$) of $100~\text{Å}$.

<!-- prettier-ignore-start -->
> 💡 **Tip:** Find the box size in the `.xsc` file—the `c_z` column gives $L_z$:
> ```
> # NAMD extended system configuration output file
> #$LABELS step a_x a_y a_z b_x b_y b_z c_x c_y c_z o_x o_y o_z
> ```
{: .block-tip }
<!-- prettier-ignore-end -->

1. **Convert to Volts:**

{% raw %}

$$
90 \text{ mV} = 0.09 \text{ V}
$$

{% endraw %}

2. **Calculate Electric Field in V/Å:**

{% raw %}

$$
\frac{0.09~\text{V}}{100~\text{Å}} = 0.0009~\text{V}/\text{Å}
$$

{% endraw %}

3. **Convert to the NAMD Units:**

Divide by the equivalence factor ($0.0434$):

{% raw %}

$$
E_{\text{NAMD}} = \frac{0.0009}{0.0434} \approx 0.02074~\text{kcal}/(\text{mol}\cdot\text{Å}\cdot e)
$$

{% endraw %}

4. **Resulting Input:**

```tcl
eField on
eField 0 0 0.02074
```

<!-- prettier-ignore-start -->
> 📝 **Note on the constant**  
> The factor $0.0434$ is the inverse of the thermodynamic conversion: $1\,\text{eV} \approx 23.06\,\text{kcal/mol}$.
{: .block-tip }
<!-- prettier-ignore-end -->

---

### Restraints for PMEPot Analysis

<!-- prettier-ignore-start -->
> ⚠️ **Important for membrane proteins**  
> Apply **position restraints** to protein backbone atoms during the sampling window.
>
> PMEpot averages the potential over multiple frames. If the protein translates or rotates, the resulting map will be spatially "smeared" relative to the fixed grid. Restraining the backbone keeps the protein aligned and prevents motion artifacts.
{: .block-warning }
<!-- prettier-ignore-end -->

---

## Computing the Electrostatic Potential with VMD

Once trajectories are complete, compute PMEpot maps in VMD. For reproducibility, run a **Tcl script** rather than using the GUI.

<details>
<summary><strong>📄 Example Tcl script (click to expand)</strong></summary>

```tcl
# load PMEPot plugin
package require pmepot

# load structure and trajectory (adjust paths as needed)
mol new ../step5_input.psf type psf waitfor all
mol addfile centered.dcd type dcd waitfor all

# set files/parameters
set xscfile pos.xsc
set gridres 2.0          ;# grid spacing in Angstroms
set ewald   0.25         ;# Ewald factor (default for periodic PMEPot)

# compute potential and write DX
pmepot -sel [atomselect top "all"] \
  -frames all \
  -xscfile $xscfile \
  -grid $gridres \
  -ewaldfactor $ewald \
  -dxfile pos_epot.dx

exit
```

</details>

| Parameter     | Description                                                   |
| ------------- | ------------------------------------------------------------- |
| `xscfile`     | Box vectors from NAMD (`.xsc`); `c_z` = $L_z$                 |
| `gridres`     | Grid spacing (Å); smaller = higher resolution, longer runtime |
| `ewaldfactor` | PME screening (default 0.25 is usually fine)                  |
| `-sel`        | Atom selection; narrow to `protein and name CA` for subsets   |

---

## Run the Analysis

```bash
python tutorials/planer_membrane/pme_pot_figure.py
```

<!-- prettier-ignore-start -->
> **Headless mode** (no GUI windows):
> ```bash
> MPLBACKEND=Agg python tutorials/planer_membrane/pme_pot_figure.py
> ```
{: .block-tip }
<!-- prettier-ignore-end -->

### What the Script Computes

1. **Adds the linear field ramp** back to the VMD PMEpot output (VMD outputs molecular potentials _without_ the applied field)
2. **Builds z-profiles** (XY-averaged) for both with-ramp and no-ramp potentials
3. **Combines POS/NEG** into a single membrane-potential profile
4. **Computes fractional membrane potential (FMP)**:  
   $\text{FMP} = \frac{\phi_{+V} - \phi_{-V}}{2\Delta V} + 0.5$

---

### Output Files

<details>
<summary><strong>📁 Generated files (click to expand)</strong></summary>

| Type                  | Files                                                                             |
| --------------------- | --------------------------------------------------------------------------------- |
| **DX (ramp removed)** | `pos_no_ramp.dx`, `neg_no_ramp.dx`                                                |
| **DX (with ramp)**    | `pos_with_ramp.dx`, `neg_with_ramp.dx`                                            |
| **CSV**               | `z_profiles_pos_neg_membrane.csv`                                                 |
| **Figures**           | `pos_neg_ramp_demo.png`, `membrane_potential.png`, `fmp_yz_heatmap_with_ramp.png` |

All outputs are written to `tutorials/planer_membrane/pme_pot_outputs/`.

</details>

---

## Results

### Ramp Removal (POS/NEG z-profiles)

<figure style="text-align:center;margin:1.5rem 0">
  <img src="/tutorials/planer_membrane/pme_pot_outputs/pos_neg_ramp_demo.png" alt="Ramp removal demo" style="max-width:100%;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,0.1)" />
  <figcaption style="margin-top:0.5rem;font-size:0.9em;color:#666"><strong>Figure 1.</strong> XY-averaged z-profiles showing the linear ramp contribution.</figcaption>
</figure>

### Membrane Potential (Combined POS/NEG)

<figure style="text-align:center;margin:1.5rem 0">
  <img src="/tutorials/planer_membrane/pme_pot_outputs/membrane_potential.png" alt="Membrane potential" style="max-width:100%;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,0.1)" />
  <figcaption style="margin-top:0.5rem;font-size:0.9em;color:#666"><strong>Figure 2.</strong> Combined membrane potential after ramp removal.</figcaption>
</figure>

### Fractional Membrane Potential (FMP)

<figure style="text-align:center;margin:1.5rem 0">
  <img src="/tutorials/planer_membrane/pme_pot_outputs/fmp_yz_heatmap_with_ramp.png" alt="FMP heat map" style="max-width:100%;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,0.1)" />
  <figcaption style="margin-top:0.5rem;font-size:0.9em;color:#666"><strong>Figure 3.</strong> FMP heat map (y–z plane, x-averaged). The potential is flat in bulk water and transitions linearly across the membrane.</figcaption>
</figure>

---

## Validation

The fractional membrane potential should be **flat in bulk** and **linear across the membrane**.

### Comparison with Theory

Compare our 1D result to the analytic Poisson–Boltzmann solution from Roux (2008):

<div style="display:flex;gap:1.5rem;flex-wrap:wrap;align-items:flex-start;justify-content:center;margin:1.5rem 0">
  <figure style="flex:1;min-width:280px;max-width:55%;margin:0">
    <img src="/tutorials/planer_membrane/pme_pot_outputs/fmp_z_profile.png" alt="FMP 1D z-profile" style="width:100%;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,0.1)" />
    <figcaption style="text-align:center;font-size:0.9em;margin-top:0.5rem;color:#666"><strong>This tutorial</strong> — FMP along z (XY-averaged)</figcaption>
  </figure>
  <figure style="flex:0 1 35%;min-width:200px;max-width:40%;margin:0">
    <img src="/tutorials/planer_membrane/roux2008.png" alt="Roux 2008 Fig 1C" style="width:100%;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,0.08)" />
    <figcaption style="text-align:center;font-size:0.9em;margin-top:0.5rem;color:#666"><strong>Roux (2008) Fig. 1C</strong></figcaption>
  </figure>
</div>

<!-- prettier-ignore-start -->
> **Good agreement!** The MD-derived FMP reproduces the expected behavior from continuum electrostatics. There are some deviations from noise that can be solved by running the simulation longer.
{: .block-tip }
<!-- prettier-ignore-end -->
