---
layout: post
title: "Bag of Words"
description: "Using a simple NLP method to analyze a 28-paper corpus."
tags: [science]
categories: [science]
---

This post reviews a homework assignment in which I used a Bag of Words model to analyze 28 scientific papers. By converting each document into a vector representation, I tested whether a simple NLP pipeline could recover meaningful scientific subtopics from the corpus.

Bag of Words is one of the earliest and most influential vector space approaches in natural language processing. While it lacks the sophistication of modern language models, it provides an interpretable foundation for understanding how text can be represented numerically and compared across documents. I present this analysis as an introduction to the broader idea of language models and computational text analysis.

<div class="card my-4">
  <div class="card-body">
    <div class="text-muted small mb-3">At a glance</div>
    <div class="row text-center">
      <div class="col-6 col-md-3 mb-3 mb-md-0">
        <div class="text-muted small">Corpus</div>
        <div class="h5 mb-0">28 papers</div>
      </div>
      <div class="col-6 col-md-3 mb-3 mb-md-0">
        <div class="text-muted small">Methods</div>
        <div class="h5 mb-0">BoW + TF-IDF</div>
      </div>
      <div class="col-6 col-md-3 mb-3 mb-md-0">
        <div class="text-muted small">Embeddings</div>
        <div class="h5 mb-0">PCA, UMAP</div>
      </div>
      <div class="col-6 col-md-3">
        <div class="text-muted small">Best cosine pair</div>
        <div class="h5 mb-0">0.6177</div>
      </div>
    </div>
  </div>
</div>

## Overview

### 1) Preprocessing and vectorization

- lowercase conversion
- punctuation removal
- whitespace token splitting
- term-document matrix construction

From the raw count matrix \(X\), I computed TF-IDF:

$$
T_{d,t}
=
\frac{X_{d,t}}{\sum_{t'} X_{d,t'}}
\cdot
\log\left(
\frac{N}{
\sum_{d'} \mathbf{1}[X_{d',t} > 0]
}
\right)
$$

Then each document vector was L2-normalized.

### 2) Dimensionality reduction and similarity

- PCA on normalized TF-IDF vectors
- UMAP with cosine distance (`n_neighbors=5`, `min_dist=0.1`)
- cosine similarity matrix + hierarchical ordering using distance \(1 - \cos(i,j)\)

## Additional comments

The utility of TF-IDF weighting and L2 normalization was a key part of this assignment.  
When I built the raw term-document matrix, the most frequent token was, unsurprisingly, `and`.

This is exactly why raw counts alone can produce weak embeddings: high-frequency background tokens dominate the signal across nearly all documents.  
After TF-IDF weighting, high-weight terms shifted toward more domain-specific vocabulary such as `cgas`.

<div class="table-responsive my-3">
  <table class="table table-sm table-striped table-bordered align-middle">
    <caption class="caption-top">Top 10 most frequent tokens in the raw corpus</caption>
    <thead>
      <tr>
        <th scope="col">Rank</th>
        <th scope="col">Term</th>
        <th scope="col">Count</th>
      </tr>
    </thead>
    <tbody>
      <tr><td>1</td><td>and</td><td>14573</td></tr>
      <tr><td>2</td><td>of</td><td>13337</td></tr>
      <tr><td>3</td><td>the</td><td>12363</td></tr>
      <tr><td>4</td><td>in</td><td>10033</td></tr>
      <tr><td>5</td><td>a</td><td>6960</td></tr>
      <tr><td>6</td><td>to</td><td>6528</td></tr>
      <tr><td>7</td><td>cells</td><td>6462</td></tr>
      <tr><td>8</td><td>t</td><td>6120</td></tr>
      <tr><td>9</td><td>al</td><td>5411</td></tr>
      <tr><td>10</td><td>et</td><td>5343</td></tr>
    </tbody>
  </table>
</div>

{% include figure.liquid path="assets/img/blog/bag-of-words-cmsc-354-hw1/term_count_heatmap.png" class="img-fluid rounded z-depth-1" alt="Term-document matrix heatmap showing sparse token occurrence across documents" caption="Term-Document Matrix. The figure shows whether or not a word appears in a given document." zoomable=true %}

## Main findings

- papers with similar subtopics tended to group together
- the first three PCA components explained `0.106`, `0.100`, and `0.095` of variance
- PCA loadings reflected biologically meaningful terms (for example `tfh`, `gc`, `germinal`, `follicular`)
- UMAP gave a cleaner nonlinear separation than PCA in some regions
- the cosine clustermap was consistent with those grouping patterns

<div class="row">
  <div class="col-md-6">
    {% include figure.liquid path="assets/img/blog/bag-of-words-cmsc-354-hw1/pca.png" class="img-fluid rounded z-depth-1" alt="PCA projection of TF-IDF vectors colored by immunology subtopic" caption="PCA projection of normalized TF-IDF vectors. Subtopic structure is partially visible in linear space." zoomable=true %}
  </div>
  <div class="col-md-6">
    {% include figure.liquid path="assets/img/blog/bag-of-words-cmsc-354-hw1/umap_opt.png" class="img-fluid rounded z-depth-1" alt="UMAP embedding of TF-IDF vectors with cosine distance and tuned parameters" caption="UMAP embedding (`n_neighbors=5`, `min_dist=0.1`) showing clearer nonlinear grouping by subtopic." zoomable=true %}
  </div>
</div>

{% include figure.liquid path="assets/img/blog/bag-of-words-cmsc-354-hw1/clustermap.png" class="img-fluid rounded z-depth-1" alt="Cosine similarity clustermap of document vectors ordered by hierarchical clustering" caption="Cosine similarity clustermap reordered by hierarchical clustering. Similar papers align in local blocks." zoomable=true %}

## Nearest-neighbor check

<div class="table-responsive my-3">
  <table class="table table-sm table-striped table-bordered align-middle">
    <caption class="caption-top">Closest document pair under cosine similarity of TF-IDF vectors</caption>
    <tbody>
      <tr><th scope="row">Query document</th><td>Doc 0</td></tr>
      <tr><th scope="row">Nearest neighbor</th><td>Doc 6</td></tr>
      <tr><th scope="row">Cosine similarity</th><td>0.6177</td></tr>
    </tbody>
  </table>
</div>

<div class="table-responsive my-3">
  <table class="table table-sm table-striped table-bordered align-middle">
    <caption class="caption-top">Metadata for the closest document pair</caption>
    <thead>
      <tr>
        <th scope="col">Doc</th>
        <th scope="col">Title</th>
        <th scope="col">Subtopic</th>
      </tr>
    </thead>
    <tbody>
      <tr><td>0</td><td>Molecular and cellular insights into T cell exhaustion.</td><td>T-cell exhaustion</td></tr>
      <tr><td>6</td><td>Defining "T cell exhaustion".</td><td>T_cell</td></tr>
    </tbody>
  </table>
</div>

<div class="table-responsive my-3">
  <table class="table table-sm table-striped table-bordered align-middle">
    <caption class="caption-top">Top shared TF-IDF terms for Docs 0 and 6</caption>
    <thead>
      <tr>
        <th scope="col">Term</th>
        <th scope="col">Shared score</th>
      </tr>
    </thead>
    <tbody>
      <tr><td>exhausted</td><td>0.2281</td></tr>
      <tr><td>exhaustion</td><td>0.1415</td></tr>
      <tr><td>pd1</td><td>0.0550</td></tr>
      <tr><td>pubmed</td><td>0.0462</td></tr>
      <tr><td>manuscript</td><td>0.0460</td></tr>
      <tr><td>author</td><td>0.0364</td></tr>
      <tr><td>wherry</td><td>0.0048</td></tr>
      <tr><td>tumour</td><td>0.0042</td></tr>
      <tr><td>pmc</td><td>0.0035</td></tr>
      <tr><td>progenitor</td><td>0.0029</td></tr>
      <tr><td>tumours</td><td>0.0027</td></tr>
      <tr><td>cd8</td><td>0.0020</td></tr>
    </tbody>
  </table>
</div>

<details class="my-4">
  <summary><strong>Supplementary: top PCA loading tables (PC1 / PC2 / PC3)</strong></summary>
  <div class="mt-3">
    <div class="table-responsive my-3">
      <table class="table table-sm table-striped table-bordered align-middle">
        <caption class="caption-top">PC1 top contributing terms (explained variance = 0.106)</caption>
        <thead>
          <tr><th scope="col">Term</th><th scope="col">Loading</th></tr>
        </thead>
        <tbody>
          <tr><td>gc</td><td>0.4543</td></tr>
          <tr><td>tfh</td><td>0.2394</td></tr>
          <tr><td>germinal</td><td>0.1579</td></tr>
          <tr><td>org</td><td>0.1191</td></tr>
          <tr><td>gcs</td><td>0.1136</td></tr>
          <tr><td>lz</td><td>0.1119</td></tr>
          <tr><td>follicular</td><td>0.1003</td></tr>
          <tr><td>annualreviews</td><td>0.0984</td></tr>
          <tr><td>dz</td><td>0.0959</td></tr>
          <tr><td>https</td><td>0.0869</td></tr>
          <tr><td>self-reactive</td><td>0.0822</td></tr>
          <tr><td>pubmed</td><td>-0.2997</td></tr>
          <tr><td>manuscript</td><td>-0.2147</td></tr>
          <tr><td>autophagy</td><td>-0.2022</td></tr>
          <tr><td>author</td><td>-0.1893</td></tr>
          <tr><td>exhausted</td><td>-0.1622</td></tr>
          <tr><td>exhaustion</td><td>-0.1589</td></tr>
          <tr><td>deretic</td><td>-0.1132</td></tr>
          <tr><td>tex</td><td>-0.0924</td></tr>
          <tr><td>pd1</td><td>-0.0754</td></tr>
        </tbody>
      </table>
    </div>

    <div class="table-responsive my-3">
      <table class="table table-sm table-striped table-bordered align-middle">
        <caption class="caption-top">PC2 top contributing terms (explained variance = 0.100)</caption>
        <thead>
          <tr><th scope="col">Term</th><th scope="col">Loading</th></tr>
        </thead>
        <tbody>
          <tr><td>https</td><td>0.3579</td></tr>
          <tr><td>org</td><td>0.3322</td></tr>
          <tr><td>tex</td><td>0.1823</td></tr>
          <tr><td>ammasome</td><td>0.1255</td></tr>
          <tr><td>1038</td><td>0.0911</td></tr>
          <tr><td>ammatory</td><td>0.0862</td></tr>
          <tr><td>guest</td><td>0.0773</td></tr>
          <tr><td>gc</td><td>-0.3272</td></tr>
          <tr><td>pubmed</td><td>-0.3113</td></tr>
          <tr><td>manuscript</td><td>-0.2155</td></tr>
          <tr><td>author</td><td>-0.1884</td></tr>
          <tr><td>germinal</td><td>-0.1300</td></tr>
          <tr><td>autophagy</td><td>-0.1139</td></tr>
          <tr><td>gcs</td><td>-0.1081</td></tr>
          <tr><td>dz</td><td>-0.1043</td></tr>
          <tr><td>lz</td><td>-0.1042</td></tr>
          <tr><td>tfh</td><td>-0.0774</td></tr>
          <tr><td>shm</td><td>-0.0714</td></tr>
          <tr><td>deretic</td><td>-0.0667</td></tr>
          <tr><td>bcr</td><td>-0.0653</td></tr>
        </tbody>
      </table>
    </div>

    <div class="table-responsive my-3">
      <table class="table table-sm table-striped table-bordered align-middle">
        <caption class="caption-top">PC3 top contributing terms (explained variance = 0.095)</caption>
        <thead>
          <tr><th scope="col">Term</th><th scope="col">Loading</th></tr>
        </thead>
        <tbody>
          <tr><td>tex</td><td>0.5089</td></tr>
          <tr><td>exhaustion</td><td>0.3057</td></tr>
          <tr><td>guest</td><td>0.2314</td></tr>
          <tr><td>exhausted</td><td>0.1664</td></tr>
          <tr><td>annualreviews</td><td>0.1507</td></tr>
          <tr><td>iy37ch19-wherry</td><td>0.1199</td></tr>
          <tr><td>pd-1</td><td>0.1158</td></tr>
          <tr><td>cls</td><td>0.1157</td></tr>
          <tr><td>arjats</td><td>0.1157</td></tr>
          <tr><td>etal</td><td>0.1138</td></tr>
          <tr><td>tmem</td><td>0.1073</td></tr>
          <tr><td>teff</td><td>0.1057</td></tr>
          <tr><td>downloaded</td><td>0.0997</td></tr>
          <tr><td>2026</td><td>0.0997</td></tr>
          <tr><td>www</td><td>0.0970</td></tr>
          <tr><td>mon</td><td>0.0907</td></tr>
          <tr><td>https</td><td>-0.2133</td></tr>
          <tr><td>autophagy</td><td>-0.1412</td></tr>
          <tr><td>org</td><td>-0.1320</td></tr>
          <tr><td>cgas</td><td>-0.1191</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</details>

## Limitations

- preprocessing was intentionally simple, so metadata/noise leaked into features
- tokens such as `annualreviews`, `https`, `pubmed`, and `author` appeared with large weights
- BoW/TF-IDF ignores word order and deeper semantics

<div class="row">
  <div class="col-md-6">
    {% include figure.liquid path="assets/img/blog/bag-of-words-cmsc-354-hw1/umap_nn.png" class="img-fluid rounded z-depth-1" alt="UMAP parameter sweep over number of neighbors" caption="UMAP hyperparameter sweep over `n_neighbors`." zoomable=true %}
  </div>
  <div class="col-md-6">
    {% include figure.liquid path="assets/img/blog/bag-of-words-cmsc-354-hw1/umap_dist.png" class="img-fluid rounded z-depth-1" alt="UMAP parameter sweep over minimum distance setting" caption="UMAP hyperparameter sweep over `min_dist`." zoomable=true %}
  </div>
</div>

## Takeaway

Bag-of-Words + TF-IDF provided an interpretable baseline that partially recovered subtopic structure in this 28-paper corpus, though the results were strongly affected by simple preprocessing choices and residual PDF/source metadata.
