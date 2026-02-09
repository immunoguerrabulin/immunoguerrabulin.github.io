---
layout: post
title: "AI Agents in Science Part 1"
description: "Notes and comments from a course I took Fall 2025"
tags: [science]
categories: [science]
---

Large Language Models (LLMs) have reached research pipelines across the board. Colleagues and I use them to debug code, optimize workflows, and summarize papers. One colleague even managed to "vibe code" an iOS app with Claude. As a fifth-year graduate student in the 2025-2026 academic year, I felt it was important to stay current with rapidly evolving computational methods. Naturally, I enrolled in "CMSC 35370 1 AI Agents for Science," taught by Professor Ian Foster. The course is still fresh in my mind, and fortunately the materials are publicly available at [Agents4Science](https://agents4science.github.io/).

This will most likely be a series of posts where I summarize the course and reflect on some of my problem set solutions. I give a reduced version of my notes here since the slides are publicly available.

## Lecture 1: What is an “Agent” and overview of the course.

_The class was packed (not surprising), and many people were even sitting on the floor to attend the lecture._ The class started with a nice introduction to the purpose of the class, what an agent is, and why there is so much hype around the topic. The quick answer to the hype portion is that the rise of LLMs provides an engine to power these systems.

{% include figure.liquid path="assets/img/blog/ai-agents-in-science/ai4science_lecture1.png" class="img-fluid rounded z-depth-1" alt="Lecture slide: a simple perspective on an LLM in a loop with an objective" caption="A simple perspective: an LLM in a loop with an objective (lecture slide)." zoomable=true %}

The meme Professor Foster provided humorously captured a common view at both ends of the spectrum: an agent is "just" an LLM placed in a loop to accomplish a task. However, when you look under the hood there could be many different ways that this "for loop" is constructed.

An _agent_ is more than a LLM that can answer questions. It is a system that:

1. Takes a state and goals
2. Sense: has the ability to observe its environment
3. Plan: figures out how to execute a goal
4. Act: has the ability to act in its environment
5. Learn: updates its state or goals based on actions

This is the "for loop" Foster talks about in the lecture.

## Review of the different types of models

_Before getting into agents themselves, Foster briefly reviewed the evolution of machine learning models that made agentic systems possible._

Traditional ML: A model of some kind (GNN, CNN,...) is trained to do a specific task. One model is typically trained for a specific modality. Requires a lot of supervision from a human.

Foundation models (E.g. LLMs): A multi-modal model that can be adapted to many different tasks. It is typically pre-trained using self-supervised objectives on large, unlabeled datasets.

Reasoning models: Use explicit multi-step reasoning and self-consistency checks to reduce errors. It is slower but usually more accurate.

## Agents in Science published, on-going work, and how they will accelerate science

#### Agentic discovery loops in practice

Since this was just the first lecture, we were given an overview of the current deployments of agents and what experts are looking to use them for. Professor Foster introduced a perspective paper, [Accelerating materials discovery using artificial intelligence, high performance computing and robotics](https://www.nature.com/articles/s41524-022-00765-z), where he uses their Fig.2 to show how a modern agentic system may work. It would have the ability to come up with a hypothesis, test it with an automated lab or deploy simulations (or both!), analyze the experiments, discuss the findings to make a discussion or update hypothesis, find gaps in the understanding, then reason.

{% include figure.liquid path="assets/img/blog/ai-agents-in-science/agent_perspective.png" class="img-fluid rounded z-depth-1" alt="Figure 2 from the perspective paper showing technology-driven acceleration of the discovery cycle" caption="Figure 2 from 'Accelerating materials discovery using artificial intelligence, high performance computing and robotics' (Nature Computational Materials, 2022)." zoomable=true %}

#### Research papers as agents

The next topic he mentioned was [Paper2Agent: Reimagining Research Papers as Interactive and Reliable AI Agents](https://arxiv.org/pdf/2509.06917). The point being that agents simplify the barrier to entry for scientists because we are able to communicate directly with them using human language. (Aside: I read over the Paper2Agent work and it is in fact exciting to see that agent was able to convert a paper into something that could be used to carry out research. In my field, this could be extremely useful for trying to use the latest papers to analyze trajectories.)

#### Single-agent vs multi-agent systems

The debate between using one large, general-purpose model versus multiple smaller, specialized models was also raised. In regard to size of the model, I mean the number of parameters that the model has. If there was a large enough reasoning model, which Prof Foster compares to a human, might be able to carry out a whole task. However, in the agentic systems era we are in right now it is more common to have several agents with one specific task, such as idea generator and idea critic.

The class concluded with a quick overview of the research being done at Argonne. I was particularly excited about the work of Arvind Ramanathan, who is trying to design antimicrobial peptides. Arvind gave a lecture later in the course, but the TLDR is that the agentic system has a link to data and the ability to use structure prediction software/physics-based simulations, has an evaluator, and they also linked it up to a real experimental setup.

Foreshadowing: A certain Nvidia paper was not mentioned in this lecture...but it will turn out that smaller models are probably where agentic systems will start heading ([arXiv:2506.02153](https://arxiv.org/pdf/2506.02153)). This idea is closely related to modern scaling laws, which describe (or try to describe) how model performance depends on the interplay between parameter count and the amount of training data. The implication is that there is a regime where smaller, well-trained models can be more efficient and effective. This is something that I think is cool!
