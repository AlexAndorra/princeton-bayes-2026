---
theme: default
title: What Your Mixed Model Already Believes
info: A first-principles tour of the Bayesian workflow, built on the repeated-measures model psychologists already fit.
author: Alexandre Andorra
colorSchema: dark
highlighter: shiki
lineNumbers: false
transition: slide-up
mdc: true
layout: center
class: text-center
fonts:
  sans: 'Montserrat, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif'
  mono: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace'
---

# What Your Mixed Model <span class="bg-clip-text text-transparent bg-gradient-to-r from-emerald-500 to-indigo-500 font-bold">Already Believes</span>

## A first-principles tour of the Bayesian workflow

<div class="pt-12 text-xl">Alexandre Andorra</div>

<div class="pt-4 font-light text-gray-400">
<a href="https://alexandorra.github.io/" target="_blank" class="text-gray-300 border-b border-gray-600 hover:text-white">Bayesian data scientist</a> · <a href="https://www.pymc.io/welcome.html" target="_blank" class="text-gray-300 border-b border-gray-600 hover:text-white">PyMC</a> core contributor · host of <a href="https://learnbayesstats.com/" target="_blank" class="text-gray-300 border-b border-gray-600 hover:text-white"><em>Learning Bayesian Statistics</em></a>
</div>

<div class="pt-6 font-light text-gray-500">Princeton Psychology · September 2026</div>

<!--
Thanks for having me. I help maintain PyMC, and I host a podcast where I interrogate people much smarter than me about Bayesian stats.

The promise for the next forty minutes: you already fit mixed models. Every one of them is a story about how your data came to be, a story your software writes for you and hides. Write it yourself, and a whole workflow opens up: see what the model assumes before collecting data, check whether it kept its promises after, improve it on purpose.

Nothing here needs you to be Bayesian already. If you fit glmer, you've done the hard part.
-->

---

## One formula, the whole talk

<div class="text-4xl mt-14 text-center">

$$
\underbrace{p(\theta \mid y)}_{\text{posterior}} \;\propto\; \underbrace{p(y \mid \theta)}_{\text{likelihood}} \;\times\; \underbrace{p(\theta)}_{\text{prior}}
$$

</div>

<div class="grid grid-cols-3 gap-6 mt-14 text-center">
  <div v-click class="bg-gray-800/50 p-5 rounded-lg border-t-4 border-indigo-500">
    <div class="text-indigo-400 font-bold text-xl">prior</div>
    <div class="mt-2 text-gray-300">what you believe <em>before</em> the data</div>
  </div>
  <div v-click class="bg-gray-800/50 p-5 rounded-lg border-t-4 border-cyan-500">
    <div class="text-cyan-400 font-bold text-xl">likelihood</div>
    <div class="mt-2 text-gray-300">the story of how the data came to be</div>
  </div>
  <div v-click class="bg-gray-800/50 p-5 rounded-lg border-t-4 border-emerald-500">
    <div class="text-emerald-400 font-bold text-xl">posterior</div>
    <div class="mt-2 text-gray-300">what you believe <em>after</em>, for every unknown at once</div>
  </div>
</div>

<!--
One formula, as a reminder. The posterior, what you believe after seeing the data, is proportional to the likelihood, your story of how the data came to be, times the prior, what you believed before.

Everything today is these three pieces: we'll write the story, look at what the prior implies, and put the posterior to the test.
-->

---

## The same formula, illustrated

<div class="mx-auto mt-2 w-190 aspect-video rounded-lg overflow-hidden border border-gray-700 shadow-lg">
<iframe
  class="w-full h-full"
  src="https://www.youtube.com/embed/8-s0MAU5HHU?start=93&end=116&rel=0&modestbranding=1"
  title="Bayes' theorem, illustrated"
  frameborder="0"
  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
  allowfullscreen
></iframe>
</div>

<div class="mt-4 text-center text-sm text-gray-500 font-mono">youtu.be/8-s0MAU5HHU · 1:33 to 1:56</div>

<!--
Press play. Twenty seconds: prior, evidence, update. That's the whole formula in one joke.
-->

---
layout: section
---

<div class="text-emerald-400 text-sm uppercase tracking-widest">Part 1</div>

# The model you already fit

<Arc :active="[1]" />

<!--
Let's start with a model that's in half the papers in this building.
-->

---

## You've fit this

<div class="mt-10 bg-gray-900 p-6 rounded-lg border border-gray-700 font-mono text-xl text-center">
glmer(correct ~ condition + (1 | participant), family = binomial)
</div>

<div v-click class="mt-14 text-3xl text-center text-gray-300">
It runs. It gives you a coefficient, a standard error, a p-value.
</div>

<div v-click class="mt-8 text-3xl text-center">
But what did it just <span class="bg-clip-text text-transparent bg-gradient-to-r from-emerald-500 to-indigo-500 font-bold">say</span>?
</div>

<!--
A logistic mixed model for accuracy: was each trial correct, does the condition change that, and each participant gets a baseline through the random intercept.

You get a table and most analyses stop there. I want to slow down on "what did it just say", because the table summarises something much richer, and the richer thing is where the leverage is.
-->

---

## Every model is a story about how the data came to be

<div class="flex items-stretch justify-center gap-3 mt-12">
  <div class="bg-gray-800/50 p-5 rounded-lg border-t-4 border-indigo-500 w-48 text-center">
    <div class="text-4xl">🌍</div>
    <div class="mt-2 text-indigo-400 font-bold">population</div>
    <div class="mt-1 text-sm text-gray-400">a distribution of abilities</div>
  </div>
  <div class="text-3xl text-gray-600 self-center">→</div>
  <div class="bg-gray-800/50 p-5 rounded-lg border-t-4 border-cyan-500 w-48 text-center">
    <div class="text-4xl">🧑‍🔬</div>
    <div class="mt-2 text-cyan-400 font-bold">participant</div>
    <div class="mt-1 text-sm text-gray-400">drawn from it</div>
  </div>
  <div class="text-3xl text-gray-600 self-center">→</div>
  <div class="bg-gray-800/50 p-5 rounded-lg border-t-4 border-teal-500 w-48 text-center">
    <div class="text-4xl">📅</div>
    <div class="mt-2 text-teal-400 font-bold">session</div>
    <div class="mt-1 text-sm text-gray-400">drawn around the person</div>
  </div>
  <div class="text-3xl text-gray-600 self-center">→</div>
  <div class="bg-gray-800/50 p-5 rounded-lg border-t-4 border-emerald-500 w-48 text-center">
    <div class="text-4xl">🎯</div>
    <div class="mt-2 text-emerald-400 font-bold">trial</div>
    <div class="mt-1 text-sm text-gray-400">drawn from the session</div>
  </div>
</div>

<div v-click class="mt-14 text-center text-xl text-gray-300">
<span class="font-mono text-white">(1 | participant)</span> is three "drawn from" arrows, compressed into one line.
</div>

<!--
Here's the story that formula tells. A population with a distribution of abilities. Participants drawn from it. Each session drawn around the person's ability. Each trial drawn from the session.

Four levels, three arrows. The random intercept asserts that whole chain. The software knows the story, it has to, but it only shows you the coefficient.

Bayesian tools make you write every arrow down. People call that the cost. I'll argue it's the benefit.
-->

---

## The same story, three dialects

<div class="grid grid-cols-3 gap-5 mt-8 text-sm">
<div class="bg-gray-800/50 p-4 rounded-lg border-t-4 border-indigo-500">
<div class="text-indigo-400 font-bold mb-2">lme4</div>

```r
glmer(correct ~ condition
      + (1 | participant),
      family = binomial)
```
</div>
<div class="bg-gray-800/50 p-4 rounded-lg border-t-4 border-cyan-500">
<div class="text-cyan-400 font-bold mb-2">brms</div>

```r
brm(correct ~ condition
    + (1 | participant),
    family = bernoulli())
```
</div>
<div class="bg-gray-800/50 p-4 rounded-lg border-t-4 border-emerald-500">
<div class="text-emerald-400 font-bold mb-2">PyMC</div>

```python
theta = mu + sigma*z[pid]
p = invlogit(theta + b*hard)
Bernoulli("y", p, observed=y)
```
</div>
</div>

<div v-click class="mt-10 text-center text-xl text-gray-300">
Not a talk about syntax. PyMC just leaves the story <span class="bg-clip-text text-transparent bg-gradient-to-r from-emerald-500 to-indigo-500 font-bold">out in the open</span>.
</div>

<!--
Same model, three ways. lme4 on the left. brms in the middle, same formula, Bayesian underneath. PyMC on the right, spelled out.

I'm not selling a language. Everything today transfers to brms. The PyMC lines are here because every symbol is one arrow of the story: theta is the ability, mu the population average, sigma how much people differ, b the condition effect. Nothing hidden.
-->

---

## "Already believes"

<div class="text-center text-xl mt-4">Every line of that model is an <span class="bg-clip-text text-transparent bg-gradient-to-r from-emerald-500 to-indigo-500 font-bold">assumption</span></div>

<div class="grid grid-cols-2 gap-5 mt-8 text-lg">
  <div v-click class="bg-gray-800/50 p-5 rounded-lg border border-gray-700 flex items-center gap-4"><span class="text-3xl">🌍</span> participants come from one shared population</div>
  <div v-click class="bg-gray-800/50 p-5 rounded-lg border border-gray-700 flex items-center gap-4"><span class="text-3xl">🧑‍🔬</span> one ability per participant, stable across sessions</div>
  <div v-click class="bg-gray-800/50 p-5 rounded-lg border border-gray-700 flex items-center gap-4"><span class="text-3xl">⚖️</span> the condition shifts everyone by the same amount</div>
  <div v-click class="bg-gray-800/50 p-5 rounded-lg border border-gray-700 flex items-center gap-4"><span class="text-3xl">🪙</span> trials within a session are exchangeable coin flips</div>
</div>

<div v-click class="mt-10 bg-indigo-900/20 border-l-4 border-indigo-500 p-4 text-indigo-100 text-center text-lg">
Frequentist software makes these silently. A Bayesian analysis makes you say them out loud, then lets you <b>check every one</b>.
</div>

<!--
Look at what that one line commits you to. One shared population. One stable ability per person. The condition moves everyone equally. Trials are flips of one coin.

At least one of these, "one stable ability across sessions", is an empirical claim that could be false, and if it is, your standard errors are wrong. The frequentist fit made it for you and didn't mention it.

First gift of the workflow: the assumptions are in the open. Second gift, the rest of the talk: every one becomes checkable.
-->

---
layout: section
---

<div class="text-emerald-400 text-sm uppercase tracking-widest">Part 2</div>

# Priors: the part you can see

<Arc :active="[2, 3]" />

<!--
We start where the story starts: before any data.
-->

---

## The one assumption you can inspect for free

<div class="flex items-center justify-center gap-6 mt-14">
  <div v-click class="bg-gray-800/50 p-6 rounded-lg border-t-4 border-indigo-500 w-56 text-center">
    <div class="text-5xl">🎲</div>
    <div class="mt-3 text-lg">draw parameters from the prior</div>
  </div>
  <div v-click class="text-3xl text-gray-600">→</div>
  <div v-click class="bg-gray-800/50 p-6 rounded-lg border-t-4 border-cyan-500 w-56 text-center">
    <div class="text-5xl">🔮</div>
    <div class="mt-3 text-lg">simulate a fake study</div>
  </div>
  <div v-click class="text-3xl text-gray-600">→</div>
  <div v-click class="bg-gray-800/50 p-6 rounded-lg border-t-4 border-emerald-500 w-56 text-center">
    <div class="text-5xl">👀</div>
    <div class="mt-3 text-lg">look. Absurd? Fix it now.</div>
  </div>
</div>

<div v-click class="mt-14 text-center text-xl text-gray-300">
No participants spent. This is the <span class="bg-clip-text text-transparent bg-gradient-to-r from-emerald-500 to-indigo-500 font-bold">prior predictive check</span>.
</div>

<!--
A prior says what values a parameter could plausibly take before the data. People treat that as the scary, subjective part of Bayes.

It's the opposite: it's the one assumption you can fully inspect before collecting anything. Draw parameters from the prior, push them through the model, generate fake datasets, look. If the fake data is absurd, the model believes something absurd, and you found out on day zero. Let me show you.
-->

---

## What the defaults claim

<div class="grid grid-cols-5 gap-6 mt-2 items-center">
<div class="col-span-3">
<img src="/fig02_prior_absurd.png" class="w-full rounded-lg" />
</div>
<div v-click class="col-span-2">
<div class="text-xl">Normal(0, 10) on the logit scale looks harmless.</div>
<div class="mt-6 bg-red-900/20 border border-red-900/50 rounded-lg p-4 text-red-200">Simulated, it says most sessions score <b>0 or 100 out of 100</b>.</div>
</div>
</div>

<!--
A prior people reach for to be "uninformative": standard deviation ten on the logit scale. Sounds humble.

Simulate from it. This is a rootogram: for each possible number correct out of a hundred, how many sessions the prior expects there. Two spikes at zero and a hundred: this prior believes most sessions are all wrong or all right.

Not humble, absurd. On the logit scale, wide is not vague. And you can see it in ten seconds, before running anyone. Maximum likelihood carries an implicit flat prior with the same shape, and never shows you.
-->

---

## What a sensible prior claims

<div class="grid grid-cols-5 gap-6 mt-2 items-center">
<div class="col-span-3">
<img src="/fig03_prior_sensible.png" class="w-full rounded-lg" />
</div>
<div v-click class="col-span-2">
<div class="text-xl">Normal(0, 1.5): every count about equally plausible.</div>
<div class="mt-6 bg-emerald-900/20 border border-emerald-900/50 rounded-lg p-4 text-emerald-200">Wide. <b>Nothing ruled out, nothing favoured.</b></div>
</div>
</div>

<!--
Same model, one change: one-point-five instead of ten. Now the prior predictive is flat: every number correct about equally plausible. It hasn't decided your result, it has just stopped insisting on the ridiculous.

Notice the move: no philosophical fight about priors. Simulate, look at the consequence in the units you care about, ask "does this look like my field". Anyone in this room can answer that.
-->

---

## Simulate before you collect

<div class="text-center text-2xl mt-6">The prior predictive is a <span class="bg-clip-text text-transparent bg-gradient-to-r from-emerald-500 to-indigo-500 font-bold">power analysis you can believe</span></div>

<div class="flex items-center justify-center gap-6 mt-12">
  <div v-click class="bg-gray-800/50 p-6 rounded-lg border-t-4 border-indigo-500 w-56 text-center">
    <div class="text-5xl">📏</div>
    <div class="mt-3">set the effect you'd care about</div>
  </div>
  <div v-click class="text-3xl text-gray-600">→</div>
  <div v-click class="bg-gray-800/50 p-6 rounded-lg border-t-4 border-cyan-500 w-56 text-center">
    <div class="text-5xl">🔮</div>
    <div class="mt-3">simulate the study, a thousand times</div>
  </div>
  <div v-click class="text-3xl text-gray-600">→</div>
  <div v-click class="bg-gray-800/50 p-6 rounded-lg border-t-4 border-emerald-500 w-56 text-center">
    <div class="text-5xl">📊</div>
    <div class="mt-3">how often do you recover it?</div>
  </div>
</div>

<div v-click class="mt-12 text-center text-xl text-gray-300">Same machinery, run forward. Design is the workflow, before the data.</div>

<!--
Once you can simulate from your model, you can do design. Set the smallest effect you'd care about, simulate the whole study a thousand times, ask how often you recover it and how wide the intervals are.

A power analysis through your actual model and priors, not a lookup table. If the answer is "you'd miss it half the time", you learn it before paying a single participant. Now let's get data and sample.
-->

---
layout: section
---

<div class="text-emerald-400 text-sm uppercase tracking-widest">Part 3</div>

# The posterior is not a number

<Arc :active="[4]" />

<!--
Now we sample, and I want to fight the most common misreading of a Bayesian result.
-->

---

## A distribution over everything

<img src="/fig04_posterior_truth.png" class="w-full mt-4 rounded-lg" />

<div v-click class="mt-6 text-center text-xl text-gray-300">
Dashed = the <b class="text-white">true values</b> (synthetic data). Not a point with an error bar: a <span class="bg-clip-text text-transparent bg-gradient-to-r from-emerald-500 to-indigo-500 font-bold">joint distribution</span> over every unknown.
</div>

<!--
Three panels: population mean, condition effect, between-participant spread. Each a full distribution. I generated this data, so the dashed lines are the truth, and they land inside. One recovery proves nothing on its own; the repeatable check is calibration, coming up. But synthetic data is the only setting where you can grade the answer.

The deeper point: the posterior is a joint distribution over everything at once, all forty participants included. The table is a few summaries of it. And holding the whole object, two ideas you learned separately turn out to be the same thing.
-->

---

## Partial pooling, when you know least

<img src="/fig05a_shrinkage_20trials.png" class="h-95 mx-auto rounded-lg" />

<div v-click class="mt-3 text-center text-lg text-gray-300">
Red = raw accuracy, blue = the model. Every arrow points <span class="bg-clip-text text-transparent bg-gradient-to-r from-emerald-500 to-indigo-500 font-bold">toward the population</span>, furthest where the data is thinnest.
</div>

<!--
Shrinkage, or partial pooling. It IS the random effect.

Twenty trials per participant, so raw estimates are noisy. Red is raw, blue is the model, and every blue dot moved toward the population mean, most for the extremes. Someone at ninety percent on twenty trials was probably lucky, and the model pulls them back.

That's "borrowing strength", and it falls straight out of the story: the participant was drawn from a population, so the population is evidence about the participant.
-->

---

## Shrinkage decays as the data arrive

<img src="/fig05b_shrinkage_progression.png" class="w-full mt-4 rounded-lg" />

<div v-click class="mt-6 text-center text-xl text-gray-300">
As each participant's own data grows, the population matters less. <span class="bg-clip-text text-transparent bg-gradient-to-r from-emerald-500 to-indigo-500 font-bold">That is what a random effect is.</span>
</div>

<!--
Left to right: twenty trials, a hundred, two sessions, four. The shrinkage percentage falls. With little data the model leans on the population; by four sessions the arrows almost vanish.

No threshold, no switch: the random effect weights each person's data against the crowd, continuously, by how much they have. The most useful thing hierarchical models do, and most people never see it happen.
-->

---

## Credible vs confidence: two questions

<img src="/fig06_ci_vs_credible.png" class="h-90 mx-auto rounded-lg" />

<div v-click class="mt-3 text-center text-lg text-gray-300">
Often close in numbers, but one asks <span class="bg-clip-text text-transparent bg-gradient-to-r from-emerald-500 to-indigo-500 font-bold">"where is the truth, given this data?"</span>, and that promise can be tested.
</div>

<!--
Red: a Wilson confidence interval from each person's data alone. Blue: the ninety percent posterior interval from the hierarchical model. Tighter, pulled toward the center: pooling again.

They answer different questions. The confidence interval is about a procedure over imagined repetitions. The credible interval says what you want: given this data and model, ninety percent probability the parameter is in here.

I won't tell you confidence intervals are wrong. My point is narrower: the credible interval makes a promise you can put to the test. So let's test it.
-->

---
layout: section
---

<div class="text-emerald-400 text-sm uppercase tracking-widest">Part 4</div>

# Checking, and expanding

<Arc :active="[5, 6, 7]" />

<!--
The model sampled. That is not the same as the model being any good. Sampling is easy; the checks are the work.
-->

---

## Simulate replications, compare to what you saw

<img src="/fig07_ppc_dist.png" class="w-full mt-2 rounded-lg" />

<div v-click class="mt-4 text-center text-lg text-gray-300">
Left, one stable ability per person: its predictions are <span class="bg-clip-text text-transparent bg-gradient-to-r from-emerald-500 to-indigo-500 font-bold">too narrow</span>. The data has more extreme sessions than it can produce.
</div>

<!--
Same forward simulation, now from the posterior: generate fake studies, thousands of times. A rootogram again: bands are what the model predicts, dots are what happened.

Left panel, the session-blind model. In the tails, the dots sit outside the bands: more very bad and very good sessions than it can generate. Too confident. Right panel, hold that thought.

This model converged cleanly and gave a tidy table. You'd never know from the table. You only know because you made it generate data and looked.
-->

---

## When it says 90%, is it right 90%?

<img src="/fig08_coverage_binomial.png" class="h-90 mx-auto rounded-lg" />

<div v-click class="mt-3 text-center text-lg text-gray-300">
Coverage at every interval width at once. Below the line everywhere: <span class="bg-clip-text text-transparent bg-gradient-to-r from-emerald-500 to-indigo-500 font-bold">over-confident</span>.
</div>

<!--
The promise from the interval slide, cashed out. For every interval width: when the model claims X percent, what fraction of the data actually falls inside? The dashed line is a model keeping its promises.

This one is below the line everywhere: its ninety percent intervals hold about seventy percent of sessions. The p-value in the corner says the deviation is real.

The most useful plot in the workflow, and the one people skip. It turns "I have a bad feeling about my standard errors" into a number, and a direction.
-->

---

## The same thing, sharper: PIT

<img src="/fig09_pit_ecdf.png" class="h-90 mx-auto rounded-lg" />

<div v-click class="mt-3 text-center text-lg text-gray-300">
A calibrated model's residuals are uniform. This curve bows: the data lands in the <span class="bg-clip-text text-transparent bg-gradient-to-r from-emerald-500 to-indigo-500 font-bold">tails</span> far too often.
</div>

<!--
Same diagnosis, sharper instrument. For each observation: where in the model's predictive distribution did the real value land? Calibrated means uniform, and this curve is flat. It bows, and the shape names the failure: data in the tails more often than allowed. Same underdispersion as the rootogram, same over-confidence as the coverage plot. Three views, one diagnosis.

Calibration is the check that generalises: reaction times, counts, choices. ArviZ, or bayesplot in R, does it in one line.
-->

---

## The story had no line for sessions

<div class="grid grid-cols-2 gap-8 mt-10">
<div v-click class="bg-gray-800/50 p-6 rounded-lg border-t-4 border-red-500">
<div class="text-red-400 font-bold">what we assumed</div>
<div class="mt-3 font-mono text-sm">y ~ Binomial(n, p_participant)</div>
<div class="mt-3 text-gray-400">one ability; sessions are just more trials</div>
</div>
<div v-click class="bg-gray-800/50 p-6 rounded-lg border-t-4 border-emerald-500">
<div class="text-emerald-400 font-bold">what we add</div>
<div class="mt-3 font-mono text-sm">p_session ~ Beta(p_participant, κ)<br>y ~ Binomial(n, p_session)</div>
<div class="mt-3 text-gray-400">each session wobbles around the person</div>
</div>
</div>

<div v-click class="mt-10 bg-indigo-900/20 border-l-4 border-indigo-500 p-4 text-indigo-100 text-center text-lg">
In brms, one word: <span class="font-mono text-white">family = beta_binomial()</span>. The failed check told us <b>which</b> word.
</div>

<!--
What do you do with a failed check? Not tweak priors until the warning goes away. The check said something specific: the data varies more than one-ability-per-person allows. A missing level in the story.

We flagged "one stable ability across sessions" as the assumption that might be false. The coverage plot is the evidence that it is. So we add the level: each session gets its own accuracy around the participant's mean, with kappa controlling the wobble. The beta-binomial. In brms, one word. We didn't guess our way there; the failed check named the fix.
-->

---

## The expanded model keeps its promise

<img src="/fig10_coverage_betabinomial.png" class="h-90 mx-auto rounded-lg" />

<div v-click class="mt-3 text-center text-lg text-gray-300">
Same plot, session-aware model: <span class="bg-clip-text text-transparent bg-gradient-to-r from-emerald-500 to-indigo-500 font-bold">back on the line</span>. Failing was where the model got better.
</div>

<!--
Coverage for the expanded model: on the line, if anything a hair cautious, the safe way to be wrong. On the rootogram's right side the dots sat inside the bands too. And it recovers the true between-session variability I planted.

Name the shape of what happened: we wrote a model, sampled it, made it generate data, it failed a measurable check, the failure pointed at a missing piece, we added it, the check passed. The failure was the most informative thing that happened.

That's the loop. So when do you stop looping?
-->

---
layout: section
---

<div class="text-emerald-400 text-sm uppercase tracking-widest">Part 5</div>

# When do you stop?

<Arc :active="[7]" />

---

## Comparison is one input, not a verdict

<img src="/fig11_compare_panel.png" class="w-full mt-4 rounded-lg" />

<!--
There is a number for "which predicts better": cross-validation, ELPD, and it strongly prefers the session-aware model.

But that number is not the verdict. It agrees with the rootogram and the coverage plot, and the agreement is the evidence: three checks reading the data three ways, all saying the session level was missing.

The tempting move is a magic number: is the difference more than some multiple of its error? Resist it. Cross-validation asks which model predicts held-out data better, a different question from which is true, or which serves your purpose. One input, never an oracle.
-->

---

## No single number closes the loop

<div class="grid grid-cols-3 gap-6 mt-10 text-center text-xl">
  <div class="bg-gray-800/50 p-6 rounded-lg border border-gray-700"><div class="text-4xl">🎯</div><div class="mt-3">a p-value</div></div>
  <div class="bg-gray-800/50 p-6 rounded-lg border border-gray-700"><div class="text-4xl">⚖️</div><div class="mt-3">a Bayes factor</div></div>
  <div class="bg-gray-800/50 p-6 rounded-lg border border-gray-700"><div class="text-4xl">📉</div><div class="mt-3">an ELPD difference</div></div>
</div>

<div v-click class="mt-12 text-center text-2xl">
Each summarises one question. None knows what your model is <span class="bg-clip-text text-transparent bg-gradient-to-r from-emerald-500 to-indigo-500 font-bold">for</span>.
</div>

<div v-click class="mt-6 text-center text-xl text-gray-400">When to stop is a judgment about purpose. Yours, not the number's.</div>

<!--
A p-value, a Bayes factor, an ELPD difference: each compresses one question into a scalar, and none knows what you'll do with the model. Good enough to estimate a group effect may be nowhere near good enough to predict one person's next session.

The workflow gives you no stopping rule. It gives you instruments that say where the model fails and by how much, so that when you stop, you stop with your eyes open. The judgment stays yours.
-->

---

## The arc

<Arc size="lg" />

<div v-click class="mt-12 text-center text-xl text-gray-300">
You already do the first two out of habit. The rest is <span class="bg-clip-text text-transparent bg-gradient-to-r from-emerald-500 to-indigo-500 font-bold">one move</span>, forward simulation, pointed at different questions.
</div>

<!--
The whole thing on one slide. Write the story. Choose priors. Simulate from them and look. Sample. Simulate from the posterior and compare to reality. Measure the promises. Where it fails, expand, and go around again.

You do the first two every time you specify a model. Everything after "sample" is the same trick, generate data from the model, aimed at a different question. Not a bag of tests: one move, repeated.

I promised a twist. What happens when you hand this problem to an AI coding assistant?
-->

---
layout: section
---

<div class="text-emerald-400 text-sm uppercase tracking-widest">Part 6</div>

# What happens when you hand this to an AI

<Arc />

---

## Same data, with a classic prompt

<div class="mt-10 bg-indigo-900/20 border-l-4 border-indigo-500 p-6 text-xl text-indigo-100 italic">
"I ran a study: 40 participants, two conditions, five sessions, 100 trials each. Compute each participant's accuracy with an interval, test whether the conditions differ, and write me a short report for lab meeting."
</div>

<div v-click class="mt-12 text-center text-2xl text-gray-300">
It answered the question <span class="bg-clip-text text-transparent bg-gradient-to-r from-emerald-500 to-indigo-500 font-bold">as asked</span>. Which is exactly the problem.
</div>

<!--
I gave a coding assistant, Claude Code on a mid-size model, the exact dataset from this talk, with the prompt most people would type. Not "do a rigorous Bayesian workflow". Just: compute accuracies, test the conditions, write it up.

It did that, competently. And "the question as asked" skips most of the workflow you just watched. Exactly what a capable, rushed human does at 11pm before lab meeting.

The fix is interesting, and it's not "use a bigger model".
-->

---

## Before / after

<div class="grid grid-cols-2 gap-6 mt-6">
<div class="bg-gray-800/50 p-5 rounded-lg border-t-4 border-red-500">
<div class="text-red-400 font-bold text-lg">on its own</div>
<ul class="mt-3 space-y-2 text-gray-300">
<li>✅ prior predictive, prior sensitivity, partial pooling, caveats</li>
<li>❌ plain binomial: sessions pooled as trials</li>
<li>❌ checked its predictions by eye, never their calibration</li>
</ul>
</div>
<div class="bg-gray-800/50 p-5 rounded-lg border-t-4 border-emerald-500">
<div class="text-emerald-400 font-bold text-lg">with the workflow written down as a "skill"</div>
<ul class="mt-3 space-y-2 text-gray-300">
<li>✅ measured the overdispersion, built the <b class="text-white">beta-binomial</b></li>
<li>✅ ran the <b class="text-white">coverage / PIT check</b> and cross-validation</li>
<li>✅ reviewed its own draft, caught it understating the diagnostics, rebuilt</li>
</ul>
</div>
</div>

<!--
Left, on its own: genuinely careful, prior predictive, sensitivity analysis, partial pooling, caveats. But a plain binomial, sessions pooled as trials, and fit checked by eye, never calibration. Session-blind.

Right, same model, same data, the workflow installed as a skill, a file it reads before starting. It measured the overdispersion, built the beta-binomial we just built, ran the coverage check and cross-validation, and reviewed its own work. Which is the next slide.
-->

---

## What it took

<div class="text-center text-xl mt-2">Not a smarter model. The <span class="bg-clip-text text-transparent bg-gradient-to-r from-emerald-500 to-indigo-500 font-bold">workflow, written down</span>, as a checklist it reads before it starts.</div>

<div class="grid grid-cols-2 gap-6 mt-8">
<div v-click class="bg-gray-800/50 p-6 rounded-lg border-t-4 border-cyan-500">
<div class="text-cyan-400 font-bold">surprise 1</div>
<div class="mt-3 text-gray-300">The bare assistant was already careful. The skill supplied the two moves a careful analyst still skipped: <b class="text-white">model the session level</b>, and <b class="text-white">check calibration</b>.</div>
</div>
<div v-click class="bg-gray-800/50 p-6 rounded-lg border-t-4 border-emerald-500">
<div class="text-emerald-400 font-bold">surprise 2</div>
<div class="mt-3 text-gray-300">Its own review caught its first write-up <b class="text-white">understating the diagnostics it had just computed</b>. It accepted the criticism, rebuilt, re-checked.</div>
</div>
</div>

<!--
Same model in both runs. What changed was the workflow, written down: the arc from a few slides ago, as a checklist. That's all a skill is.

Two surprises. First, the bare assistant was already careful; the skill didn't rescue a lazy agent, it supplied the two domain moves a careful one still skipped: model the session level, check calibration.

Second, the real one: with the workflow, it reviewed its own work before calling it done, and that review caught its first write-up understating the diagnostics: an unreliable cross-validation, a calibration softened to "mild" that wasn't. It rebuilt and re-checked. It caught itself. That's the thesis inside the machine: the workflow doesn't make the model right, it makes the analyst check hard enough to find where it's wrong.
-->

---

## This afternoon

<div class="flex items-center justify-center gap-6 mt-12">
  <div v-click class="bg-gray-800/50 p-6 rounded-lg border-t-4 border-indigo-500 w-56 text-center">
    <div class="text-5xl">🛠️</div>
    <div class="mt-3">build both models on this data</div>
  </div>
  <div v-click class="bg-gray-800/50 p-6 rounded-lg border-t-4 border-cyan-500 w-56 text-center">
    <div class="text-5xl">🎯</div>
    <div class="mt-3">watch the checks catch the session-blind one</div>
  </div>
  <div v-click class="bg-gray-800/50 p-6 rounded-lg border-t-4 border-emerald-500 w-56 text-center">
    <div class="text-5xl">🤖</div>
    <div class="mt-3">critique the AI's run yourselves</div>
  </div>
</div>

<div v-click class="mt-12 text-center text-lg text-gray-400">Google Colab, nothing to install, no Python assumed. R users welcome: it all transfers to brms.</div>

<!--
You build both models on this data, watch the checks catch the session-blind one, and critique the AI's run yourselves. No coding required, just reading plots and asking the questions it didn't.

Everything runs in the browser via Google Colab. Nothing to install. R users welcome, it all transfers to brms.
-->

---
layout: center
class: text-center
---

# <span class="bg-clip-text text-transparent bg-gradient-to-r from-emerald-500 to-indigo-500 font-bold">Thank You</span>

<div class="mt-4 text-lg text-gray-400">A loop you run with instruments, until the model is good enough for what <em>you</em> need.</div>

<div class="grid grid-cols-3 gap-8 mt-10 w-full max-w-3xl mx-auto">
  <div class="flex flex-col items-center">
    <div class="bg-white p-2 rounded-xl shadow-lg border-2 border-emerald-500">
      <img src="/qr_repo.png" class="w-32 h-32" />
    </div>
    <span class="mt-4 font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-600 to-emerald-400">Slides, notebook & code</span>
    <span class="text-xs text-gray-500 font-mono mt-1">github.com/AlexAndorra/princeton-bayes-2026</span>
  </div>
  <div class="flex flex-col items-center">
    <div class="bg-white p-2 rounded-xl shadow-lg border-2 border-cyan-500">
      <img src="/qr_podcast.png" class="w-32 h-32" />
    </div>
    <span class="mt-4 font-bold bg-clip-text text-transparent bg-gradient-to-r from-cyan-600 to-cyan-400">Podcast</span>
    <span class="text-xs text-gray-500 font-mono mt-1">learnbayesstats.com</span>
  </div>
  <div class="flex flex-col items-center">
    <div class="bg-white p-2 rounded-xl shadow-lg border-2 border-indigo-500">
      <img src="/qr_site.png" class="w-32 h-32" />
    </div>
    <span class="mt-4 font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-indigo-400">Contact</span>
    <span class="text-xs text-gray-500 font-mono mt-1">alexandorra.github.io</span>
  </div>
</div>

<div class="mt-10 text-gray-500">Alexandre Andorra</div>

<!--
That's the talk. The one sentence to keep: the Bayesian workflow isn't a test you pass, it's a loop you run with instruments until the model is good enough for what you actually need, and you're the one who defines enough.

Everything is in the repo: slides, data, notebook, the AI runs. The podcast is where I argue about this every couple of weeks with people who know more than I do.

Thank you for your attention. I'd love to take questions, and to see you this afternoon.
-->
