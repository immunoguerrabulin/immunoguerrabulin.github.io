---
layout: post
title: "The Ethical Quagmires of AI Drug Design"
description: "I revist a paper I read in 2022 about the dual-use of AI driven drug discovery"
tags: [science]
categories: [science]
---

## Background

On April 4, 2022, GPT-3 was still mostly an API-mediated tool rather than a consumer chatbot. Generative AI had not yet reached the general public in the way it has now. Back then, I was a first-year graduate student in Chemistry at the University of Chicago, and for journal club I chose to discuss a paper on the dual-use risks of AI-powered drug discovery [[1]](#ref-urbina2022). The paper came out of Spiez CONVERGENCE, a workshop hosted by Spiez Laboratory to examine how cutting-edge research in chemistry, biology, and related technologies might be misused [[2]](#ref-spiez-convergence).

As an aside, it has now been a couple of years since that conference. Spiez CONVERGENCE released another report in 2024 that returned to questions around digitalization, automation, and artificial intelligence [[3]](#ref-spiez-convergence2024). To me, the fact that the impact first raised in 2022 kept coming up shows the importance of keeping these discussions ongoing.

At the time, I was already familiar with computational tools for drug design, including molecular docking and free-energy calculations. I viewed them primarily as tools for discovering safer and more effective therapeutics. I had not yet fully considered their darker potential. If a model can optimize molecules for a desired biological property, what happens when the desired outcome is harm? That question is what makes the 2022 paper especially worth revisiting now, during a period of rapid progress in generative AI.

## Commentary

The drug discovery setting is usually framed around therapeutic goals. In practice, that means identifying molecules that bind a target, improving potency, reducing toxicity, and eventually finding something that can be synthesized and tested. The uncomfortable point raised by Urbina and colleagues is that the same optimization machinery can be redirected. A model that normally penalizes toxicity can instead be asked to reward predicted toxicity while preserving other desirable molecular properties such as bioactivity [[1]](#ref-urbina2022).

The software used in the paper was MegaSyn. I think this distinction matters because MegaSyn is not just a generic "AI drug design model." MegaSyn combines SMILES-based generative models with optimization, analog generation, and estimates of synthetic viability [[4]](#ref-megasyn2022). The risk is not molecule generation alone. It is generation paired with scoring and some estimate of whether a molecule could plausibly be made.

The ethical concern is not that AI systems spontaneously decide to invent weapons. It is that optimization systems can be redirected by changing their objectives. In the dual-use demonstration, the authors used an LD50-based toxicity model, where LD50 refers to the dose expected to kill 50% of a tested population. LD50 also depends on context, including the species being tested, the route of exposure, and the assay conditions. The authors then inverted the usual goal. Instead of penalizing toxicity, the workflow rewarded it [[1]](#ref-urbina2022). The paper reports that this generated a large set of candidate molecules predicted to be highly toxic, including compounds predicted to be more toxic than VX, a highly toxic nerve agent. This was an in silico result, not experimental validation. The striking point is that several of these compounds were not in the original training data. The model did not simply retrieve information from its training set. It had generalized, producing novel toxic candidates from structural patterns it had learned to associate with lethality.

This is where the governance problem becomes difficult. None of the individual pieces are inherently bad. Toxicity datasets are useful for designing safer drugs. Retrosynthetic planning tools help chemists decide whether a molecule is worth pursuing. Commercial synthesis is a normal part of medicinal chemistry. The concern is what happens when these useful pieces are combined into an automated design pipeline with a harmful goal. Until recently, deep expertise served as a natural barrier to harm. A bad actor would usually have needed a team of specialists. With tools that can suggest retrosynthetic routes and increasingly assist with protocol-level reasoning, some of that barrier may be lower than it used to be, even though practical synthesis still requires expertise, materials, equipment, and regulatory friction.

These are some slides from my talk. They helped me separate the problem into two parts. First, there was the reward-function change itself. Then there was the broader misuse pathway around open tools, synthesis, and access.

<div class="row align-items-start justify-content-center">
  <div class="col-md-6 mb-4">
    {% include figure.liquid path="assets/img/blog/the-ethical-quagmires-of-ai-drug-design/what-is-going-on-change.png" class="img-fluid rounded z-depth-1 mx-auto d-block" max-width="100%" alt="Slide titled What is going on and what did they change, explaining the reward change in MegaSyn with t-SNE and toxicity plots" caption="MegaSyn reward-function change discussed by Urbina and colleagues <a href='#ref-urbina2022'>[1]</a>." zoomable=true %}
  </div>
  <div class="col-md-6 mb-4">
    {% include figure.liquid path="assets/img/blog/the-ethical-quagmires-of-ai-drug-design/why-is-misuse-problem.png" class="img-fluid rounded z-depth-1 mx-auto d-block" max-width="100%" alt="Slide titled Why is misuse a potential problem with bullets about open-source software, toxicity data, model misuse, and chemical synthesis" caption="Why misuse is a potential problem for AI-powered drug discovery." zoomable=true %}
  </div>
</div>

{% include figure.liquid path="assets/img/blog/the-ethical-quagmires-of-ai-drug-design/aizynthfinder-retrosynthesis.png" class="img-fluid rounded z-depth-1 mx-auto d-block" max-width="760px" alt="Slide showing the AiZynthFinder retrosynthetic planning article in the Journal of Cheminformatics" caption="AiZynthFinder as an example of open-source retrosynthetic planning software <a href='#ref-genheden2020'>[5]</a>." zoomable=true %}

Although retrosynthetic planning is still an open research direction in computational chemistry, many people are working on this problem, including efforts to make pathways that are greener or use less dangerous reagents and techniques. I think it is a good thing that these risks were already being discussed in 2022. Researchers building these tools will probably need to think carefully about who gets access, what parts of the workflow should be restricted, and how much friction is appropriate before the software becomes useful for the wrong reasons.

Another point to consider is accountability. When harmful content is generated with a tool, the blame usually falls on the person who generated it. The notion of responsibility is also relevant, and somewhat unclear, when it comes to autonomous labs. It is less clear what responsibility belongs to the developers when a system is misused in a way they did not anticipate. This question feels more urgent as frontier models become more capable.

In retrospect, the biosafety questions raised by the 2022 paper have expanded into a broader conversation about advanced AI systems. In June 2026, Anthropic described safeguards, fallback routing, and trusted-access programs for highly capable biology and chemistry model use [[6]](#ref-anthropic-fable-mythos2026). OpenAI's Safety Bug Bounty also accepts AI safety and abuse reports, and OpenAI notes that private campaigns may focus on biorisk content [[7]](#ref-openai-safety-bug-bounty2026). Deciding who gets access can reduce misuse, but it can also limit good uses. It is difficult to know where this will end up, but recent advances in LLMs have accelerated the need for careful regulation of technologies that can be used with bad intentions.

## References

1. <a id="ref-urbina2022"></a>Urbina F, Lentzos F, Invernizzi C, Ekins S. "Dual Use of Artificial Intelligence-powered Drug Discovery." _Nat Mach Intell_. 2022 Mar;4(3):189-191. doi: [10.1038/s42256-022-00465-9](https://doi.org/10.1038/s42256-022-00465-9). Epub 2022 Mar 7. PMID: [36211133](https://pubmed.ncbi.nlm.nih.gov/36211133/); PMCID: [PMC9544280](https://pmc.ncbi.nlm.nih.gov/articles/PMC9544280/).
2. <a id="ref-spiez-convergence"></a>Spiez Laboratory. "Spiez CONVERGENCE." Swiss Federal Office for Civil Protection. [https://www.spiezlab.admin.ch/en/spiez-convergence-en](https://www.spiezlab.admin.ch/en/spiez-convergence-en).
3. <a id="ref-spiez-convergence2024"></a>Spiez Laboratory. "Spiez CONVERGENCE 2024." Swiss Federal Office for Civil Protection. [https://www.spiezlab.admin.ch/dam/it/sd-web/SmmMK5KGL8Ph/LaborSpiezConvergence2024_en.pdf](https://www.spiezlab.admin.ch/dam/it/sd-web/SmmMK5KGL8Ph/LaborSpiezConvergence2024_en.pdf).
4. <a id="ref-megasyn2022"></a>Urbina F, Lowden CT, Culberson JC, Ekins S. "MegaSyn: Integrating Generative Molecular Design, Automated Analog Designer, and Synthetic Viability Prediction." _ACS Omega_. 2022 May 27;7(22):18699-18713. doi: [10.1021/acsomega.2c01404](https://doi.org/10.1021/acsomega.2c01404). PMID: [35694522](https://pubmed.ncbi.nlm.nih.gov/35694522/); PMCID: [PMC9178760](https://pmc.ncbi.nlm.nih.gov/articles/PMC9178760/).
5. <a id="ref-genheden2020"></a>Genheden S, Thakkar A, Chadimová V, Reymond JL, Engkvist O, Bjerrum E. "AiZynthFinder: a fast, robust and flexible open-source software for retrosynthetic planning." _J Cheminform_. 2020 Nov 17;12(1):70. doi: [10.1186/s13321-020-00472-1](https://doi.org/10.1186/s13321-020-00472-1). PMID: [33292482](https://pubmed.ncbi.nlm.nih.gov/33292482/); PMCID: [PMC7672904](https://pmc.ncbi.nlm.nih.gov/articles/PMC7672904/).
6. <a id="ref-anthropic-fable-mythos2026"></a>Anthropic. "Claude Fable 5 and Claude Mythos 5." _Anthropic_. 2026 Jun 9; updated 2026 Jun 12. Accessed 2026 Jun 26. [https://www.anthropic.com/news/claude-fable-5-mythos-5](https://www.anthropic.com/news/claude-fable-5-mythos-5).
7. <a id="ref-openai-safety-bug-bounty2026"></a>OpenAI. "Introducing the OpenAI Safety Bug Bounty program." _OpenAI_. 2026 Mar 25. Accessed 2026 Jun 26. [https://openai.com/index/safety-bug-bounty/](https://openai.com/index/safety-bug-bounty/).
