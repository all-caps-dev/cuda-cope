# CUDA Cope

Benchmarks for running large local models on one 16 GB consumer NVIDIA card,
published with the failures included.

The scope is narrow on purpose: one **16 GB card**. Numbers from a bigger card
do not transfer down, so this repo measures what 16 GB actually does, names the
quant and the driver, and publishes the runs that broke as well as the ones that
worked. For 24 GB and multi-card serving recipes, see
[club-3090](https://github.com/noonghunna/club-3090).

## Why this exists

Most local-model benchmarks are marketing. They publish wins, omit the
configuration that produced them, and never say which CUDA build was loaded. A
corpus that only contains successes tells you nothing about your own box.

Three rules keep this one honest:

1. **Every number names its config.** Quant, context depth, offload setting,
   driver, CUDA toolkit, llama.cpp commit. A number without those is a rumour.
2. **Failures are results.** An out-of-memory at a given depth is the fit ceiling,
   which is the most useful thing in the table.
3. **Speed without a quality pass is how you ship a broken quant.** A low-bit
   quant on the wrong runtime can load fine, run fast, and emit nonsense.

## The protocol

See [PROTOCOL.md](PROTOCOL.md). In one line: one hypothesis with a number in it,
one change, three runs, record to CSV, decide, and a quality pass on every quant
change.

## Layout

| Path | What it holds |
|---|---|
| `PROTOCOL.md` | the measurement loop, and what counts as a result |
| `HARDWARE.md` | the reference box, measured rather than quoted from a spec sheet |
| `harness/probe.py` | graded quality probe: counting, arithmetic, coherence, JSON |
| `benches/` | one file per run, dated, config stated at the top |
| `prompts/` | the graded prompt sets, with expected answers |

## Status

Early. The first real result is in
[`benches/2026-09-22-nail-iq3.md`](benches/2026-09-22-nail-iq3.md), and it is a
negative one: the quant everyone would suspect turned out to be fine, and the
failure was somewhere else entirely.

## License

Code: Apache-2.0, see [LICENSE](LICENSE) and [NOTICE](NOTICE). Write-ups and
results: CC BY 4.0, see [CONTENT-LICENSE.md](CONTENT-LICENSE.md). Use them
freely; credit **cuda-cope** and link the bench file you took the number from.
