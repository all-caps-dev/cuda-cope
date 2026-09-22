# The measurement loop

You do not run this by hand. Cheap models run the sweep; you read the CSV.

## One experiment

1. **Hypothesis.** One sentence with a number in it. "IQ3_S at `--n-cpu-moe 48`
   beats 47 tok/s shallow." A hypothesis without a number cannot fail, so it is
   not a hypothesis.
2. **One change.** Nothing else moves. Same quant, same depths, same repetitions.
3. **Three runs.** Warm the box first. Cold runs read low and will flatter
   whatever you test second.
4. **Record.** Append to the run CSV in the schema below. Stamp the driver, CUDA
   toolkit and llama.cpp commit alongside it.
5. **Decide.** Faster and it loaded clean, it becomes the new baseline.
   Otherwise revert, and write down why it lost.
6. **Quality pass on every quant change.** Speed alone is how a gibberish quant
   ships.

## The CSV schema

```
label,quant,type,depth,pp_tok_s,tg_tok_s,vram_peak_mib,ram_used_peak_mib,status
```

- Sort by `tg_tok_s` for the ranking you feel day to day.
- Filter `status=FAIL` for the fit ceiling. An OOM writes FAIL and the sweep
  continues, so the CSV doubles as a fit map.
- Watch `ram_used_peak_mib` on mixture-of-experts rows. A FAIL with healthy
  `vram_peak_mib` is the system out-of-memory killer, not the card.

## Dense versus mixture-of-experts on 16 GB

A mixture-of-experts model must hold **all** expert weights resident, because the
router can pick any expert for any token. An "A3B" style name describes compute
per token, not memory footprint. Offloading idle experts to system RAM is cheap
for MoE, because only a few fire per token, and expensive for dense, because
every parameter fires every time.

The practical consequence: for MoE the real ceiling is **system RAM**, not VRAM.

## What gets published

Every run, including the ones that failed. A bench corpus that only publishes
wins is a marketing corpus.
