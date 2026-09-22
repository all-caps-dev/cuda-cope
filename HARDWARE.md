# The reference box

Measured on the box, not copied from a spec sheet. Re-measure before trusting
any of it; hardware notes rot faster than code.

| Component | Value |
|---|---|
| GPU | NVIDIA GeForce RTX 4070 Ti SUPER, 16,376 MiB |
| GPU class | roughly a 5070 for compute; the 16 GB is the product, not the speed |
| Memory bandwidth | 672 GB/s |
| CPU | Ryzen 7 7800X3D, 8 physical cores |
| Host RAM | 30 GB, container limited to 24,888 MB with 512 MB swap |
| Driver | 595.71.05 |
| CUDA toolkit linked | 13.3.1 |
| llama.cpp | build 10968, commit 41abbfd59 |

## The CUDA version trap

`nvidia-smi` prints a "CUDA Version" figure that is the **driver's maximum
supported runtime**, not the toolkit your binary linked against. On this box
`nvidia-smi` says 13.2 while the loaded runtime is 13.3.1.

That distinction matters because **CUDA 13.2 produces gibberish on low-bit
Qwen3.6 quants**. Reading the wrong number leads you to diagnose a phantom, or
worse, to miss a real one. Check what the binary actually links:

```sh
ldd "$(command -v llama-server)" | grep -E 'cudart|cublas'
readlink -f /usr/local/cuda
```

Pin 13.1 or 13.3. Record the answer in every bench file.

## Threads

Expert offload is DDR5-bandwidth-bound rather than cache-bound, so thread counts
above the physical core count are flat or slightly worse. Eight is the setting
here. Test it first because it is the cheapest experiment in the list.
