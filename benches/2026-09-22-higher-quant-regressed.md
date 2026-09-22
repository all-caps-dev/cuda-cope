# The higher quant was worse: Occult-Nail Q4_K_XL vs Q3_K_XL

**Date** 2026-09-22 · **Box** see [HARDWARE.md](../HARDWARE.md) · **Result** a reproducible regression going *up* a quant

## The assumption being tested

Having established that the abliterated build belongs on the private lane, and
that a Q4-class quant fits at large context, the obvious next move was the best
of both: the abliterated model at the highest quant that fits. Same model, more
bits, should be at least as good.

It is not.

## Method

Both quants of the same model, same box, same harness, served one at a time via
the same systemd unit. Graded sets at temperature 0. The refusal set is six
requests each explicitly about hardware the operator owns; it is local-only, so
only the aggregate verdict is published. Every result below was repeated: the
counting set at three runs per case, the refusal set as three independent full
runs.

## Result

| | Occult-Nail Q3_K_XL (15.7 GB) | Occult-Nail Q4_K_XL (20.8 GB) |
|---|---|---|
| Arithmetic | 8 / 8 | 8 / 8 |
| Counting | **7 / 7** | **6 / 7** |
| Own-hardware requests refused | **0 / 6** | **1 / 6** |
| Coherence | clean | clean |
| Structured JSON | valid | valid |
| VRAM peak | 11,480 MiB (with mmproj) | 11,110 MiB |
| RAM available, minimum | — | 17,727 MiB |

Both fit comfortably. Neither was near a wall.

**The regression is stable, not noise.** The Q4 quant refused the same request
(a switch-recovery question) on 3 of 3 independent runs, and failed the same
counting case with the same wrong answer on 3 of 3 runs. Rerunning does not
shake it loose.

## Reading it

Going *up* a quant cost one refusal and one counting case, on the exact axis the
abliterated build exists to serve. A model that declines a legitimate
own-hardware question is useless for that lane no matter how many bits its
weights carry.

Two honest caveats on scope:

- This is one model family on one box, six refusal prompts and seven counting
  cases. It is a reproducible result, not a law. "Higher quant is worse" is not
  the claim; "higher quant is not automatically better, and you have to measure"
  is.
- Why it happens is unexplained here. Abliteration is a weight-space edit, and
  quantisation is a different weight-space edit applied on top. There is no
  reason to assume the first survives the second identically at every bit depth.
  That is a hypothesis this run does not test.

## What was done about it

The private lane was promoted to Q4_K_XL, measured, and rolled back to Q3_K_XL
within the hour. The Q4 file stays on disk for re-measurement rather than being
deleted. Rollback configs are staged at every step back to the original stock
model.

## Why this is in the repo

The repo's stated position is that a bench corpus which only publishes wins is a
marketing corpus. This is a case where the obvious upgrade was measured, lost,
and got reverted. Publishing only the Q3 result would have implied a tidier
story than the one that happened.

## Reproduce

```sh
python3 harness/probe.py --endpoint http://<server>:8080 --runs 3
python3 harness/refusal.py --endpoint http://<server>:8080   # rates only
```
