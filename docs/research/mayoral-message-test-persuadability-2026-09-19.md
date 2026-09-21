# Mainstreet Sept 2026 message test — an upper bound on persuadability

The Mainstreet City of Toronto September 2026 survey (field Sept 14–17, IVR,
n=1,000; source `mainstreet_2026-09-14_toronto_public.pdf`) carries a
**randomised split-sample message experiment** alongside the horse race. It is
not a second poll: respondents were split into two treatment arms, each heard a
single one-sided argument, and were then re-asked their vote. Because the arms
are randomised within one sample, the A-vs-B contrast is causal within the poll.

## Observed results (source PDF)

Un-messaged baseline (decided), for reference: **Chow 45.8 / Bradford 37.7**
(margin **+8.1** Chow); all-voters **Chow 38.1 / Bradford 31.4**.

**Arm A — pro-Chow argument** (crime down while hiring continued; TTC safety
team combining enforcement and prevention), unweighted n=487:
- All voters in arm: Chow 39.4 / Bradford 29.2 / Alexander 8.1 / Undecided 16.6
- Decided and leaning: **Chow 47.2 / Bradford 35.0** (margin **+12.2** Chow)

**Arm B — pro-Bradford argument** (clearer accountability; visible police,
uniformed officers in subway stations, platform-edge doors, mayor on the Police
Service Board), unweighted n=513:
- All voters in arm: Chow 31.5 / Bradford 38.8 / Alexander 7.6 / Undecided 16.1
- Decided and leaning: **Chow 37.5 / Bradford 46.3** (margin **−8.8** Chow, i.e.
  Bradford +8.8)

## What it shows

The decided Chow–Bradford margin spans **+12.2 (arm A) to −8.8 (arm B)** — a
**~21-point swing** between the two best one-sided framings, and the pro-Bradford
argument alone **flips the lead** (from the +8.1 baseline to −8.8, a ~17-point
move). Both campaigns have a live persuasion path; the pro-Bradford message
moves more, consistent with Bradford's larger headroom (far fewer "definitely
not" voters — see the fundamentals note in the methodology doc).

## Why it is an upper bound, and stays out of the average

This is a **ceiling on persuadability, not a forecast input**:
- one-sided message with **no rebuttal**, whereas a real campaign is two-sided;
- measured **immediately** after exposure (no decay, no competing information);
- the pollster's **chosen strongest** framing for each side.

It is therefore **not ingested as a vote-intention reading**: only the
un-messaged `mainstreet_20260914_mayor_all` / `_decided` readings enter the
corpus (both `general_vote_intention`). The message-test toplines are recorded
here as research context only and must never enter the polling average.

## Bearing on the forecast

It **bounds** the campaign-drift component (2) rather than the direction: it
shows the decided race *can* move on the order of ~15–20 points under a
favourable one-sided push, which is why drift is not collapsed toward zero
despite five stable polls — but because both sides can move their own way, it
adds no directional bias. It independently corroborates component (3)'s premise
(the race has soft, persuadable vote), without changing any parameter. No model
value was tuned to these numbers.
