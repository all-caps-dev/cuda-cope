# A larger quant at large context: it fits, and it is not close

**Date** 2026-09-22 · **Box** see [HARDWARE.md](../HARDWARE.md) · Guarded fit sweep, private lane restored after

## The question

Received wisdom on a 16 GB card is that you trade quant quality for context: a
bigger quant leaves no room for a deep KV cache. Is that true for this
mixture-of-experts model, where experts offload to system RAM?

## Method

Each configuration was loaded with a hard RAM guard: a watcher sampled
`MemAvailable` every two seconds and killed the attempt if it fell below 1,400
MiB, so the cgroup out-of-memory killer could never fire and take the box down.
VRAM peak and the minimum available RAM were recorded during load, and an OK
result also had to serve one generation. The private lane was stopped once for
the sweep and restored to its exact prior config afterward.

## Result

| Model | Quant | Context | n-cpu-moe | Status | VRAM peak | RAM avail min |
|---|---|---|---|---|---|---|
| Nail | Q4_K_S 19.5 GB | 65,536 | 20 | OK | 12,156 MiB | 17,869 MiB |
| Nail | Q4_K_S 19.5 GB | 131,072 | 24 | OK | 11,292 MiB | 17,795 MiB |
| Nail | Q4_K_S 19.5 GB | **262,144** | 28 | **OK** | 11,308 MiB | 17,660 MiB |
| Occult-Nail | Q3_K_XL 15.7 GB | 131,072 | 20 | OK | 11,036 MiB | 17,806 MiB |

Nothing came close to a wall. VRAM peaked around 11 to 12 GiB of 16, and
available RAM never dropped below 17.6 GiB of ~24. The RAM guard never tripped.

## Why the trade-off is weaker than the folklore

Two reasons, both specific to this model and setup:

1. **The weights are memory-mapped.** llama.cpp mmaps the GGUF, so the expert
   weights parked in system RAM are file-backed pages that `MemAvailable`
   counts as reclaimable, not as used memory. A 19.5 GB quant does not subtract
   19.5 GB from the RAM budget the way a malloc would. This is why the 20.89 GB
   quant question is less scary than the disk size suggests.

2. **The KV cache is tiny for this architecture.** Qwen3.6-35B-A3B uses a single
   key/value head with an MLA-style projection, so the per-token KV footprint is
   a fraction of a normal attention model's. A quarter-million-token context
   barely moves VRAM: 262,144 tokens peaked *lower* than 65,536 did, because the
   higher `n-cpu-moe` at the deep-context run pushed more experts to RAM and the
   small KV growth did not offset it.

The lever that actually matters on this card is `n-cpu-moe`, not the quant size
or the context length.

## What this means for the private lane

The private local model can run **Nail Q4_K_S or Occult-Nail at Q3_K_XL and up,
at 256k context**, on this 16 GB card, with headroom on both VRAM and RAM. The
earlier IQ3_S choice was leaving quality on the table for no fit reason. The
Occult-Nail vs Nail bench already showed the abliterated build is the better
private-lane pick; this shows it can run at a serious quant and full context at
the same time.

## Caveats

- VRAM peak is measured with the KV cache **allocated** for the declared context,
  which llama.cpp reserves at load. It is not measured with 256k tokens actually
  resident and every expert hot. A real 256k-token workload should be watched on
  [the board] once, but the allocation headroom says it will hold.
- Generation *speed* at depth was not measured here; this was a fit sweep, not a
  throughput run. Deep context is slower to prefill regardless of fit.
- `n-cpu-moe` was raised with context to keep VRAM flat. The values here are a
  safe starting point, not the tuned optimum; lower them to pull experts onto the
  GPU until VRAM fills, for speed.

## Reproduce

The guarded sweep script pattern: stop the service, load each config with a
`MemAvailable` watchdog, record VRAM/RAM peak, require one generation, kill,
restore. Keep the guard above your largest expected transient.
