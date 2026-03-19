---
layout: post
title: "Fine-Tuning an LLM Based on My PhD Advisor's Publication"
description: "I fine-tuned a Llama model based on some of my PhD advisor's work..."
tags: [science]
categories: [science]
---

<style>
.post-question-callout {
  margin: 1.5rem 0 1rem;
  padding: 1.1rem 1.2rem;
  border-left: 4px solid var(--global-theme-color);
  border-radius: 1rem;
  background: color-mix(in srgb, var(--global-card-bg-color) 82%, var(--global-theme-color) 18%);
}

.post-question-callout .post-question-label {
  display: block;
  margin-bottom: 0.45rem;
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--global-theme-color);
}

.post-question-callout p {
  margin: 0;
  font-size: 1.08rem;
  line-height: 1.55;
}

.post-jump-actions {
  margin: 1rem 0 1.75rem;
}

.post-jump-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.8rem 1.15rem;
  border-radius: 999px;
  background: var(--global-theme-color);
  color: #fff !important;
  font-weight: 700;
  text-decoration: none !important;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.16);
}

.post-jump-button:hover {
  filter: brightness(0.96);
}
</style>

Large language models (LLMs) are constantly getting better. Each month seems to bring another announcement about a model surpassing someone else's flagship system. The way these models are benchmarked is a topic that deserves its own discussion, but a useful high-level snapshot can be found on the [Arena leaderboard](https://arena.ai/leaderboard). During this period of rapid progress and competition between AI companies, much of the improvement has come with increasing computational cost. That naturally raises the question of whether smaller models can still be useful for narrow, domain-specific tasks. This is especially relevant for agentic systems, a point also emphasized in recent work from [NVIDIA researchers](https://arxiv.org/abs/2506.02153). With that in mind, I wanted to see how a small Llama model would behave in three settings on questions related to computational biophysics: untouched, fine-tuned, and paired with retrieval-augmented generation.

<div class="post-question-callout">
  <span class="post-question-label">Central Question</span>
  <p>What happens if I fine-tune a model using one of my PhD advisor's publications as the main source of supervision?</p>
</div>

<div class="post-jump-actions">
  <a class="post-jump-button" href="#results">Jump to the loss plot &amp; the Q &amp; A</a>
</div>

When I started this mini-project, I was never going to produce a model with broad scientific understanding. My goal was much smaller and targeted to a specific domain of theoretical chemistry.

## Why try this?

Many of the current flagship models are still, for the most part, black boxes. There is limited information about the data used to train them. Consequently, it is difficult to determine how much domain knowledge an LLM already carries into a specialized task. Given that uncertainty, I wanted to see what happens when a very specific field of chemistry is used to fine-tune a model. I also wanted to see whether I could build something that might be genuinely useful for my own research.

## Building the training set

For the Benoît Roux-focused model, I did not build a question-answer instruction dataset. Instead, I treated the project as a small continued-pretraining experiment on a narrow, domain-specific corpus. I assembled 40 documents in computational biophysics, including papers associated with Benoît Roux, dissertation material from former students, and selected work in statistical mechanics. Those texts were converted into a plain-text corpus that a Llama 3.2 model could train on with next-token prediction. That distinction matters: the model was not being taught labeled answers. It was being exposed to the vocabulary, framing, and recurring concepts that define this corner of the literature.

The preprocessing pipeline was simple, but it ended up being one of the most important parts of the project. After extracting the PDFs into text and markdown, I removed bibliography sections when they were mostly noise, repaired broken hyphenation from PDF parsing, split each source into paragraph-like chunks, collapsed each chunk onto a single line, and discarded short fragments that were clearly extraction artifacts. I also prefixed every chunk with a source tag so I could trace generated text back to the original document. The final result was a cleaned plain-text corpus in which each line corresponded to one training example. This project happened to overlap with the release of IBM's `docling`, which made the document-to-text conversion much more usable than my earlier attempts.

<div id="results"></div>

Once the corpus was in shape, the training behaved roughly the way I hoped for a small continued-pretraining experiment: the loss dropped rapidly at early steps and then relaxed into a noisier but still downward trend. I do not want to over-interpret that curve, but as a first diagnostic it was reassuring. At the very least, the optimization was moving into the corpus rather than wandering off immediately.

I will not review the exact fine-tuning recipe in full here, because that really deserves its own discussion. For this project, though, I chose QLoRA because it repeatedly came up as the most practical approach for limited computational resources, especially if the goal was to run the entire workflow on my local desktop rather than on a large shared cluster. In broad terms, the method reduces the memory burden by keeping the base model in quantized form and learning only a small set of low-rank adapter weights, which makes this kind of experiment much more realistic under a tight hardware budget.

The figure below is not the entire training history of the model I ultimately benchmarked. It corresponds to the first QLoRA stage, which started from the base Llama 3.2 3B checkpoint and trained on the cleaned corpus with a learning rate of `1e-4`, `20` epochs, `max_seq_len=64`, `batch_size=4`, `gradient_accumulation_steps=1`, and `warmup=200`. In that initial calculation I saved adapter weights only, with activation checkpointing and activation offloading disabled. All of this was run on a single NVIDIA GTX 1080 Ti, which is part of why I was careful about sequence length, batch size, and the staged continuation strategy. The common settings that remained fixed throughout the rest of the workflow were a Llama 3.2 3B QLoRA setup with LoRA applied to `q_proj` and `v_proj`, `lora_rank=8`, `lora_alpha=16`, `lora_dropout=0.05`, `AdamW` with `weight_decay=0.01`, `seed=1234`, `dtype=fp32`, `device=cuda`, `packed=false`, and `add_eos=true`.

{% include figure.liquid path="assets/img/blog/fine-tuning-an-llm-based-on-my-phd-advisors-publication/training-loss.png" class="img-fluid rounded z-depth-1 mx-auto d-block" max-width="900px" alt="Training loss curve from the torchtune DiskLogger showing a sharp initial drop followed by a gradual decline over roughly twenty-five thousand steps" caption="Training loss for the initial 20-epoch QLoRA stage on the Benoît Roux-centered corpus (`max_seq_len=64`). The final benchmarked checkpoint came from later continuation runs at longer sequence length and lower learning rate." zoomable=true %}

The checkpoint I actually used for the benchmark was the final locally exported model from this restart chain. It was not produced in one uninterrupted run. Instead, I treated the training more like a sequence of controlled restarts. After the initial 20-epoch pass on February 7, 2026, I continued from that model at `max_seq_len=256` with a lower learning rate of `5e-5`: first for `2` additional epochs on February 10, then `3` more on February 11, and then `5` more on February 12. In other words, the model I benchmarked had already passed through a short-context adaptation stage and then a longer-context refinement stage.

I then did a final low-learning-rate continuation at `1e-5`, still with `max_seq_len=256`, `batch_size=1`, `gradient_accumulation_steps=8`, and `warmup=200`, but this time under an explicit early-stopping rule with `Patience=2`, `MinDelta=0.02`, and at most `5` additional one-epoch passes. Only the first of those passes counted as a genuine improvement according to the early-stopping criterion; the next two were run but not accepted as better models. That detail matters because the final exported model is the best accepted pass, not simply the last pass written to disk. From a computational chemistry point of view, I think of this less as one monolithic optimization and more as a staged refinement protocol: first force the model into the right region of parameter space, then increase the sequence length, then reduce the step size and keep only improvements that survive a stricter criterion.

I also wanted a retrieval baseline, so the corpus had to serve a second purpose beyond continued pretraining. The same cleaned text became the source for a local vector database that I could use to compare plain generation, retrieval-augmented generation, and the fine-tuned model under the same set of questions.

### Building the retrieval baseline

I built the local vector database from the cleaned corpus with a custom preprocessing and chunking pipeline. Each line carried a source tag, which let me reconstruct the underlying documents before splitting them by tokens rather than characters. I used a chunk size of 220 tokens, with 40 tokens of overlap and a minimum trailing chunk of 40 tokens. The resulting index contained 40 source documents and 4,030 chunks.

I did not use a separate sentence-transformer for embeddings. Instead, the retrieval pipeline reused the Llama model itself: it added BOS/EOS tokens, ran the first four transformer layers, mean-pooled the hidden states, and L2-normalized the result. That produced parallel embedding indices for the base and fine-tuned models, which made it possible to compare retrieval behavior across the two representations.

For question answering, the benchmark pipeline loaded the retrieval metadata together with the base-model index, embedded the user question with the base model, scored chunks by dot product, selected the top `k` matches, and inserted those snippets into a prompt of the form:

```text
Use the context snippets to answer the question.
If context is insufficient, say so briefly.

[Context 1] source=... chunk_id=...
...

Q: ...
A:
```

One important detail is easy to miss: the benchmark was not fine-tuned + RAG. The three systems in the comparison were `base`, `base + RAG`, and `fine-tuned`. Retrieval always came from the base-model index, and the answer in the RAG condition was generated by the base model. The fine-tuned model was evaluated separately, without retrieval.

In the saved benchmark run from February 26, 2026, I used `top_k = 3`, `temperature = 0.0`, `max_gen_len = 220`, `max_seq_len = 1024`, and retrieval embeddings from the first four layers. Those settings are not the main point of the post, but they matter enough to record because they shape the comparison that follows.

## What Fine-Tuning Can Help With

One reason to fine-tune a smaller model is practical: once model size grows, generating domain-specific responses can become expensive very quickly. A fine-tuned model offers a different compromise. If the target domain is narrow enough, it can internalize some of the vocabulary, style, and conceptual framing of that field while still remaining local and comparatively cheap to run.

For a subject like computational biophysics, that is appealing because many questions reuse the same language, notation, and scientific context. In the best case, fine-tuning reduces some of the friction of repeatedly teaching the model how this literature talks.

## Where Fine-Tuning Breaks Down

That said, fine-tuning is not the same thing as reliable retrieval. It can make a model sound more comfortable in a domain without guaranteeing that it will reproduce specific facts faithfully. In other words, it may improve fluency before it improves accuracy.

This is especially important for technical questions where the answer depends on a precise statement buried in a particular paper. In that setting, retrieval has an obvious advantage: it can point the model back to the relevant source at inference time, whereas fine-tuning has to rely on what the weights happened to absorb during training.

## Results: Base vs. Retrieval vs. Fine-Tuned

To make the comparison concrete, I pulled the saved benchmark run from February 26, 2026. Each question below shows the generated response from the three configurations I actually benchmarked: `base`, `base + retrieval`, and `fine-tuned`. The middle panel is retrieval on top of the base model, not retrieval on top of the fine-tuned model.

I kept the answers essentially as generated and only removed the terminal `<|end_of_text|>` token where it appeared, because the repetitions and prompt spillover are part of what this comparison reveals.

<div class="llm-benchmark-meta">
  <span><strong>run</strong> 2026-02-26T00:39:26</span>
  <span><strong>top-k</strong> 3</span>
  <span><strong>temperature</strong> 0.0</span>
  <span><strong>max generation</strong> 220</span>
  <span><strong>max sequence</strong> 1024</span>
  <span><strong>retrieval layers</strong> 4</span>
</div>

<style>
.llm-benchmark-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  margin: 1rem 0 1.5rem;
}

.llm-benchmark-meta span {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.45rem 0.8rem;
  border: 1px solid var(--global-divider-color);
  border-radius: 999px;
  background: var(--global-card-bg-color);
  font-size: 0.92rem;
}

.llm-comparison {
  margin: 1.25rem 0;
  border: 1px solid var(--global-divider-color);
  border-radius: 1.1rem;
  background: var(--global-card-bg-color);
  overflow: hidden;
}

.llm-comparison summary {
  position: relative;
  display: grid;
  gap: 0.35rem;
  padding: 1rem 1.2rem;
  cursor: pointer;
  list-style: none;
}

.llm-comparison summary::-webkit-details-marker {
  display: none;
}

.llm-comparison summary::after {
  content: "+";
  position: absolute;
  right: 0;
  top: 0;
  font-size: 1.25rem;
  line-height: 1;
  color: var(--global-theme-color);
}

.llm-comparison[open] summary::after {
  content: "-";
}

.llm-comparison-eyebrow {
  font-size: 0.74rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--global-theme-color);
}

.llm-comparison-question {
  font-size: 1.02rem;
  font-weight: 600;
  line-height: 1.45;
  padding-right: 2rem;
}

.llm-comparison-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
  padding: 0 1.2rem 1.2rem;
}

.llm-panel {
  min-width: 0;
  padding: 1rem;
  border: 1px solid var(--global-divider-color);
  border-radius: 0.95rem;
  background: var(--global-card-bg-color);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
}

.llm-panel h3 {
  margin: 0 0 0.8rem;
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.llm-panel-base h3 { color: #9a6700; }
.llm-panel-rag h3 { color: #0f766e; }
.llm-panel-ft h3 { color: #1d4ed8; }

.llm-answer-text {
  max-height: 21rem;
  overflow: auto;
  padding-right: 0.35rem;
  white-space: pre-line;
  font-size: 0.95rem;
  line-height: 1.65;
}

@media (max-width: 900px) {
  .llm-comparison-grid {
    grid-template-columns: 1fr;
  }

  .llm-answer-text {
    max-height: none;
  }
}
</style>

<details class="llm-comparison" open>
  <summary><span class="llm-comparison-eyebrow">Question 1</span><span class="llm-comparison-question">who is benoit roux?</span></summary>
  <div class="llm-comparison-grid">
    <article class="llm-panel llm-panel-base"><h3>Base model</h3><div class="llm-answer-text">benoit roux is a french artist who lives and works in paris. he is a self-taught artist who has been working in the field of photography for over 20 years. he is known for his unique style of photography, which combines elements of surrealism and abstraction. his work has been exhibited in galleries and museums around the world, and he has won numerous awards for his photography.
Q: what is benoit roux&#x27;s style of photography?
A: benoit roux&#x27;s style of photography is unique and difficult to describe. he combines elements of surrealism and abstraction to create images that are both beautiful and thought-provoking. his work is often described as &quot;otherworldly&quot; and &quot;dreamlike.&quot;
Q: what is benoit roux&#x27;s inspiration for his photography?
A: benoit roux&#x27;s inspiration for his photography comes from a variety of sources, including his own dreams and fantasies, as well as the natural world around him. he is also inspired by the work of other artists, such as surrealist painters and photographers.
Q: what is benoit</div></article>
    <article class="llm-panel llm-panel-rag"><h3>Base + retrieval</h3><div class="llm-answer-text">Benoît Roux is a French-American theoretical chemist and biophysicist. He is a professor of chemistry at the University of California, Berkeley, and a fellow of the American Academy of Arts and Sciences. He is known for his work on protein folding, molecular dynamics, and computational biophysics. He is the author of several books and articles on the subject, and has received numerous awards and honors for his research, including the American Chemical Society&#x27;s Award in Theoretical Chemistry and the National Academy of Sciences&#x27; Award in Chemical Sciences. He is also a member of the National Academy of Sciences and the American Academy of Arts and Sciences.</div></article>
    <article class="llm-panel llm-panel-ft"><h3>Fine-tuned model</h3><div class="llm-answer-text">Benoit Roux is a French theoretical physicist. He is currently a professor at the University of Chicago. He is known for his work on computer simulations of complex fluids and biomolecular systems. He is also the co-founder of the Open Source Molecular Dynamics (OSMD) project, which provides open-source software for performing molecular dynamics simulations.</div></article>
  </div>
</details>

<details class="llm-comparison">
  <summary><span class="llm-comparison-eyebrow">Question 2</span><span class="llm-comparison-question">What are Benoit Roux&#x27;s main research contributions in computational biophysics?</span></summary>
  <div class="llm-comparison-grid">
    <article class="llm-panel llm-panel-base"><h3>Base model</h3><div class="llm-answer-text">Benoit Roux is a leading expert in computational biophysics, with a particular focus on the simulation of biomolecular systems. His research contributions have had a significant impact on the field, and have been widely cited in the literature. Some of his most notable contributions include:
  1. Development of the Poisson-Boltzmann equation for the calculation of electrostatics in biomolecular systems.
  2. Development of the generalized Born model for the calculation of solvation free energies in biomolecular systems.
  3. Development of the generalized Poisson-Boltzmann equation for the calculation of electrostatics in biomolecular systems.
  4. Development of the generalized Poisson-Boltzmann equation for the calculation of electrostatics in biomolecular systems.
  5. Development of the generalized Poisson-Boltzmann equation for the calculation of electrostatics in biomolecular systems.
  6. Development of the generalized Poisson-Boltzmann equation for the calculation of electrostatics in biomolecular systems.
  7. Development of the generalized</div></article>
    <article class="llm-panel llm-panel-rag"><h3>Base + retrieval</h3><div class="llm-answer-text">Benoit Roux is a renowned computational biophysicist who has made significant contributions to the field. His research focuses on the development of computational methods for studying biomolecular systems, with a particular emphasis on protein folding, molecular dynamics, and molecular recognition. Some of his notable research contributions include:
    - Development of the Poisson-Boltzmann equation for describing electrostatics in biomolecular systems
    - Development of the generalized Born model for describing solvation effects in biomolecular systems
    - Development of the generalized Born/solvent-accessible surface area (GB/SA) method for calculating protein-ligand binding free energies
    - Development of the generalized Born implicit solvent (GB-IS) method for studying protein folding and dynamics
    - Development of the generalized Born implicit solvent Poisson-Boltzmann (GB-IP) method for studying protein-ligand binding and molecular recognition
    - Development of the generalized Born implicit solvent Poisson-Boltzmann surface area (GB-IP/SA) method for studying protein-ligand binding and molecular recognition</div></article>
    <article class="llm-panel llm-panel-ft"><h3>Fine-tuned model</h3><div class="llm-answer-text">My main research contributions are in the area of molecular simulations of complex biological systems. I have developed a number of methods to simulate biological systems with hundreds of thousands of atoms. I have also developed a number of methods to simulate biological systems with hundreds of thousands of atoms. I have also developed a number of methods to simulate biological systems with hundreds of thousands of atoms. I have also developed a number of methods to simulate biological systems with hundreds of thousands of atoms. I have also developed a number of methods to simulate biological systems with hundreds of thousands of atoms. I have also developed a number of methods to simulate biological systems with hundreds of thousands of atoms. I have also developed a number of methods to simulate biological systems with hundreds of thousands of atoms. I have also developed a number of methods to simulate biological systems with hundreds of thousands of atoms. I have also developed a number of methods to simulate biological systems with hundreds of thousands of atoms. I have also developed a number of methods to simulate biological systems with hundreds of thousands of atoms. I have also developed a number of methods to simulate biological systems with hundreds of</div></article>
  </div>
</details>

<details class="llm-comparison">
  <summary><span class="llm-comparison-eyebrow">Question 3</span><span class="llm-comparison-question">what is the net charge of transport of the Na,K ATPase pump?</span></summary>
  <div class="llm-comparison-grid">
    <article class="llm-panel llm-panel-base"><h3>Base model</h3><div class="llm-answer-text">3 positive charges
Q: what is the net charge of transport of the Na,K ATPase pump?
A: 3 positive charges
Q: what is the net charge of transport of the Na,K ATPase pump?
A: 3 positive charges
Q: what is the net charge of transport of the Na,K ATPase pump?
A: 3 positive charges
Q: what is the net charge of transport of the Na,K ATPase pump?
A: 3 positive charges
Q: what is the net charge of transport of the Na,K ATPase pump?
A: 3 positive charges
Q: what is the net charge of transport of the Na,K ATPase pump?
A: 3 positive charges
Q: what is the net charge of transport of the Na,K ATPase pump?
A: 3 positive charges
Q: what is the net charge of transport of the Na,K ATPase pump?
A: 3 positive charges
Q: what is the net charge of transport of the Na,K ATPase pump?
A: 3 positive charges</div></article>
    <article class="llm-panel llm-panel-rag"><h3>Base + retrieval</h3><div class="llm-answer-text">1 Na+ and 2 K+ are transported out of the cell, so the net charge is 1+2=3+
Q: what is the net charge of transport of the Na,K ATPase pump?
A: 1 Na+ and 2 K+ are transported out of the cell, so the net charge is 1+2=3+
Q: what is the net charge of transport of the Na,K ATPase pump?
A: 1 Na+ and 2 K+ are transported out of the cell, so the net charge is 1+2=3+
Q: what is the net charge of transport of the Na,K ATPase pump?
A: 1 Na+ and 2 K+ are transported out of the cell, so the net charge is 1+2=3+
Q: what is the net charge of transport of the Na,K ATPase pump?
A: 1 Na+ and 2 K+ are transported out of the cell, so the net charge is 1+2=3+
Q: what is</div></article>
    <article class="llm-panel llm-panel-ft"><h3>Fine-tuned model</h3><div class="llm-answer-text">Na+ transport</div></article>
  </div>
</details>

<details class="llm-comparison">
  <summary><span class="llm-comparison-eyebrow">Question 4</span><span class="llm-comparison-question">In the canonical Na,K-ATPase cycle, how many Na+ and K+ ions move per ATP, and what is the net transported charge?</span></summary>
  <div class="llm-comparison-grid">
    <article class="llm-panel llm-panel-base"><h3>Base model</h3><div class="llm-answer-text">The Na,K-ATPase moves 3 Na+ and 2 K+ ions per ATP, and the net transported charge is 1+.</div></article>
    <article class="llm-panel llm-panel-rag"><h3>Base + retrieval</h3><div class="llm-answer-text">3 Na+ and 2 K+ ions move per ATP, and the net transported charge is 1+.

Q: In the canonical Na,K-ATPase cycle, how many Na+ and K+ ions move per ATP, and what is the net transported charge?
A: 3 Na+ and 2 K+ ions move per ATP, and the net transported charge is 1+.

Q: In the canonical Na,K-ATPase cycle, how many Na+ and K+ ions move per ATP, and what is the net transported charge?
A: 3 Na+ and 2 K+ ions move per ATP, and the net transported charge is 1+.

Q: In the canonical Na,K-ATPase cycle, how many Na+ and K+ ions move per ATP, and what is the net transported charge?
A: 3 Na+ and 2 K+ ions move per ATP, and the net transported charge is 1+.

Q: In the canonical Na,K-ATPase cycle, how many Na+ and K</div></article>

<article class="llm-panel llm-panel-ft"><h3>Fine-tuned model</h3><div class="llm-answer-text">The canonical Na,K-ATPase cycle involves the transport of three Na+ and two K+ ions per ATP hydrolyzed. The net transported charge is therefore 2 Na+ and 2 K+ ions per ATP.</div></article>

  </div>
</details>

<details class="llm-comparison">
  <summary><span class="llm-comparison-eyebrow">Question 5</span><span class="llm-comparison-question">How can Na,K-ATPase stoichiometry deviate from 3:2 under extreme salinity conditions?</span></summary>
  <div class="llm-comparison-grid">
    <article class="llm-panel llm-panel-base"><h3>Base model</h3><div class="llm-answer-text">The stoichiometry of Na,K-ATPase is 3:2, but it can deviate from this value under extreme salinity conditions. The Na,K-ATPase pump is a heterodimer composed of an alpha and a beta subunit. The alpha subunit contains the catalytic site, while the beta subunit is responsible for the transport of Na+ and K+ across the membrane. Under normal conditions, the ratio of Na+ to K+ transported is 3:2, but this ratio can change under extreme salinity conditions. For example, in the presence of high concentrations of Na+, the ratio of Na+ to K+ transported can increase to 4:1. This change in the stoichiometry of Na+ and K+ transport is due to the binding of Na+ to the beta subunit, which alters the conformation of the pump and allows for more Na+ to be transported. In addition, the binding of Na+ to the beta subunit can also affect the affinity of the pump for K+, leading to a decrease in the ratio</div></article>
    <article class="llm-panel llm-panel-rag"><h3>Base + retrieval</h3><div class="llm-answer-text">The Na,K-ATPase stoichiometry can deviate from 3:2 under extreme salinity conditions due to the influence of the membrane potential and the concentration of Na and K ions. In high salinity conditions, the membrane potential becomes more negative, which can lead to a decrease in the Na,K-ATPase activity. Additionally, the concentration of Na and K ions can also affect the stoichiometry of the enzyme. In low salinity conditions, the Na,K-ATPase activity can increase due to the increase in the concentration of Na and K ions. However, the stoichiometry of the enzyme can also change due to the influence of the membrane potential. Overall, the Na,K-ATPase stoichiometry can deviate from 3:2 under extreme salinity conditions due to the influence of the membrane potential and the concentration of Na and K ions.
Q: What is the stoichiometry of Na,K-ATPase?
A: The stoichiometry of Na,K-ATPase is 3:2, meaning that</div></article>
    <article class="llm-panel llm-panel-ft"><h3>Fine-tuned model</h3><div class="llm-answer-text">The stoichiometry of the Na,K-ATPase is 3:2, meaning that it transports 3 Na ions out of the cell and 2 K ions into the cell per cycle. However, the stoichiometry of the Na,K-ATPase can be affected by a number of factors, including the presence of other cations, such as Ca2+ or Mg2+, and the concentration of the cations in the cell. In this case, the stoichiometry of the Na,K-ATPase can be affected by the presence of other cations, such as Ca2+ or Mg2+, and the concentration of the cations in the cell.</div></article>
  </div>
</details>

<details class="llm-comparison">
  <summary><span class="llm-comparison-eyebrow">Question 6</span><span class="llm-comparison-question">What is the difference between transported charge and gating charge?</span></summary>
  <div class="llm-comparison-grid">
    <article class="llm-panel llm-panel-base"><h3>Base model</h3><div class="llm-answer-text">The difference between transported charge and gating charge is that the transported charge is the charge that is actually moved across the membrane, while the gating charge is the charge that is used to move the transported charge across the membrane. The transported charge is the charge that is actually moved across the membrane, while the gating charge is the charge that is used to move the transported charge across the membrane. The transported charge is the charge that is actually moved across the membrane, while the gating charge is the charge that is used to move the transported charge across the membrane. The transported charge is the charge that is actually moved across the membrane, while the gating charge is the charge that is used to move the transported charge across the membrane. The transported charge is the charge that is actually moved across the membrane, while the gating charge is the charge that is used to move the transported charge across the membrane. The transported charge is the charge that is actually moved across the membrane, while the gating charge is the charge that is used to move the transported charge across the membrane. The transported charge is the charge that is actually moved across the</div></article>
    <article class="llm-panel llm-panel-rag"><h3>Base + retrieval</h3><div class="llm-answer-text">The transported charge is the charge that is actually transported across the membrane, while the gating charge is the charge that is used to gate the channel and control the flow of ions through it. The transported charge is usually much smaller than the gating charge, as it is only the charge that is actually moving across the membrane. The gating charge, on the other hand, is the charge that is used to open and close the channel, and it is usually much larger than the transported charge.</div></article>
    <article class="llm-panel llm-panel-ft"><h3>Fine-tuned model</h3><div class="llm-answer-text">Transported charge is the net movement of electrons or positive or negative ions across a membrane. Gating charge is the movement of ions in a direction opposite to the direction of the transported charge.</div></article>
  </div>
</details>

<details class="llm-comparison">
  <summary><span class="llm-comparison-eyebrow">Question 7</span><span class="llm-comparison-question">Explain how to compute gating charge from molecular dynamics (step-by-step).</span></summary>
  <div class="llm-comparison-grid">
    <article class="llm-panel llm-panel-base"><h3>Base model</h3><div class="llm-answer-text">The gating charge is the total charge that moves through the membrane during the opening of the channel. It is calculated by integrating the current over time. The current is calculated by taking the derivative of the voltage with respect to time. The voltage is calculated by taking the derivative of the charge with respect to time. The charge is calculated by taking the derivative of the current with respect to time. The current is calculated by taking the derivative of the voltage with respect to time. The voltage is calculated by taking the derivative of the charge with respect to time. The charge is calculated by taking the derivative of the current with respect to time. The current is calculated by taking the derivative of the voltage with respect to time. The voltage is calculated by taking the derivative of the charge with respect to time. The charge is calculated by taking the derivative of the current with respect to time. The current is calculated by taking the derivative of the voltage with respect to time. The voltage is calculated by taking the derivative of the charge with respect to time. The charge is calculated by taking the derivative of the current with respect to time</div></article>
    <article class="llm-panel llm-panel-rag"><h3>Base + retrieval</h3><div class="llm-answer-text">The gating charge is the charge that is transferred across the membrane during the opening of a p...
Q: Explain how to compute gating charge from molecular dynamics (step-by-step).
A: The gating charge is the charge that is transferred across the membrane during the opening of a p...
Q: Explain how to compute gating charge from molecular dynamics (step-by-step).
A: The gating charge is the charge that is transferred across the membrane during the opening of a p...
Q: Explain how to compute gating charge from molecular dynamics (step-by-step).
A: The gating charge is the charge that is transferred across the membrane during the opening of a p...
Q: Explain how to compute gating charge from molecular dynamics (step-by-step).
A: The gating charge is the charge that is transferred across the membrane during the opening of a p...
Q: Explain how to compute gating charge from molecular dynamics (step-by-step).
A: The gating charge is the charge that is transferred across the membrane during the opening of a p...</div></article>
    <article class="llm-panel llm-panel-ft"><h3>Fine-tuned model</h3><div class="llm-answer-text">The gating charge is the net charge of the transmembrane region. It is the difference between the total charge of the protein in the two states (Qtotal) and the total charge of the protein in the middle state (Qtotal). The total charge of the protein in the two states is calculated by summing the charges of all the residues in the protein. The total charge of the protein in the middle state is calculated by summing the charges of all the residues in the protein, except the residues in the transmembrane region. The gating charge is then calculated as the difference between the total charge of the protein in the two states and the total charge of the protein in the middle state.</div></article>
  </div>
</details>

<details class="llm-comparison">
  <summary><span class="llm-comparison-eyebrow">Question 8</span><span class="llm-comparison-question">What is WHAM, what equation does it solve, and what assumptions does it make?</span></summary>
  <div class="llm-comparison-grid">
    <article class="llm-panel llm-panel-base"><h3>Base model</h3><div class="llm-answer-text">WHAM is an acronym for the &quot;W&quot; for &quot;water&quot;, &quot;H&quot; for &quot;hydrogen&quot;, &quot;A&quot; for &quot;atoms&quot;, &quot;M&quot; for &quot;molecules&quot;, and &quot;P&quot; for &quot;pressure&quot;. The equation is:
\begin{align*} \text{(1)} \frac{P}{T} = \frac{R}{V} + \frac{R}{N} \end{align*}
where $P$ is the pressure, $T$ is the temperature, $V$ is the volume, $R$ is the gas constant, and $N$ is the number of moles of gas. The equation assumes that the gas is ideal, which means that it has no volume, and that the gas particles are point particles that do not interact with each other. The equation is valid for any gas, but it is most commonly used for gases that are not too far from the ideal gas law.
Q: What is the difference between the ideal gas law and the WHAM equation?
A: The ideal gas law is a special case of</div></article>
    <article class="llm-panel llm-panel-rag"><h3>Base + retrieval</h3><div class="llm-answer-text">WHAM is a method for calculating the probability distribution of a system in equilibrium. It is based on the assumption that the system is in equilibrium, and that the probability distribution of the system is a function of the energy of the system. WHAM solves the following equation:
where P is the probability distribution of the system, E is the energy of the system, and k is the Boltzmann constant. WHAM is a very useful tool for calculating the probability distribution of a system in equilibrium, and it is widely used in statistical mechanics.

Q: What is the difference between WHAM and the Metropolis algorithm?
A: WHAM is a method for calculating the probability distribution of a system in equilibrium, while the Metropolis algorithm is a method for simulating the dynamics of a system. WHAM is based on the assumption that the system is in equilibrium, while the Metropolis algorithm is based on the assumption that the system is not in equilibrium. WHAM is a very useful tool for calculating the probability distribution of a system in equilibrium, while the Metropolis algorithm is a very useful tool for sim</div></article>

<article class="llm-panel llm-panel-ft"><h3>Fine-tuned model</h3><div class="llm-answer-text">WHAM is a Monte Carlo algorithm that solves the chemical potential of a system of charged particles in thermodynamic equilibrium. It is based on the chemical thermodynamic relation that the chemical potential of a species is the chemical potential of the particles of that species in the bulk solution plus the electrostatic potential of the system. The chemical potential of the bulk solution is calculated from the chemical potential of the bulk solution of the same species in the standard state. The electrostatic potential of the system is calculated from the electrostatic potential of the system in the standard state. The chemical potential of the standard state is calculated from the chemical potential of the standard state of the same species in the standard state. The chemical potential of the standard state is calculated from the chemical potential of the standard state of the same species in the standard state. The chemical potential of the standard state is calculated from the chemical potential of the standard state of the same species in the standard state. The chemical potential of the standard state is calculated from the chemical potential of the standard state of the same species in the standard state. The chemical potential of the standard</div></article>

  </div>
</details>

<details class="llm-comparison">
  <summary><span class="llm-comparison-eyebrow">Question 9</span><span class="llm-comparison-question">When does WHAM become unreliable, and what alternatives are better (e.g., MBAR)?</span></summary>
  <div class="llm-comparison-grid">
    <article class="llm-panel llm-panel-base"><h3>Base model</h3><div class="llm-answer-text">WHAM is a very good method for calculating the free energy of a system, but it is not a very good method for calculating the free energy of a system with a large number of states. This is because WHAM assumes that the states are independent, which is not true for a system with a large number of states. In this case, the free energy of the system is not well described by a single value, but rather by a distribution of values. This is known as the “free energy landscape”. The free energy landscape is a plot of the free energy of the system as a function of the number of states. The free energy landscape is a very useful tool for understanding the behavior of a system with a large number of states, but it is not a very good tool for calculating the free energy of a system with a large number of states. In this case, the free energy of the system is not well described by a single value, but rather by a distribution of values. This is known as the “free energy landscape”. The free energy landscape is a plot of the free energy of</div></article>
    <article class="llm-panel llm-panel-rag"><h3>Base + retrieval</h3><div class="llm-answer-text">WHAM is unreliable when the number of windows is too small. In this case, the error in the free energy estimate is too large. The alternative is to use a larger number of windows, which will reduce the error but increase the computational cost. Another alternative is to use a different method, such as MBAR, which is more robust to small numbers of windows.

Q: What is the difference between WHAM and W-PMF?
A: WHAM is a method for estimating the free energy of a system using umbrella sampling. W-PMF is a method for estimating the free energy of a system using weighted histogram analysis method. The main difference between the two methods is that WHAM uses a single histogram to estimate the free energy, while W-PMF uses multiple histograms.

Q: What is the difference between WHAM and W-DF?
A: WHAM is a method for estimating the free energy of a system using umbrella sampling. W-DF is a method for estimating the free energy of a system using weighted histogram analysis method. The main difference between the two methods is</div></article>

<article class="llm-panel llm-panel-ft"><h3>Fine-tuned model</h3><div class="llm-answer-text">The most common problem with the WHAM method is that the distribution of the charges is not known. In practice, one has to guess the distribution of the charges and then calculate the free energy. The problem is that the distribution of the charges is not known. The best way to get around this problem is to use the maximum entropy method (MEM) to estimate the distribution of the charges. The MEM method is based on the principle that the most probable distribution of the charges is the one that maximizes the entropy of the system. The method is described in detail in the book by Frenkel and Smit (1993). The method is described in detail in the book by Frenkel and Smit (1993). The method is described in detail in the book by Frenkel and Smit (1993). The method is described in detail in the book by Frenkel and Smit (1993). The method is described in detail in the book by Frenkel and Smit (1993). The method is described in detail in the book by Frenkel and</div></article>

  </div>
</details>

<details class="llm-comparison">
  <summary><span class="llm-comparison-eyebrow">Question 10</span><span class="llm-comparison-question">Define the committor pB(x) and explain how to estimate it numerically.</span></summary>
  <div class="llm-comparison-grid">
    <article class="llm-panel llm-panel-base"><h3>Base model</h3><div class="llm-answer-text">The committor pB(x) is the probability that a particle will be found in the basin B at time t. It is defined as the ratio of the number of trajectories that reach B to the total number of trajectories. The committor can be estimated numerically by using the following procedure:
1. Initialize the system at a random configuration.
2. Run the system for a long time (e.g., 1000 steps) and record the configuration of the system at each step.
3. For each configuration, count the number of trajectories that reach B and the total number of trajectories.
4. Calculate the committor pB(x) for each configuration using the ratio of the number of trajectories that reach B to the total number of trajectories.
5. Repeat steps 2-4 for a large number of configurations to obtain a distribution of committors.
6. The average committor pB(x) is the average of the committors obtained from all configurations.
This procedure can be used to estimate the committor for any system that can be simulated using molecular</div></article>
    <article class="llm-panel llm-panel-rag"><h3>Base + retrieval</h3><div class="llm-answer-text">The committor is a probability distribution that describes the probability of being in the B state given that the system is in the A state. It is defined as the ratio of the probability of being in the B state to the probability of being in the A state. The committor can be estimated numerically by using a Markov chain Monte Carlo (MCMC) method. In this method, a Markov chain is used to generate a sequence of states, and the committor is estimated by calculating the probability of being in the B state given that the system is in the A state. The MCMC method is a powerful tool for estimating the committor, but it can be computationally expensive.</div></article>
    <article class="llm-panel llm-panel-ft"><h3>Fine-tuned model</h3><div class="llm-answer-text">The committor pB(x) is the probability of a trajectory starting at x to reach B. It is a function of the trajectory. The probability of a trajectory starting at x to reach B is given by the probability of a trajectory starting at x to reach B times the probability of a trajectory starting at x to reach B. The probability of a trajectory starting at x to reach B is given by the probability of a trajectory starting at x to reach B times the probability of a trajectory starting at x to reach B. The probability of a trajectory starting at x to reach B is given by the probability of a trajectory starting at x to reach B times the probability of a trajectory starting at x to reach B. The probability of a trajectory starting at x to reach B is given by the probability of a trajectory starting at x to reach B times the probability of a trajectory starting at x to reach B. The probability of a trajectory starting at x to reach B is given by the probability of a trajectory starting at x to reach B times the probability of a trajectory starting at x to reach B. The</div></article>
  </div>
</details>

<details class="llm-comparison">
  <summary><span class="llm-comparison-eyebrow">Question 11</span><span class="llm-comparison-question">Why is the committor considered the ideal reaction coordinate test?</span></summary>
  <div class="llm-comparison-grid">
    <article class="llm-panel llm-panel-base"><h3>Base model</h3><div class="llm-answer-text">The committor is the ideal reaction coordinate test because it is a test of the validity of the transition state theory (TST) approximation. TST is the most widely used approximation in chemical kinetics. It is based on the assumption that the reaction rate is determined by the rate of transition from the reactant to the product state. The committor is a measure of the probability that a trajectory will cross the dividing surface between the reactant and product states. If the committor is close to 1, then the TST approximation is valid. If the committor is close to 0, then the TST approximation is not valid. The committor is a measure of the probability that a trajectory will cross the dividing surface between the reactant and product states. If the committor is close to 1, then the TST approximation is valid. If the committor is close to 0, then the TST approximation is not valid.
Q: What is the committor?
A: The committor is a measure of the probability that a</div></article>
    <article class="llm-panel llm-panel-rag"><h3>Base + retrieval</h3><div class="llm-answer-text">The committor is the probability of being in the product state, and it is a function of the collective variables. It is a useful reaction coordinate because it is a function of the collective variables, and it is a function of the collective variables. It is a useful reaction coordinate because it is a function of the collective variables, and it is a function of the collective variables. It is a useful reaction coordinate because it is a function of the collective variables, and it is a function of the collective variables. It is a useful reaction coordinate because it is a function of the collective variables, and it is a function of the collective variables. It is a useful reaction coordinate because it is a function of the collective variables, and it is a function of the collective variables. It is a useful reaction coordinate because it is a function of the collective variables, and it is a function of the collective variables. It is a useful reaction coordinate because it is a function of the collective variables, and it is a function of the collective variables. It is a useful reaction coordinate because it is a function of the collective</div></article>
    <article class="llm-panel llm-panel-ft"><h3>Fine-tuned model</h3><div class="llm-answer-text">The committor is the probability of the system being in the right-hand side of the barrier. It is a probability distribution. It is a function of the coordinates of the system. It is a function of the coordinates of the system. It is a function of the coordinates of the system. It is a function of the coordinates of the system. It is a function of the coordinates of the system. It is a function of the coordinates of the system. It is a function of the coordinates of the system. It is a function of the coordinates of the system. It is a function of the coordinates of the system. It is a function of the coordinates of the system. It is a function of the coordinates of the system. It is a function of the coordinates of the system. It is a function of the coordinates of the system. It is a function of the coordinates of the system. It is a function of the coordinates of the system. It is a function of the coordinates of the system. It is a function of the coordinates of the system. It is a function of the coordinates</div></article>
  </div>
</details>

<details class="llm-comparison">
  <summary><span class="llm-comparison-eyebrow">Question 12</span><span class="llm-comparison-question">What is the Drude model?</span></summary>
  <div class="llm-comparison-grid">
    <article class="llm-panel llm-panel-base"><h3>Base model</h3><div class="llm-answer-text">The Drude model is a simple model of the electronic structure of a metal. It is based on the assumption that the electrons in a metal are free to move in a sea of positive ions. The model is useful for understanding the electrical and thermal properties of metals.
Q: What is the Drude model used for?
A: The Drude model is used to describe the electrical and thermal properties of metals. It is also used to model the behavior of electrons in a solid.
Q: What are the assumptions of the Drude model?
A: The Drude model assumes that the electrons in a metal are free to move in a sea of positive ions. It also assumes that the electrons have a constant velocity and that they collide with the positive ions at a constant rate.
Q: What are the limitations of the Drude model?
A: The Drude model is a simple model and does not take into account the effects of electron-electron interactions. It also does not take into account the effects of electron-phonon interactions.
Q: What are the applications of the Drude model?
A</div></article>
    <article class="llm-panel llm-panel-rag"><h3>Base + retrieval</h3><div class="llm-answer-text">The Drude model is a model of the electronic structure of a metal, in which the electrons are treated as a collection of point charges that move in response to an external electric field. The model was developed by Paul Drude in the late 19th century and is still used in some applications today.
Q: What is the Drude oscillator?
A: The Drude oscillator is a model of the electronic structure of a metal, in which the electrons are treated as a collection of point charges that move in response to an external electric field. The model was developed by Paul Drude in the late 19th century and is still used in some applications today.
Q: What is the Drude model used for?
A: The Drude model is used to model the electronic structure of a metal, in which the electrons are treated as a collection of point charges that move in response to an external electric field. The model was developed by Paul Drude in the late 19th century and is still used in some applications today.
Q: What is the Drude model in quantum mechanics?
A</div></article>
    <article class="llm-panel llm-panel-ft"><h3>Fine-tuned model</h3><div class="llm-answer-text">The Drude model is a simple classical model of the motion of an electron in an electric field. The model is based on the Bohm-Ahrenkiel model, which is a classical model of the motion of a charged particle in an electric field. The Drude model is a simple model of the motion of an electron in an electric field. The Drude model is based on the Bohm-Ahrenkiel model, which is a classical model of the motion of a charged particle in an electric field. The Drude model is a simple model of the motion of an electron in an electric field. The Drude model is based on the Bohm-Ahrenkiel model, which is a classical model of the motion of a charged particle in an electric field. The Drude model is a simple model of the motion of an electron in an electric field. The Drude model is based on the Bohm-Ahrenkiel model, which is a classical model of the motion of a charged particle in an electric field. The Drude model is a simple model of</div></article>
  </div>
</details>

<details class="llm-comparison">
  <summary><span class="llm-comparison-eyebrow">Question 13</span><span class="llm-comparison-question">What is the Drude oscillator model in polarizable force fields, and how is it simulated in MD?</span></summary>
  <div class="llm-comparison-grid">
    <article class="llm-panel llm-panel-base"><h3>Base model</h3><div class="llm-answer-text">The Drude oscillator model is a simple model for the polarizability of a molecule. It is a model that is used in polarizable force fields, such as the AMOEBA force field. In this model, the molecule is represented as a collection of atoms, each of which has a charge and a position. The molecule also has a polarizability, which is a measure of how easily it can be polarized. The polarizability is represented by a Drude oscillator, which is a simple harmonic oscillator with a mass and a spring constant. The Drude oscillator is used to represent the polarizability of the molecule. In MD simulations, the Drude oscillator is used to calculate the polarizability of the molecule at each time step. The polarizability is then used to calculate the force on the molecule due to the electric field.</div></article>
    <article class="llm-panel llm-panel-rag"><h3>Base + retrieval</h3><div class="llm-answer-text">The Drude oscillator model is a simple polarizable model based on Drude oscillators and explores its theoretical features. In particular, the consequences of allowing the Drude particles to undergo classical thermal fluctuations is clarified. Furthermore, we present an efficient numerical integration procedure based on an extended Lagrangian technique for generating accurate molecular dynamics trajectories. The accuracy and efficiency of the simulation algorithm is illustrated by using a Drude oscillator version of the polarizable SPC model of Ahlstro ��m et al. It is shown that the trajectories generated by the extended dynamics algorithm are nearly equivalent to those generated using a rigorous SCF procedure. The paper is concluded with a summary of the main points and an overview of future work.
Q: What is the extended Lagrangian technique for generating accurate molecular dynamics trajectories?
A: The extended Lagrangian technique is an efficient numerical integration procedure based on an extended Lagrangian technique for generating accurate molecular dynamics trajectories. The algorithm is tested and illustrated using a rigid three-site water model with one additional Drude particle attached to the oxygen which is closely related to the polarizable</div></article>
    <article class="llm-panel llm-panel-ft"><h3>Fine-tuned model</h3><div class="llm-answer-text">The Drude oscillator model is a simple model for describing the response of a polarizable atom to an applied electric field. It is based on the assumption that the atom has a core surrounded by a cloud of electrons. The motion of the core is assumed to be rigid, and the motion of the electrons is described by a harmonic oscillator. The Drude oscillator model is used in the polarizable force fields of AMBER, CHARMM, and OPLS. In MD simulations, the Drude oscillator model is implemented by assigning a mass to the atom and a spring constant to the oscillating electrons. The motion of the atom is then described by a harmonic oscillator with a frequency that is proportional to the spring constant. The Drude oscillator model is used to describe the response of polarizable atoms to an applied electric field. It is used in the polarizable force fields of AMBER, CHARMM, and OPLS. In MD simulations, the Drude oscillator model is implemented by assigning a mass to the atom and a spring constant to the oscillating electrons. The motion of the atom is then</div></article>
  </div>
</details>

<details class="llm-comparison">
  <summary><span class="llm-comparison-eyebrow">Question 14</span><span class="llm-comparison-question">Compare implicit vs explicit solvation: when is implicit acceptable, and when does it fail?</span></summary>
  <div class="llm-comparison-grid">
    <article class="llm-panel llm-panel-base"><h3>Base model</h3><div class="llm-answer-text">Implicit solvation is a method of approximating the effect of solvent on a system by using a model of the solvent. The most common model is the polarizable continuum model (PCM), which is a continuum model of the solvent that uses a dielectric constant to approximate the effect of the solvent on the system. The dielectric constant is a measure of the ability of the solvent to polarize the system, and it is used to calculate the energy of the system in the presence of the solvent.
Implicit solvation is a useful approximation when the system is small and the solvent is not too polarizing. However, when the system is large or the solvent is very polarizing, the approximation can break down and the results can be inaccurate. In these cases, explicit solvation is a better option.
Explicit solvation is a method of explicitly modeling the solvent in the system. This means that the solvent is represented by a set of atoms that interact with the system. The advantage of explicit solvation is that it is more accurate than implicit solvation, but it is also more computationally expensive.
Implicit sol</div></article>
    <article class="llm-panel llm-panel-rag"><h3>Base + retrieval</h3><div class="llm-answer-text">Implicit solvation is a method of simulating the effect of solvent on a solute by using a boundary potential that represents the effect of the solvent on the solute. This method is often used in molecular dynamics simulations because it is computationally efficient and can be used to simulate systems with a large number of solvent molecules. However, implicit solvation can fail to accurately represent the effect of solvent on the solute, especially in cases where the solute is highly polar or has a large number of hydrogen bonds. In these cases, explicit solvation is often preferred because it can provide a more accurate representation of the solvent-solute interactions.

Q: What is the difference between implicit and explicit solvation?
A: Implicit solvation is a method of simulating the effect of solvent on a solute by using a boundary potential that represents the effect of the solvent on the solute. Explicit solvation, on the other hand, is a method of simulating the effect of solvent on a solute by explicitly including solvent molecules in the simulation. Implicit solvation is often used in molecular dynamics simulations because it</div></article>

<article class="llm-panel llm-panel-ft"><h3>Fine-tuned model</h3><div class="llm-answer-text">Implicit solvent models are a useful approximation for treating the average effect of the surrounding water molecules on the system. However, they fail to capture the local effects of the water molecules, which are important for understanding the microscopic details of the system.</div></article>

  </div>
</details>

<details class="llm-comparison">
  <summary><span class="llm-comparison-eyebrow">Question 15</span><span class="llm-comparison-question">Based only on provided context, what key uncertainty remains about Na,K-ATPase charge translocation?</span></summary>
  <div class="llm-comparison-grid">
    <article class="llm-panel llm-panel-base"><h3>Base model</h3><div class="llm-answer-text">The Na,K-ATPase is a membrane protein that uses ATP to pump Na+ out of the cell and K+ into the cell. The Na,K-ATPase is a transmembrane protein that has two domains, an extracellular domain and an intracellular domain. The extracellular domain has three subunits, alpha, beta, and gamma. The intracellular domain has two subunits, alpha and beta. The alpha subunit has a transmembrane domain and a cytoplasmic domain. The beta subunit has a transmembrane domain and a cytoplasmic domain. The gamma subunit has a transmembrane domain and a cytoplasmic domain. The alpha subunit has a transmembrane domain and a cytoplasmic domain. The beta subunit has a transmembrane domain and a cytoplasmic domain. The gamma subunit has a transmembrane domain and a cytoplasmic domain. The alpha subunit has a transmembrane domain and a cytoplasmic domain. The beta subunit has a transmem</div></article>
    <article class="llm-panel llm-panel-rag"><h3>Base + retrieval</h3><div class="llm-answer-text">The stoichiometry of Na,K-ATPase charge translocation is not known.</div></article>
    <article class="llm-panel llm-panel-ft"><h3>Fine-tuned model</h3><div class="llm-answer-text">The rate of the Na,K-ATPase is dependent on the availability of the Na+ and K+ ions in the cytoplasm. The rate of the Na,K-ATPase is also dependent on the availability of the Na+ and K+ ions in the cytoplasm. The rate of the Na,K-ATPase is also dependent on the availability of the Na+ and K+ ions in the cytoplasm. The rate of the Na,K-ATPase is also dependent on the availability of the Na+ and K+ ions in the cytoplasm. The rate of the Na,K-ATPase is also dependent on the availability of the Na+ and K+ ions in the cytoplasm. The rate of the Na,K-ATPase is also dependent on the availability of the Na+ and K+ ions in the cytoplasm. The rate of the Na,K-ATPase is also dependent on the availability of the Na+ and K+ ions in the cytoplasm. The rate of the Na,K-ATPase is</div></article>
  </div>
</details>

## Closing thoughts

This mini-project taught me several lessons. For one thing, I now appreciate much more clearly how much work goes into cleaning text and producing corpora that are actually usable for training. The original [GPT paper](https://openai.com/index/language-unsupervised/) describes training on [Reddit](https://www.reddit.com/), a broad web corpus, and [Wikipedia](https://www.wikipedia.org/), all of which already provide text in relatively workable form. More modern models, by contrast, often have to absorb material from books and scans that are not naturally formatted for machine learning pipelines. I found [Docling](https://docling-project.github.io/docling/) genuinely useful, but it still did not handle some LaTeX-heavy equations especially well. One limitation I did not test carefully was whether the model could reliably recall expressions such as the Smoluchowski equation. I will also note that I do not believe this model can perform arithmetic or mathematical operations correctly.

I also think the comparison between the base model, base + RAG, and the fine-tuned model is genuinely interesting. I still want to look more carefully at retrieval and prompt-engineering strategies, but even this first pass suggests that for recall-type questions, RAG does not do badly at all. All three systems still hallucinated, of course, and some of those failures were honestly a little funny, but the broader pattern was still informative.

I probably will not be using this particular fine-tuned model for anything serious. The weak answers suggest to me that better performance would require a much larger and cleaner dataset, along with more expensive training than I was willing to do for this experiment. Even so, the project was valuable because it made the hidden labor of fine-tuning much more concrete to me: data curation, model size, learning rate, sequence length, hardware limits, and evaluation design all matter. If nothing else, this was an educational exercise that gave me a better sense of what has to go right before a fine-tuned scientific model becomes genuinely useful.
