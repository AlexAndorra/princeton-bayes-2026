I'm a second-year PhD student in psychology. I ran a repeated-measures study: 40 participants
did a task in two conditions ("standard" and "hard") across 5 sessions, 100 trials per session
per condition. `data/sessions.csv` has one row per participant × session × condition with
`n_correct` out of `n_trials`; `data/trials.csv` has the trial-level data. The codebook is in
`data/README.md`.

Can you:
1. compute each participant's accuracy with a 95% interval,
2. test whether accuracy differs between the two conditions, and
3. write me a short report (a markdown file) with a figure or two I can show at lab meeting?

Python is already set up in this folder — run things with `uv run python`. Save the report and
figures here.
