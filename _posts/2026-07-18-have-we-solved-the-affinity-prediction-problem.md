---
layout: post
title: "Have We Solved Binding-Affinity Prediction?"
description: "Notes on a recent perspective about biomolecular ensembles, affinity prediction, and the benchmarks used to evaluate AI models."
tags: [science]
categories: [science]
published: true
---

Machine learning for biology and chemistry has promised a great deal. As new structure and affinity models appear, however, it is becoming harder to distinguish genuine generalization from impressive interpolation within familiar chemical and structural space. More recently, Chai Discovery [made headlines for raising $400 million](https://www.nytimes.com/2026/07/14/business/dealbook/chai-discovery-ai-drug-development.html) to use AI to accelerate drug discovery.


Its hard to avoid more AI in chemistry headlines...I recently came across a Perspective in *The Journal of Physical Chemistry Letters*, ["Predicting Biomolecular Interactions in the Next Decade: Physics-Based Methods Meet AI-Driven Approaches"](https://pubs.acs.org/doi/10.1021/acs.jpclett.6c01412). It provides a useful overview of recent developments in biomolecular modeling. Ultimately, we want thermodynamic and kinetic observables derived from high-dimensional molecular ensembles. Physics-based methods have a formal, although approximate, connection to thermodynamic weighting; machine-learning methods can generate structures efficiently, but the probabilities assigned to those structures are not necessarily connected to a partition function. The probability of observing a structure from a diffusion model is not grounded to physics. 

Two issues from the Perspective have stayed with me. The first is whether learned models can generate physically meaningful conformational ensembles. The second is whether our current benchmarks can tell us when an affinity model has learned transferable molecular interactions rather than the regularities of its training set.

## Affinity is an ensemble problem

In statistical mechanics, binding affinity is an ensemble observable, not a property of a single pose. A model can generate a convincing protein-ligand complex and still predict the wrong affinity because it misrepresents conformational reorganization, solvation, entropy, or the relative weights of alternative states. Generating multiple structures is therefore necessary in many systems, but it is not sufficient: the structures must also have meaningful statistical weights.

Sampling these ensembles has always been difficult in molecular simulation. Umbrella sampling, metadynamics, replica exchange, and related enhanced-sampling methods were developed because straightforward dynamics often fails to cross important barriers on accessible timescales. In that respect, the current development of learned ensemble generators resembles an older history in molecular simulation. Producing configurations is the easy part. Several innovations were required to allow simulations to sample more regions of phase space and to derive their statistical weights.

Several adaptations of AlphaFold2 illustrate the progress that has already been made. Del Alamo and colleagues showed that stochastic subsampling of multiple-sequence alignments could encourage AlphaFold2 to generate alternative conformations ([del Alamo et al.](https://elifesciences.org/articles/75751)). AF-Cluster subsequently grouped sequences in an MSA using DBSCAN and supplied the resulting clusters separately to AlphaFold2, recovering distinct structural states in several systems. These results suggest that different subsets of evolutionary information can favor different conformations, although the frequency with which AlphaFold2 generates a state should not automatically be interpreted as its equilibrium population ([Wayment-Steele et al.](https://www.nature.com/articles/s41586-023-06832-9)).

Other innovations have followed, including [DEERFold](https://www.nature.com/articles/s41467-025-62582-4), [ExEnDiff](https://journals.aps.org/prxlife/abstract/10.1103/PRXLife.3.023013), and [ConforNets](https://arxiv.org/abs/2604.18559v1). ExEnDiff is particularly interesting because it guides a pretrained diffusion-based ensemble sampler using experimental measurements. The idea is similar to what has been done with restrained-ensemble simulations that complement MD with DEER experiments ([Roux & Islam](https://pubs.acs.org/doi/10.1021/jp3110369)).  Its framework can incorporate information associated with NMR, SAXS, and cryo-EM, including observables such as the radius of gyration, end-to-end distance, and secondary-structure content. Rather than relying entirely on the distribution learned from structural or simulation data, the model uses measurements to restrict the generated ensemble toward conformations consistent with the experiment.

This hybrid strategy may be more scientifically useful than treating generative models as direct replacements for molecular dynamics. A learned generator can provide rapid exploration of configurational space, while simulations, physical energy functions, and experimental measurements can be used to reweight or validate the resulting structures. At the same time, agreement with a small set of observables does not establish that the entire high-dimensional equilibrium distribution is correct. The relevant test is whether the ensemble predicts orthogonal measurements and thermodynamic properties that were not used during generation.

The ability to repurpose pretrained structure models is encouraging, especially given how costly they are to train. Learned generators may eventually become much more efficient than conventional Langevin integration for producing decorrelated configurations or proposing transitions between metastable states. Whether they are better samplers in a statistical-mechanical sense, however, depends on whether they preserve the correct state populations and reproduce the observables of interest.

We can therefore imagine several kinds of reference distributions for future models. Some may learn force-field-dependent ensembles from molecular-dynamics trajectories under specified conditions, in a similar spirit to BioEmu. Others may begin with a learned structural prior and condition it on experimental measurements, as in ExEnDiff. In either case, the target should not be described as an unqualified ground-truth distribution: it will depend on temperature, solution conditions, protonation states, the physical model, the available experiments, and the uncertainties associated with each source of information.

{% include figure.liquid path="assets/img/blog/have-we-solved-the-affinity-prediction-problem/figure2-modeling-timeline.jpg" class="img-fluid rounded z-depth-1 mx-auto d-block" max-width="100%" alt="Timeline with four horizontal tracks (Resources & evaluation, Template-based & ab initio, Machine/Deep Learning, and Docking & MD) plotting methods such as PDB, CASP1, MODELLER, Rosetta, AlphaFold, RoseTTAFold, AF3, Boltz-2, AMBER, CHARMM, GROMACS, DiffDock, and BioEmu from 1970 to 2025." caption="Taken from Figure 2 of the <a href='https://pubs.acs.org/doi/10.1021/acs.jpclett.6c01412'>Perspective</a>: a timeline of the various methodologies for modeling biomolecules." zoomable=true %}

## Benchmarks can reward familiarity

Even a good ensemble generator does not solve the second problem: how we evaluate these models, and whether their benchmark performance reflects real use.

Data leakage in molecular machine learning is not limited to exact duplicates. Related ligands, homologous proteins, or similar protein-ligand interaction patterns can occur in both training and test sets. A model can then interpolate among familiar systems while appearing to generalize to new ones.

<style>
.concept-callout {
  margin: 1.25rem 0;
  border: 1px solid var(--global-divider-color);
  border-radius: 1.1rem;
  background: var(--global-card-bg-color);
  overflow: hidden;
}

.concept-callout summary {
  position: relative;
  display: grid;
  gap: 0.35rem;
  padding: 1rem 1.2rem;
  cursor: pointer;
  list-style: none;
}

.concept-callout summary::-webkit-details-marker {
  display: none;
}

.concept-callout summary::after {
  content: "+";
  position: absolute;
  right: 1.2rem;
  top: 0.9rem;
  font-size: 1.35rem;
  line-height: 1;
  color: var(--global-theme-color);
}

.concept-callout[open] summary::after {
  content: "\2212";
}

.concept-callout-eyebrow {
  font-size: 0.74rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--global-theme-color);
}

.concept-callout-title {
  font-size: 1.02rem;
  font-weight: 600;
  line-height: 1.45;
  padding-right: 2rem;
}

.concept-callout-body {
  padding: 0 1.2rem 1.2rem;
  line-height: 1.65;
}

.concept-callout-body p {
  margin: 0;
}
</style>

<details class="concept-callout">
  <summary><span class="concept-callout-eyebrow">Concept</span><span class="concept-callout-title">What is data leakage?</span></summary>
  <div class="concept-callout-body">
    <p>In the context of benchmarks for affinity prediction, leakage happens when a ligand or protein&ndash;ligand complex that closely resembles one already in the training set also shows up in the evaluation set. The model can then look accurate by effectively recognizing something it has seen before, rather than by learning transferable binding physics&mdash;which inflates its reported performance.</p>
  </div>
</details>

Leak-Proof PDBBind addresses this problem by reorganizing PDBBind to reduce similarity across proteins, ligands, and protein-ligand interaction fingerprints ([Leak-Proof PDBBind](https://pubs.acs.org/doi/10.1021/acs.jpcb.5c08598)). A more recent benchmark takes a complementary approach: it uses a temporal split and reports performance across ligand-similarity tiers. Rather than asking only for one aggregate correlation, it asks how quickly performance deteriorates as the test chemistry becomes less familiar. Its ligand-only baseline is especially useful as a diagnostic, because it measures how much benchmark performance can be obtained without representing the protein at all ([systematic data leakage in affinity benchmarks](https://www.biorxiv.org/content/10.64898/2026.06.29.735309v1)).

This is a more precise problem than saying that researchers have failed to clean their datasets. Even carefully curated datasets can produce misleading evaluations when the splitting procedure does not reflect the intended use of the model. For affinity prediction, the relevant concerns are domain shift, analog redundancy, incomplete coverage of chemical space, heterogeneous measurements, and experimental uncertainty.

Recent results reported for Boltz-2 and Isomorphic Labs' IsoDDE should be viewed in that context. The leakage analysis does not demonstrate that these models are useless, and it does not invalidate every independent result. It does suggest that strong performance on established free-energy benchmarks, such as the OpenFE benchmark set and standard relative free-energy (FEP) series, cannot by itself establish generalization to unfamiliar ligands or targets ([IsoDDE technical report](https://doi.org/10.5281/zenodo.19699685)). Pat Walters makes a related point. Cofolding performance tends to weaken as systems become less similar to the training data, and tests involving allostery or binding-site mutations expose limitations that ordinary pose benchmarks can miss. That points to a need for stronger evaluation rather than a blanket dismissal of the models (which actually could be useful in some systems). The critical question is not whether a model obtains a high average score, but where that score comes from and how performance changes with novelty.

Predictions should also be accompanied by calibrated uncertainty estimates. Ideally, an evaluation would distinguish uncertainty arising from experimental variability from uncertainty caused by limited training coverage or model inadequacy. A model that knows when it is extrapolating may be more scientifically useful than one with a slightly better average error but poorly calibrated confidence.

## What does the future look like? 

A static benchmark is unlikely to settle the question. What the field needs is sustained, independent, prospective evaluation in which predictions are frozen before the corresponding structures or affinity measurements are released. Similar to the language model benchmarks. This would not have to begin from scratch. D3R has run blinded challenges on protein-ligand poses and affinities, and SAMPL, CACHE, and OpenADMET offer related models for prospective, experimentally grounded evaluation ([Drug Design Data Resource](https://drugdesigndata.org/about/publications)). The opportunity is to make this kind of testing a central and continuous part of affinity-model development.

Such evaluations should distinguish among pose prediction, ranking within a congeneric series, relative-affinity prediction, and absolute-affinity prediction. They should stratify results by ligand and target novelty, include repeated or orthogonal experimental measurements where possible, and assess uncertainty calibration in addition to correlation and average error.

So, have we solved binding-affinity prediction? Not yet. We have models that appear highly useful within familiar chemical and structural neighborhoods, and those models will probably improve rapidly. The harder claim, that they can provide calibrated affinity predictions for novel targets and chemotypes under well-defined conditions, remains unproven. Progress will depend as much on ensembles, data curation, uncertainty, and prospective evaluation as it will on larger models. In the end, the same challenges we are taught about in introductory computer science still plague the affinity prediction field. For now, machine learning and physics remain complementary, and the strongest progress will come from combining them. 

## References

1. *Predicting Biomolecular Interactions in the Next Decade: Physics-Based Methods Meet AI-Driven Approaches.* <br> Ruqaiya Khalil, Elena Frasnetti, Han Kurt, Tareq Hameduh, Mohd Athar, Giorgio Colombo, and Attilio Vittorio Vargiu. <br> *The Journal of Physical Chemistry Letters* **2026**, Articles ASAP. <br> DOI: [10.1021/acs.jpclett.6c01412](https://doi.org/10.1021/acs.jpclett.6c01412)
2. *Sampling alternative conformational states of transporters and receptors with AlphaFold2.* <br> Diego del Alamo, Davide Sala, Hassane S. Mchaourab, and Jens Meiler. <br> *eLife* **11**, e75751 (2022). <br> DOI: [10.7554/eLife.75751](https://doi.org/10.7554/eLife.75751)
3. *Predicting multiple conformations via sequence clustering and AlphaFold2.* <br> Hannah K. Wayment-Steele, Adedolapo Ojoawo, Renee Otten, Julia M. Apitz, Warintra Pitsawong, Marc Hömberger, Sergey Ovchinnikov, Lucy Colwell, and Dorothee Kern. <br> *Nature* **625**, 832-839 (2024). <br> DOI: [10.1038/s41586-023-06832-9](https://doi.org/10.1038/s41586-023-06832-9)
4. *Modeling protein conformational ensembles by guiding AlphaFold2 with Double Electron Electron Resonance (DEER) distance distributions.* <br> Tianqi Wu, Richard A. Stein, Te-Yu Kao, Benjamin Brown, and Hassane S. Mchaourab. <br> *Nature Communications* **16**, 7107 (2025). <br> DOI: [10.1038/s41467-025-62582-4](https://doi.org/10.1038/s41467-025-62582-4)
5. *ExEnDiff: An Experiment-Guided Diffusion Model for Protein Conformational Ensemble Generation.* <br> Yikai Liu, Zongxin Yu, Richard J. Lindsay, Guang Lin, Ming Chen, Abhilash Sahoo, and Sonya M. Hanson. <br> *PRX Life* **3**, 023013 (2025). <br> DOI: [10.1103/PRXLife.3.023013](https://doi.org/10.1103/PRXLife.3.023013)
6. *ConforNets: Latents-Based Conformational Control in OpenFold3.* <br> Minji Lee, Colin Kalicki, Minkyu Jeon, Aymen Qabel, Alisia Fadini, and Mohammed AlQuraishi. <br> *arXiv*, arXiv:2604.18559 (2026). <br> DOI: [10.48550/arXiv.2604.18559](https://doi.org/10.48550/arXiv.2604.18559)
7. *Restrained-Ensemble Molecular Dynamics Simulations Based on Distance Histograms from Double Electron-Electron Resonance Spectroscopy.* <br> Benoît Roux and Shahidul M. Islam. <br> *The Journal of Physical Chemistry B* **117**, 4733-4739 (2013). <br> DOI: [10.1021/jp3110369](https://doi.org/10.1021/jp3110369)
8. *Leak Proof PDBBind: A Reorganized Data Set of Protein-Ligand Complexes for More Generalizable Binding Affinity Prediction.* <br> Jie Li, Xingyi Guan, Oufan Zhang, Kunyang Sun, Yingze Wang, Dorian Bagni, and Teresa Head-Gordon. <br> *The Journal of Physical Chemistry B* **130**, 730-740 (2026). <br> DOI: [10.1021/acs.jpcb.5c08598](https://doi.org/10.1021/acs.jpcb.5c08598)
9. *Identifying and Addressing Systematic Data Leakage in Protein-Ligand Affinity Benchmarks.* <br> Björn Mattsson and W. Patrick Walters. <br> *bioRxiv* (preprint), version 1, posted June 30, 2026. <br> DOI: [10.64898/2026.06.29.735309](https://doi.org/10.64898/2026.06.29.735309)
10. *Accurate Predictions of Novel Biomolecular Interactions with IsoDDE.* <br> Isomorphic Labs Team. <br> Zenodo, version 2, February 10, 2026. <br> DOI: [10.5281/zenodo.19699685](https://doi.org/10.5281/zenodo.19699685)