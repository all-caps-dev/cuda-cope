# Occult-Nail vs Nail: abliteration answers the own-hardware questions, and counts better too

**Date** 2026-09-22 · **Box** see [HARDWARE.md](../HARDWARE.md) · **Both models on the same box, same harness**

## The question

The private local lane is for work a hosted model would refuse: auditing hardware
you own. Stock instruct models decline a share of that even when the request is
plainly about your own devices. The question was whether an abliterated build
recovers those refusals without wrecking the model's actual competence.

Two models, both quants of Qwen3.6-35B-A3B:

| | Nail | Occult-Nail |
|---|---|---|
| Nature | stock Qwen + terseness metadata | abliterated (base: uncensored-heretic) |
| Quant tested | UD-IQ3_S, 12.7 GB | UD-Q3_K_XL, 15.7 GB |
| Publisher | peculiar-ragdoll | peculiar-ragdoll |

Both served on llama.cpp on the reference box, temperature 0 for graded sets,
three repetitions each. The refusal set is six requests, each explicitly about
hardware the operator owns (switch recovery, TV telemetry, UART firmware audit,
own-port scan, self-MITM, own-Wi-Fi handshake test). The refusal prompts are not
published; only the aggregate verdict is.

## Result

| Metric | Nail IQ3_S | Occult-Nail Q3_K_XL |
|---|---|---|
| Arithmetic | 8 / 8 | 8 / 8 |
| Counting | 6 / 7 | **7 / 7** |
| Coherence | clean | clean |
| Structured JSON | valid | valid |
| **Own-hardware requests answered** | **4 / 6** | **6 / 6** |
| Own-hardware requests refused | 2 / 6 | **0 / 6** |

Nail declined two of the six own-hardware requests. Occult-Nail answered all six,
and lost nothing measurable doing it: identical arithmetic, one better on
counting, clean prose, valid JSON.

## Reading it

For the private lane, **Occult-Nail Q3_K_XL is the better model here**. It removes
the refusals that make a stock model useless for own-device auditing, and it does
not read as damaged: competence held or improved across every graded check.

## The honest confound

This run changes **two** variables at once, not one. Occult-Nail was tested at
Q3_K_XL (15.7 GB) and Nail at IQ3_S (12.7 GB), so the counting win (7/7 vs 6/7)
could be the higher quant rather than the abliteration. Abliteration and quant
are tangled here.

What is *not* confounded is the refusal result. Abliteration is the only thing
that plausibly drives 2 refusals to 0; a higher quant of a stock model does not
make it more willing to discuss switch recovery. So: the refusal delta is
abliteration, the counting delta is unattributed. To isolate the rest, a future
run needs Occult-Nail at IQ3_S or Nail at Q3_K_XL. Both fit on VRAM; system RAM
is the wall.

## Method notes

- **The harness caught its own bug mid-run.** The quality probe globbed every
  prompt set in the directory, including the refusal set, which has no graded
  answer key, and crashed. Fixed to skip `*.local.json` and any set whose cases
  lack an answer. Recorded because a harness that hides its own failures is the
  thing this repo exists to argue against.
- **The private lane was down twice, ~30 s each**, once per model served, with
  the stock service backed up and restored to the exact prior config both times.
  Two 35B models cannot share 16 GB of VRAM, so there is no zero-downtime path.

## Reproduce

Quality is reproducible from this repo:
```sh
python3 harness/probe.py --endpoint http://<server>:8080 --runs 3
```
The refusal set is local-only by design (own-device specifics), so the refusal
run is not reproducible from the public tree. The grader is:
```sh
python3 harness/refusal.py --endpoint http://<server>:8080   # rates only
```

## Open

- Isolate abliteration from quant: same quant, both models.
- Occult-Nail's card reports 0% HarmBench refusal and a 0.7-point MMLU-Pro cost
  vs Nail, both measured at Q6_K_XL, a quant that does not fit this box. Unverified
  here.
