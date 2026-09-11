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
fonts:
  sans: 'Montserrat, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif'
  mono: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace'
---

<style>
:root { --bg: #1a1d21; }
.slidev-layout { background: var(--bg); color: #E6E8EB; }
.slidev-layout h1 { color: #fff; font-weight: 700; }
.slidev-layout h2 { color: #fff; font-weight: 600; }
.grad { background: linear-gradient(90deg, #0078ee, #00eeb2); -webkit-background-clip: text; background-clip: text; color: transparent; font-weight: 700; }
.card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 0.6rem; padding: 1rem 1.2rem; }
.tag { color: #9bddfb; font-size: 0.8rem; letter-spacing: 0.08em; text-transform: uppercase; }
.slidev-layout img { border-radius: 0.4rem; }
code { color: #9bddfb; }
</style>

# What Your Mixed Model <span class="grad">Already Believes</span>

### A first-principles tour of the Bayesian workflow

<div class="mt-16 text-gray-400">
Alex Andorra · Bayesian data scientist · PyMC core contributor<br>
host of the <em>Learning Bayesian Statistics</em> podcast
</div>

<!--
Thanks for having me. I'm a Bayesian data scientist, I help maintain PyMC — the library a lot of this runs on — and I host a podcast called Learning Bayesian Statistics, where I mostly get to interrogate people much smarter than me.

Here's the promise for the next forty minutes. You already fit mixed-effects models. I want to show you that every one of them is a story about how your data came to be — a story your software writes down for you and then hides. A Bayesian analysis makes you write it yourself, and the moment you do, a whole workflow opens up: you can see what your model assumes before you collect data, you can check whether it kept its promises after, and you can improve it on purpose instead of by trial and error.

No part of this needs you to already be Bayesian. If you fit lmer or glmer, you have already done the hard modelling; you just haven't been shown the object underneath. That's what today is.
-->

---
layout: section
---

<div class="tag">Part 1</div>

# The model you already fit

<!--
Let's start with a model that's in half the papers in this building.
-->

---

## You've fit this

<div class="mt-8 card font-mono text-xl">
glmer(correct ~ condition + (1 | participant), family = binomial)
</div>

<div v-click class="mt-10 text-2xl">
It runs. It gives you a coefficient on <span class="grad">condition</span>, a standard error, a p-value.
</div>

<div v-click class="mt-6 text-2xl text-gray-300">
But what did it just <em>say</em>?
</div>

<!--
This is a logistic mixed model for accuracy: was each trial correct, does the condition change that, and participants get their own baseline through the random intercept.

You fit it, you get a table: a coefficient on condition, a standard error, a p-value, maybe an AIC. And the table is where most analyses stop — you report the coefficient and move on.

I want to slow down on the "what did it just say" part, because the table is a summary of something much richer, and the richer thing is where all the leverage is. The coefficient is an answer. Today is about the question it answered, and the three or four other questions the same model can answer if you ask.
-->

---

## Every model is a story about how the data came to be

<div class="grid grid-cols-4 gap-3 mt-10">
  <div class="card"><div class="tag">population</div><div class="mt-2">a distribution of abilities across people</div></div>
  <div class="card"><div class="tag">participant</div><div class="mt-2">each person drawn from it</div></div>
  <div class="card"><div class="tag">session</div><div class="mt-2">each sitting drawn around the person</div></div>
  <div class="card"><div class="tag">trial</div><div class="mt-2">each response drawn from the session</div></div>
</div>

<div v-click class="mt-10 text-xl text-gray-300">
The formula <span class="font-mono text-white">(1 | participant)</span> is three "drawn from" statements, compressed into one line.
</div>

<!--
Here's the story that formula tells. There's a population of people with a distribution of abilities. Your participants are drawn from that population. Each participant sits down for several sessions, and their accuracy on a given day is drawn around their own personal ability. And within a session, each trial is a draw — correct or not — from that session's accuracy.

Population, participant, session, trial. Four levels, three "drawn from" arrows. When you write the random intercept, you are asserting that whole chain. The software knows the story — it has to, to compute anything — but it shows you only the final coefficient. The generative story is doing all the work and getting none of the credit.

Frequentist tools let you stay agnostic about most of this. Bayesian tools do not: to sample a model you have to write every arrow down. People sometimes describe that as the cost of going Bayesian. I want to argue it's the benefit.
-->

---

## The same story, three dialects

<div class="grid grid-cols-3 gap-4 mt-8 text-sm">
<div class="card"><div class="tag">lme4</div>

```r
glmer(correct ~ condition
      + (1 | participant),
      family = binomial)
```
</div>
<div class="card"><div class="tag">brms</div>

```r
brm(correct ~ condition
    + (1 | participant),
    family = bernoulli())
```
</div>
<div class="card"><div class="tag">PyMC</div>

```python
theta = mu + sigma*z[pid]
p = invlogit(theta + b*hard)
Bernoulli("y", p, observed=y)
```
</div>
</div>

<div v-click class="mt-8 text-xl text-gray-300">
This is not a talk about syntax. The PyMC one just leaves the story <span class="grad">out in the open</span>.
</div>

<!--
Same model, three ways to write it. On the left, lme4 — what most of you use. In the middle, brms, which many of you have touched: same formula syntax, but it samples the Bayesian version under the hood. On the right, the PyMC version, spelled out.

I'm not here to sell you a language. If you take one thing home, it should transfer to whichever of these you already use — and it does; brms gives you every check I'll show, and I'll put the R commands on the last slide.

The only reason I show the PyMC lines is that they make the story explicit. theta is the participant's ability. mu is the population average, sigma is how much people differ, z is where this particular participant sits. Then b is the condition effect. Every symbol is one arrow of the story. Nothing is hidden — and that's the whole point of the next forty minutes.
-->

---

## "Already believes"

<div class="mt-6 text-xl">Every line of that model is an <span class="grad">assumption</span>:</div>

<div class="grid grid-cols-2 gap-4 mt-6 text-lg">
  <div v-click class="card">participants come from one shared population</div>
  <div v-click class="card">a participant has one ability, stable across sessions</div>
  <div v-click class="card">the condition shifts everyone by the same amount</div>
  <div v-click class="card">trials within a session are exchangeable coin flips</div>
</div>

<div v-click class="mt-8 text-xl text-gray-300">
Frequentist software makes these for you, silently. A Bayesian analysis makes you <span class="text-white">say them out loud</span> — and then lets you <span class="text-white">check every one</span>.
</div>

<!--
Look at what that one-line model already commits you to. Participants come from a single shared population — not two subgroups, one population. Each participant has one stable ability that doesn't drift across sessions. The condition moves everyone by the same amount — no interaction with person. And trials within a session are exchangeable, like flips of one coin.

Some of these are fine. At least one of them — "one stable ability across sessions" — is a genuine empirical claim that could be false, and if it's false it changes your standard errors and your conclusions. The frequentist fit made that assumption for you and didn't mention it.

The Bayesian workflow's first gift is just this: it forces the assumptions into the open. Its second gift, which is the rest of the talk, is that once they're written down, every single one becomes checkable. Let's go level by level.
-->

---
layout: section
---

<div class="tag">Part 2</div>

# Priors: the part you can see

<!--
We start where the story starts: before any data.
-->

---

## Priors are the assumptions you get to look at

<div class="mt-8 text-xl">
A prior says what values a parameter could plausibly take <em>before</em> you see data.
</div>

<div v-click class="mt-8 text-xl text-gray-300">
People treat that as the scary part of Bayes. It's the opposite: it's the one modelling assumption you can <span class="grad">simulate and inspect</span> before you've spent a single participant.
</div>

<div v-click class="mt-8 text-lg card">
Pick priors, simulate fake datasets from them, and look. If the fake data is absurd, your model believes something absurd. Fix it <span class="text-white">now</span>, for free.
</div>

<!--
A prior is just a statement about what a parameter could be before the data arrives. "The population's average accuracy is probably somewhere sensible, not exactly fifty percent and not exactly a hundred." That's a prior.

Priors have a bad reputation — "isn't that subjective, aren't you putting your thumb on the scale." But here's the thing nobody tells you: the prior is the one assumption in your entire model that you can fully inspect before collecting data. You draw parameter values from the prior, push them through the model, and generate fake datasets. Then you look at them. This is called a prior predictive check, and it costs nothing — no participants, no data.

If the fake datasets look insane, your model believes something insane, and you just found out on day zero instead of at review. Let me show you what that looks like.
-->

---

## What the defaults claim

<div class="grid grid-cols-2 gap-6 mt-4">
<div>
<img src="/fig02_prior_absurd.png" class="w-full" />
<div class="text-center text-gray-400 mt-1">a "flat, uninformative" prior</div>
</div>
<div v-click class="flex flex-col justify-center">
<div class="text-xl">A Normal(0, 10) on the logit scale looks harmless.</div>
<div class="mt-4 text-xl text-gray-300">Simulated, it says: most sessions score <span class="grad">either 0 or 100 out of 100</span>, almost none in between.</div>
<div class="mt-4 text-lg text-gray-400">No psychologist believes that. But the software would have used it without a word.</div>
</div>
</div>

<!--
Here's a prior people reach for when they want to be "uninformative": a Normal with standard deviation ten on the logit scale. Sounds humble — wide, agnostic, letting the data speak.

Now simulate from it. This is a rootogram: for each possible number correct out of a hundred, how many sessions the prior expects to see there, before any data. Two spikes: almost everything is piled at zero and at a hundred. This prior sincerely believes that most sessions are either all wrong or all right, and hardly any land in between.

That's not humble, it's absurd — no task in this department produces that. And "uninformative" priors are full of this: on the logit scale, wide is not the same as vague. The important thing is you can SEE it here, in ten seconds, before running a single subject. Maximum likelihood places no prior at all — an implicit flat one, which on the logit scale runs toward this same U-shape — and it never shows you the consequence.
-->

---

## What a sensible prior claims

<div class="grid grid-cols-2 gap-6 mt-4">
<div>
<img src="/fig03_prior_sensible.png" class="w-full" />
<div class="text-center text-gray-400 mt-1">a weakly-informative prior</div>
</div>
<div v-click class="flex flex-col justify-center">
<div class="text-xl">Normal(0, 1.5): every count from 0 to 100 about equally plausible.</div>
<div class="mt-4 text-xl text-gray-300">Wide, <span class="grad">nothing ruled out, nothing favoured</span>.</div>
<div class="mt-4 text-lg text-gray-400">Nothing controversial. Just a prior that has met a human before.</div>
</div>
</div>

<!--
Same model, one change: standard deviation one-point-five instead of ten. Simulate again, and now the prior predictive is flat: every number correct, from zero to a hundred, about equally plausible. Nothing ruled out, nothing favoured.

This is what "weakly informative" should mean. It hasn't decided your result — the data will move it easily. It has just stopped insisting on the physically ridiculous.

And notice the move: I didn't argue about priors in the abstract, I simulated from them and looked at the consequence in the units I care about — accuracy. That's the whole discipline. You never have to have a philosophical fight about priors. You draw fake data and ask "does this look like my field." That question anyone in this room can answer.
-->

---

## Simulate before you collect

<div class="mt-8 text-2xl">
The prior predictive is a <span class="grad">power analysis you can actually believe</span>.
</div>

<div class="grid grid-cols-3 gap-4 mt-10 text-lg">
  <div v-click class="card">Set the effect you'd care about</div>
  <div v-click class="card">Simulate the study from your model, many times</div>
  <div v-click class="card">See how often you'd recover it — before running anyone</div>
</div>

<div v-click class="mt-10 text-xl text-gray-300">
Same machinery, run forward. Design is just the workflow, before the data.
</div>

<!--
One more thing this buys you, and then we'll sample. Once you can simulate data from your model, you can do design. Set the smallest effect you'd care about, plug it in, and simulate the entire study — not once, but a thousand times. Ask: with this many participants and this many trials, how often do I actually recover the effect? How wide are my intervals?

That's a power analysis, but not the kind from a lookup table with assumptions you can't see. It's a power analysis run through your actual model, with your actual design and your actual priors. If the answer is "you'd miss this effect half the time," you learn it before you've paid a single participant.

This is the same forward simulation we just did with priors. Design, in this framing, isn't a separate ritual — it's the workflow run before the data instead of after. Okay: let's get some data and sample.
-->

---
layout: section
---

<div class="tag">Part 3</div>

# The posterior is not a number

<!--
Now we sample, and I want to fight the single most common misreading of a Bayesian result.
-->

---

## A distribution over everything, and it recovered what we planted

<img src="/fig04_posterior_truth.png" class="w-full mt-4" />

<div v-click class="mt-4 text-xl text-gray-300">
The dashed lines are the <span class="text-white">true values</span> (synthetic data, so we know them). The posterior isn't a point estimate with an error bar. It's a <span class="grad">joint distribution</span> over every unknown in the story.
</div>

<!--
Here's the posterior. Three panels: the population mean, the condition effect, the between-participant spread. Each is a full distribution — that's the posterior.

Because I generated this data myself, I know the true values, and they're the dashed lines. Notice they land inside each distribution — on this one dataset, the model recovered what generated it. One recovery isn't proof a method always finds the truth; the real, repeatable check is the calibration section coming up. But throughout I'll keep using synthetic data for this reason: it's the only setting where you can grade the answer, because it's the only setting where you know it. Real data never grades you.

But the deeper point is what the posterior IS. It is not a coefficient plus a standard error. It's a joint distribution over every unknown in the model at once — the population parameters and all forty participants' abilities, together, with all their correlations. The table your software prints is a few one-number summaries of this object. The object is the result. And once you hold the whole object, two things you were taught as separate ideas turn out to be the same thing.
-->

---

## Partial pooling, when you know least

<img src="/fig05a_shrinkage_20trials.png" class="h-96 mx-auto" />

<div v-click class="mt-2 text-xl text-gray-300">
Red = each participant's raw accuracy. Blue = the model's estimate. Every arrow points <span class="grad">toward the population</span> — furthest when the data is thinnest.
</div>

<!--
This is the first one: shrinkage, also called partial pooling, and it IS the random effect — not an add-on, the thing itself.

I sampled the model with just the first twenty trials per participant, so the raw estimates are noisy. Red dots are each person's raw accuracy from those twenty trials. Blue dots are the model's estimate for the same person. Every blue dot has moved toward the yellow line, the population mean — and the arrows are longest for the people out at the extremes.

Why? Because someone who scored ninety percent on twenty trials — the model reasons, correctly, that extreme raw scores are usually a lucky or unlucky sample from a more moderate ability, and it pulls them back toward the crowd. That is what "borrowing strength" means concretely. It's not a correction bolted on; it falls straight out of the story — the participant was drawn from a population, so the population is evidence about the participant. When you write the random intercept, this is what you asked for.
-->

---

## Shrinkage decays as the data arrive

<img src="/fig05b_shrinkage_progression.png" class="w-full mt-6" />

<div v-click class="mt-4 text-xl text-gray-300">
20 trials, 100, two sessions, four. As each participant's own data accumulates, the population matters less. <span class="grad">That is what a random effect is.</span>
</div>

<!--
And shrinkage isn't a fixed fudge factor — it's adaptive, and this is the panel that shows it. Left to right: twenty trials, a hundred trials, two sessions, four sessions. The shrinkage percentage in each title is falling.

With twenty trials the model leans hard on the population, because each person's own data is weak and the population is the better guide. By four sessions, each participant has hundreds of their own trials, the population has little left to add, and the arrows almost vanish — the estimates sit essentially on the raw values.

So the random effect automatically weights each participant's own data against the crowd, in proportion to how much data that participant has. When you know little about someone, you lean on the population; as you learn more, you trust them. No threshold, no switch — it's continuous, and it's the correct amount, given the model. This is the single most useful thing hierarchical models do, and most people fit them without ever seeing it happen.
-->

---

## Credible vs confidence: two questions

<img src="/fig06_ci_vs_credible.png" class="h-90 mx-auto" />

<div v-click class="mt-2 text-lg text-gray-300">
Often close in numbers. But one asks <span class="grad">"where is the truth, given this data?"</span> — and it makes a <span class="text-white">probability claim you can test</span>. (A confidence interval's coverage is testable too — the coverage plots that follow are exactly that test.)
</div>

<!--
The second idea that falls out for free is the interval. Here, for a dozen participants, red is a classic Wilson confidence interval computed from each person's data alone; blue is the ninety-percent posterior interval from the hierarchical model.

Two things. First, the blue intervals are tighter and pulled toward the center — that's the pooling again, borrowing strength. Second, and this is the conceptual point: these answer different questions. The confidence interval is a statement about a procedure — "if I repeated this experiment many times, ninety percent of the intervals I'd build this way would cover the fixed true value." It is not a statement about this interval. The credible interval says the thing you actually want: "given this data and this model, there's a ninety percent probability the parameter is in here."

I'm not going to tell you confidence intervals are wrong or that you should never use one. They're often numerically close, and Kruschke has written the careful version of this. My point is narrower and it sets up the rest of the talk: the credible interval makes a promise you can actually put to the test. When it says ninety percent, you can go check whether it's right ninety percent of the time. So let's check.
-->

---
layout: section
---

<div class="tag">Part 4</div>

# Checking, and expanding

<!--
The model sampled. That is not the same as the model being any good. Sampling is easy; the checks are where the work is.
-->

---

## Simulate replications, compare to what you saw

<img src="/fig07_ppc_dist.png" class="w-full mt-2" />

<div v-click class="mt-3 text-lg text-gray-300">
The sampled model can generate fake studies (bands = its predictions, dots = your data). On the left, the model that assumes one stable ability per person. Its predictions are <span class="grad">too narrow</span> — the real data has more extreme sessions than it can produce.
</div>

<!--
Same forward simulation as the prior predictive, but now from the sampled model: draw parameters from the posterior, generate a full fake study, do it thousands of times. This is a posterior predictive check, and it's a rootogram — for each possible number-correct, the band is how often the model predicts it, the dot is how often it actually happened.

Left panel is the model we've been sampling: one stable ability per participant, sessions are just more trials from it. Look at the tails — the dots sit outside the bands out at the low and high ends. The real data has more very-bad and very-good sessions than this model can generate. It's underdispersed: too confident, too narrow.

Right panel — hold that thought, I'll come back to it. The move here is the important one: a model that sampled fine numerically, converged cleanly, gave you a tidy coefficient table — is visibly failing to reproduce the data it was trained on. You would never know from the summary table. You only know because you made it generate data and you looked.
-->

---

## When it says 90%, is it right 90%?

<img src="/fig08_coverage_binomial.png" class="h-90 mx-auto" />

<div v-click class="mt-2 text-lg text-gray-300">
Coverage, at every interval width at once. This model sits <span class="text-white">below the line</span> everywhere: its 90% intervals hold about 70% of sessions, its 50% about a third. <span class="grad">Over-confident</span>, with a receipt.
</div>

<!--
This is the promise from the interval slide, cashed out. The coverage plot asks, for every interval width at once: when the model claims an X percent interval, what fraction of the data actually falls inside? The flat dashed line at zero is a model keeping its promises exactly.

This model is below the line everywhere. Its ninety-percent intervals contain about seventy percent of the sessions. Its fifty-percent intervals contain about a third. It is systematically over-confident — it promises more certainty than it delivers — and the little p-value in the corner is a formal test that this deviation is real, not noise.

This is the single most useful plot in the workflow, and it's the one people skip. It turns "I have a bad feeling about my standard errors" into a measured, quantitative statement: at the ninety-percent level, this model is off by almost twenty points of coverage. And crucially it tells you the DIRECTION — over-confident, not under — which tells you what to fix.
-->

---

## The same thing, sharper: PIT

<img src="/fig09_pit_ecdf.png" class="h-90 mx-auto" />

<div v-click class="mt-2 text-lg text-gray-300">
A calibrated model's residuals are uniform; this curve bows away from flat. The dip means the data lands in the <span class="grad">tails</span> of the model's predictions far more often than it should.
</div>

<!--
Same diagnosis, a sharper instrument — this is the PIT, the probability integral transform. For each observation you ask: where in the model's predictive distribution did the real value land? If the model is calibrated, those positions are uniform — every quantile equally likely — and this difference-from-uniform curve is flat.

It isn't flat; it bows. And the shape tells you the failure mode. This downward bow means real observations land in the extreme tails of the predictions much more often than a calibrated model allows — the data is more spread out than the model expects. That's the same underdispersion the rootogram showed and the same over-confidence the coverage plot measured. Three views, one diagnosis, and they agree because they're all reading the same misfit.

I'm dwelling on calibration because it's the check that generalizes. Whatever you're modelling — reaction times, counts, choices — the question "when my model says ninety percent, is it right ninety percent of the time" is always available, and ArviZ, or bayesplot in R, computes it in one line for any data type.
-->

---

## The story had no line for sessions

<div class="mt-6 text-xl">Our story said: participant, then trials. It skipped a level.</div>

<div class="grid grid-cols-2 gap-6 mt-8">
<div v-click class="card">
<div class="tag">what we assumed</div>
<div class="mt-2 font-mono text-sm">y ~ Binomial(n, p_participant)</div>
<div class="mt-2 text-gray-300">one ability, sessions are just more trials</div>
</div>
<div v-click class="card">
<div class="tag">what we add</div>
<div class="mt-2 font-mono text-sm">p_session ~ Beta(p_participant, k)<br>y ~ Binomial(n, p_session)</div>
<div class="mt-2 text-gray-300">each session wobbles around the person</div>
</div>
</div>

<div v-click class="mt-6 text-lg text-gray-400">
In brms, one word: <span class="font-mono text-white">family = beta_binomial()</span>. The failed check told us <em>which</em> word.
</div>

<!--
So what do we do about a failed check? We don't tweak priors and re-run hoping the warning goes away. The check told us something specific: the data varies more than one-ability-per-person allows. That points at a missing level in the story.

Our story went participant, then trials — it had no line for the session. It assumed every session shares one fixed ability. But that was exactly the assumption we flagged on slide five as an empirical claim that might be false. The coverage plot is the evidence that it IS false. People's accuracy genuinely moves from session to session — sleep, practice, attention — and the model had nowhere to put that.

So we add the level. Each session gets its own accuracy, drawn around the participant's mean, with a concentration parameter kappa controlling how much it wobbles. That's the beta-binomial. In brms it is literally one word: change binomial to beta binomial. The important part is that we didn't guess our way there — the failed check named the fix.
-->

---

## The expanded model keeps its promise

<img src="/fig10_coverage_betabinomial.png" class="h-90 mx-auto" />

<div v-click class="mt-2 text-lg text-gray-300">
Same coverage plot, session-aware model: <span class="grad">back on the line</span> — if anything a touch conservative, which is the safe way to be wrong. Its recovered between-session spread matches the truth we set. Failing was where the model got better.
</div>

<!--
Here's the coverage plot for the expanded, session-aware model. Back on the line — at every width, its intervals now hold at least what they promise; in-sample it sits a hair above the line, so if anything it's slightly cautious, which is the direction you want to err. (The leave-one-out version the workshop runs sits right on it.) Go back one panel in your memory to the rootogram's right side: the dots sat inside the bands there too. And on the synthetic data, this model recovers the true between-session variability I set when I generated it — it found the level the first model was blind to.

I want to name the shape of what just happened, because it's the whole workflow in one arc. We wrote a model. We sampled it. We made it generate data and it failed a specific, measurable check. The failure pointed at a specific missing piece of the story. We added that piece — one word — and the check passed. The failure wasn't a setback; it was the most informative thing that happened, because it told us precisely what the data knew that our model didn't.

That's the loop. And it raises the obvious question — when do you stop looping?
-->

---
layout: section
---

<div class="tag">Part 5</div>

# When do you stop?

---

## Comparison is one input, not a verdict

<img src="/fig11_compare_panel.png" class="w-full mt-2" />

<div v-click class="mt-4 text-lg text-gray-300">
Cross-validation says the session-aware model predicts far better. Good. But the rootogram and the coverage plot said the same thing <span class="grad">for a reason you can point at</span> — that's the evidence. The number is a summary of it.
</div>

<!--
There is a number for "which model predicts better" — it's cross-validation, ELPD, and here it strongly prefers the session-aware model. The bar is the difference; it's far from zero and far from its own error bar.

But I want to be careful, especially in this room. That number is not the verdict. It agrees with the rootogram and the coverage plot, and the agreement is the point — three different checks, reading the data three different ways, all saying "you were missing the session level." THAT convergence is the evidence. The ELPD is a one-number summary of it.

I say this pointedly because the tempting move is to reduce model choice to a magic number: is the ELPD difference more than some multiple of its standard error. Resist that magic-number mentality. There's careful published work on the limits of cross-validation for choosing among models when every model is wrong — which is always. Cross-validation asks "which of these predicts held-out data better," and that is a genuinely different question from "which of these is true," or even "which should I use for my actual scientific purpose." Lean on it as one input, alongside the checks and alongside what the models mean. Never as an oracle.
-->

---

## No single number closes the loop

<div class="grid grid-cols-3 gap-4 mt-10 text-center text-lg">
  <div class="card">a p-value</div>
  <div class="card">a Bayes factor</div>
  <div class="card">an ELPD difference</div>
</div>

<div v-click class="mt-10 text-2xl text-center">
Each is a <span class="grad">summary</span> of one question. None of them knows what your model is <em>for</em>.
</div>

<div v-click class="mt-8 text-xl text-gray-300 text-center">
When to stop is a judgment about purpose — and it's yours, not the number's.
</div>

<!--
So when do you stop? Not when a number crosses a line. A p-value, a Bayes factor, an ELPD difference — each compresses one specific question into one scalar, and none of them knows what you're going to do with the model.

A model good enough to estimate a group-level effect might be nowhere near good enough to predict an individual's next session. A model that's well-calibrated for your data might rest on an assumption that breaks the moment you generalize to a new population. "Good enough" is a statement about purpose, and purpose lives in your head, not in the data.

What the workflow gives you is not a stopping rule. It gives you a set of honest instruments — prior checks, calibration, coverage, comparison — that tell you where the model is failing and by how much, so that when you decide to stop, you're deciding with your eyes open. The judgment stays yours. The workflow just makes sure it's an informed one. That's the whole method: a loop you run with instruments, until the model is good enough for what you need — and you're the one who defines enough.
-->

---

## The arc

<div class="flex flex-wrap gap-2 mt-10 text-sm items-center">
  <div class="card">story</div><span>&rarr;</span>
  <div class="card">priors</div><span>&rarr;</span>
  <div class="card">prior predictive</div><span>&rarr;</span>
  <div class="card">sample</div><span>&rarr;</span>
  <div class="card">posterior predictive</div><span>&rarr;</span>
  <div class="card">coverage</div><span>&rarr;</span>
  <div class="card grad font-bold">expand</div><span>&#8635;</span>
</div>

<div class="mt-10 text-xl text-gray-300">
You already do the first two out of habit. The rest is the same forward simulation, pointed at different questions.
</div>

<!--
Here's the whole thing on one slide. Write the story. Choose priors. Simulate from them and look — prior predictive. Sample. Simulate from the posterior and compare to reality — posterior predictive. Measure the promises — coverage and calibration. Where it fails, expand, and go around again.

You already do the first two steps every time you specify a model, you just don't usually look at what you specified. Everything after "sample" is the same forward-simulation trick — generate data from the model — aimed at a different question each time. That's the entire toolkit, and it's why it transfers: it's not a bag of tests, it's one move applied repeatedly.

Now — I promised you at the start there'd be a twist, and it's the reason the workshop this afternoon exists. What happens when you hand this exact problem not to a person, but to an AI coding assistant?
-->

---
layout: section
---

<div class="tag">Part 6</div>

# What happens when you hand this to an AI

---

## Same data, a student's prompt

<div class="card mt-8 text-lg italic">
"I ran a study: 40 participants, two conditions, five sessions, 100 trials each. Compute each participant's accuracy with an interval, test whether the conditions differ, and write me a short report for lab meeting."
</div>

<div v-click class="mt-8 text-xl text-gray-300">
The prompt a second-year would type. The assistant answered the question <span class="grad">as asked</span> — which is exactly the problem, and exactly what a rushed human does too.
</div>

<!--
I gave a coding assistant — Claude Code, running on a mid-size model — the exact synthetic dataset from this talk, with the prompt a second-year student would actually type. Not "do a rigorous Bayesian workflow." Just: compute accuracies, test the conditions, write it up for lab meeting.

And it did that. Competently. It answered the question exactly as asked. Which is the whole problem — because "the question as asked" quietly skips most of the workflow you just watched. It answered the literal question and stopped, which is precisely what a capable, rushed human does at eleven pm before lab meeting.

I want to show you the before and after, because the fix is interesting and it's not "use a bigger model."
-->

---

## Before / after

<div class="grid grid-cols-2 gap-6 mt-6 text-sm">
<div class="card">
<div class="tag">on its own</div>
<ul class="mt-2 space-y-1 text-gray-300">
<li>built a plain binomial mixed model — one ability per person, sessions pooled as trials</li>
<li>ran a prior predictive check, a prior-sensitivity analysis, reported partial-pooled estimates with intervals and honest caveats</li>
<li class="text-red-300">never modelled the session-to-session wobble</li>
<li class="text-red-300">checked the model by eye (an ECDF overlay), not calibration</li>
</ul>
</div>
<div class="card">
<div class="tag">with the workflow written down as a "skill"</div>
<ul class="mt-2 space-y-1 text-gray-300">
<li>measured the overdispersion (~2.6× binomial), reached for a session-level term, found it unstable, switched to a <span class="text-white">beta-binomial</span> — the model we just built</li>
<li>ran the <span class="text-white">coverage / PIT check</span> and cross-validation, then reviewed its own work and caught its first draft glossing them — and rebuilt</li>
<li>followed the workflow's reporting layout without being asked</li>
</ul>
</div>
</div>

<div v-click class="mt-6 text-lg text-gray-400">
No scores, no leaderboard. Same model, same data you now understand — just what each run did.
</div>

<!--
Left, on its own. It built a plain binomial mixed model — one ability per participant, sessions pooled together as more trials. And it was genuinely careful: it ran a prior predictive check, it ran a prior-sensitivity analysis, it reported partially-pooled estimates with credible intervals, it wrote sensible caveats. If a student handed me this, I'd be pleased. But it never modelled the session-to-session wobble — the exact thing this whole talk is about — and it checked its predictions by eye, with an ECDF overlay, never their calibration. It answered the question as asked, well, and stopped.

Right, same model, same data, now with the workflow installed as a skill — a file it reads before it starts. It measured the overdispersion, saw the sessions vary about two-and-a-half times more than binomial noise allows, and reached for a session-level term. That term turned out unstable, it noticed, and it switched to a beta-binomial — the model we built together twenty minutes ago. Then it ran the coverage and PIT check and cross-validation. And here's the part I didn't expect, which is the next slide.
-->

---

## What it took

<div class="mt-8 text-xl">The fix wasn't a smarter model. It was giving it the <span class="grad">workflow, written down</span> — the same arc from two slides ago, as a checklist it reads before it starts.</div>

<div class="grid grid-cols-2 gap-4 mt-8">
<div v-click class="card">
<div class="tag">surprise 1</div>
<div class="mt-2 text-gray-300">The bare assistant was already good — prior predictive, sensitivity, partial pooling, all unprompted. The skill didn't rescue a lazy agent; it supplied the two domain moves a <em>careful</em> one still skipped: model the session level, and check calibration.</div>
</div>
<div v-click class="card">
<div class="tag">surprise 2</div>
<div class="mt-2 text-gray-300">With the workflow, it ran its own adversarial review before calling the job done — and that review caught its <em>first write-up understating the diagnostics it had just computed</em>. It accepted the criticism, rebuilt to the beta-binomial, and re-checked. It caught itself.</div>
</div>
</div>

<!--
What did it take? Not a bigger model — it was the same model in both runs. It took the workflow, written down: the arc from a few slides ago, as a checklist the assistant reads before it touches the data. That's all a "skill" is.

Two things surprised me, and they're the honest version of this. First: the assistant that didn't have the workflow loaded was already careful — prior predictive, sensitivity analysis, partial pooling, all on its own. But careful, on its own terms, still meant session-blind and unchecked for calibration. Having the workflow as an active skill is what turned careful-but-incomplete into the whole loop.

Second, and this is the real one. With the workflow, before it called the job done, it ran its own adversarial review of its work — and that review caught its own first write-up understating the very diagnostics it had just computed: a cross-validation that was actually unreliable, a calibration it had softened to "mild" that wasn't. It took the criticism, rebuilt to the beta-binomial, and re-checked — and that version is honestly calibrated. It caught itself. That is the whole thesis, happening inside the machine: the workflow doesn't make the model right, it makes the analyst, human or not, check hard enough to find where it's wrong. This afternoon, that's your job: this data, its run in front of you, and the questions it should have asked.
-->

---

## This afternoon

<div class="mt-10 text-2xl">
The workshop picks up right here, hands-on.
</div>

<div class="mt-8 text-xl text-gray-300">
You build both models on this data, watch the checks catch the session-blind one, and <span class="grad">critique the AI's run yourselves</span> — no coding required, just reading plots and asking the questions it didn't.
</div>

<div class="mt-10 text-lg text-gray-400">Everything runs in the browser via Google Colab. Nothing to install. R users welcome — it all transfers to brms.</div>

<!--
This afternoon we do it with your hands on it. Everything runs in Google Colab, in the browser, nothing to install, and no Python assumed — the notebooks are pre-written and your job is to run them and change things.

You'll build both models on this same data, watch the session-blind one fail the coverage check in real time, and then — this is the part I'm most curious about — you'll critique the AI assistant's run yourselves. I'll play back what it did, and the room's job is to catch what it got wrong. Not at the code level — at the level of the questions: did it check what it should have, and where would you have pushed back. No coding required for that part; if you can read a coverage plot, and after this talk you can, you can do it.

R users, you are genuinely welcome — every check I showed has a brms and bayesplot equivalent, and they're on the next slide.
-->

---
layout: center
class: text-center
---

# Thank you

<div class="mt-6 text-xl text-gray-300">The workflow is a loop you run with instruments,<br>until the model is good enough for what <em>you</em> need.</div>

<div class="mt-10 text-gray-400 text-sm font-mono">github.com/AlexAndorra/princeton-bayes-2026 &middot; learnbayesstats.com</div>

<div class="mt-8 text-sm text-gray-500">
R: brms <span class="font-mono">beta_binomial()</span> &middot; <span class="font-mono">sample_prior="only"</span> &middot; <span class="font-mono">pp_check(type="rootogram")</span> &middot; bayesplot <span class="font-mono">ppc_pit_ecdf</span> &middot; <span class="font-mono">loo_compare()</span>
</div>

<!--
That's the talk. The one sentence to keep: the Bayesian workflow isn't a test you pass, it's a loop you run with honest instruments until the model is good enough for what you actually need — and you're the one who defines enough.

Everything is in the repo — the slides, the data, the notebook, and the AI runs, transcripts and all. The podcast is where I argue about this stuff every couple of weeks with people who know more than I do.

And for the R users, the bottom line is your Rosetta stone: prior predictive is sample-prior-only, the rootogram and calibration are pp-check and ppc-pit-ecdf, comparison is loo-compare. Same workflow, same instruments, your language. I'd love to take questions — and to see you this afternoon.
-->
