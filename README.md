# CUDA Cope

Benchmarks for running large local models on one 16 GB consumer NVIDIA card,
published with the failures included.

CUDA Cope is based on [club-3090](https://github.com/noonghunna/club-3090) by
noonghunna, the community recipes for serving LLMs on 24 GB and multi-card RTX
setups. It takes the same approach down to the smaller card.

The scope is narrow on purpose: one **16 GB card**. Numbers from a bigger card
do not transfer down, so this repo measures what 16 GB actually does, names the
quant and the driver, and publishes the runs that broke as well as the ones that
worked. For 24 GB and multi-card serving recipes, use club-3090 itself.

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

Four results so far, all measured 2026-09-22 on the reference box in [HARDWARE.md](HARDWARE.md):

| Bench | Question | Answer |
|---|---|---|
| [nail-iq3](benches/2026-09-22-nail-iq3.md) | Is the IQ3_S quant damaged? | No. 8/8 arithmetic; the failure was somewhere else. |
| [occult-nail-vs-nail](benches/2026-09-22-occult-nail-vs-nail.md) | Does the abliterated build answer own-hardware questions the stock one refuses? | Yes: 6/6 answered vs 4/6. |
| [large-quant-large-context](benches/2026-09-22-large-quant-large-context.md) | Does a Q4 quant fit at large context on 16 GB? | Yes: Q4_K_S at 262k context, about 11 GB VRAM. |
| [higher-quant-regressed](benches/2026-09-22-higher-quant-regressed.md) | Is the higher quant better? | No. Q4_K_XL lost a counting case and refused one request that Q3_K_XL passed, 3 runs out of 3. |

### Earlier results (July 2026)

Before this repo, the same card was benched with
[localai-16gb-bench](https://github.com/ryanilano/localai-16gb-bench) (MIT), a throughput and fit
sweep for Qwen3.6 on llama.cpp. Its headline numbers, from the run notes in that repo:

- **35B-A3B MoE, UD-Q3_K_M:** fastest config in the sweep, about 58 tok/s generation at low depth,
  and it stayed up to about 255k context at about 6 GB VRAM with idle experts in system RAM.
- **27B dense, NEO-CODE IQ3_M:** about 40 tok/s, up to 80k context at about 15.4 GB VRAM.
- **27B dense, NEO-CODE IQ4_XS:** the context wall is the KV cache, not the weights. q8_0 KV caps
  near 16k; q4_0 KV reaches about 49k at about 15.8 GB, with no quality loss found on short prompts.
- **CUDA 13.2** makes low-bit Qwen3.6 quants emit gibberish; pin 13.1 or 13.3.

Those are speed and fit numbers. This repo adds the quality pass that says whether a fast quant is
still thinking.

## License

Code: Apache-2.0, see [LICENSE](LICENSE) and [NOTICE](NOTICE). Write-ups and
results: CC BY 4.0, see [CONTENT-LICENSE.md](CONTENT-LICENSE.md). Use them
freely; credit **cuda-cope** and link the bench file you took the number from.
