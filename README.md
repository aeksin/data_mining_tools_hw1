# Frame matching

Matching frames from two cameras based on the closest timestamps.
Реализации: AArch64 assembly, c, numba, многопоточный NumPy.

Implementations: AArch64 assembly, C, Numba, and multi-threaded NumPy.

## Requirements

Requires Python, `make`, and a C compiler.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make
python matching.py
```

The ASM implementation runs by default.

Running multiple implementations with timing:

```bash
MATCH_MODES=asm,c,numba,parallel python3 matching.py
```

Number of threads:

```bash
MATCH_MODES=parallel MATCH_WORKERS=4 python3 matching.py
```


On x86-64, use `MATCH_MODES=c`, as the ASM implementation
is designed for AArch64.

## Docker

```bash
docker build -t frame-matching .
docker run --rm frame-matching
```

Selecting implementations:

```bash
docker run --rm -e MATCH_MODES=asm,c,numba,parallel -e MATCH_WORKERS=4 frame-matching
```

On x86-64, specify `-e MATCH_MODES=c` for the default run.