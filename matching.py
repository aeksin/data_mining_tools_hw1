import ctypes
import os
import sys
import time
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from numba import njit

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

def get_native_function(name):
    ext = ".dylib" if sys.platform == "darwin" else ".so"
    lib = ctypes.CDLL(str(Path(__file__).with_name("libmatch" + ext)))
    func = getattr(lib, "match_" + name)
    func.argtypes = [
        ctypes.c_void_p, ctypes.c_size_t,
        ctypes.c_void_p, ctypes.c_size_t,
        ctypes.c_void_p,
    ]
    func.restype = None
    return func

def match_native(a, b, func):
    result = np.empty(a.size, dtype=np.int64)
    func(
        a.ctypes.data, a.size,
        b.ctypes.data, b.size,
        result.ctypes.data,
    )
    return result

@njit(cache=True)
def match_numba(a, b):
    res = np.empty(a.size, dtype=np.int64)
    j = 0
    cur_b = b[0]

    for i in range(a.size):
        cur_a = a[i]
        while j + 1 < b.size:
            next_b = b[j + 1]
            if next_b - cur_a >= cur_a - cur_b:
                break
            j += 1
            cur_b = next_b

        res[i] = j

    return res


def match_chunk(a, b, result, lb, rb):
    x = a[lb:rb]
    pos = np.searchsorted(b, x)

    left = np.clip(pos - 1, 0, b.size - 1)
    right = np.clip(pos, 0, b.size - 1)

    result[lb:rb] = np.where(
        b[right] - x < x - b[left], right, left
    )

def match_threads(a, b):
    result = np.empty(a.size, dtype=np.int64)
    workers = int(os.getenv("MATCH_WORKERS", os.cpu_count() or 1))

    if workers == 1:
        match_chunk(a, b, result, 0, a.size)
        return result

    with ThreadPoolExecutor(max_workers=workers) as pool:
        jobs = [
            pool.submit(
                match_chunk, a, b, result,
                i * a.size // workers,
                (i + 1) * a.size // workers,
            )
            for i in range(workers)
        ]
        for job in jobs:
            job.result()

    return result


def make_timestamps(fps: int, st_ts: float, fn_ts: float) -> np.ndarray:
    """
    Create array of timestamps. This array is discretized with fps,
    but not evenly.
    Timestamps are assumed sorted and unique.
    Parameters:
    - fps: int
        Average frame per second
    - st_ts: float
        First timestamp in the sequence
    - fn_ts: float
        Last timestamp in the sequence
    Returns:
        np.ndarray: synthetic timestamps
    """
    # generate uniform timestamps
    timestamps = np.linspace(st_ts, fn_ts, int((fn_ts - st_ts) * fps))
    # add an fps noise
    timestamps += np.random.randn(len(timestamps))
    timestamps = np.unique(np.sort(timestamps))
    return timestamps

def match_timestamps(timestamps1: np.ndarray, timestamps2: np.ndarray) -> np.ndarray:
    """
    Timestamp matching function. It returns such array `matching` of length len(timestamps1),
    that for each index i of timestamps1 the output element matching[i] contains
    the index j of timestamps2, so that the difference between
    timestamps2[j] and timestamps1[i] is minimal.
    """
    if timestamps1.size == 0 or timestamps2.size == 0:
        return np.empty(0, dtype=np.int64)

    a = np.ascontiguousarray(timestamps1, dtype=np.float64)
    b = np.ascontiguousarray(timestamps2, dtype=np.float64)

    methods = {
        "numba": lambda: match_numba(a, b),
        "parallel": lambda: match_threads(a, b),
    }
    modes = [
        s.strip().lower()
        for s in (os.getenv("MATCH_MODES") or "asm").split(",")
        if s.strip()
    ]
    if len(modes) == 0:
        modes = ["asm"]

    first = None

    valid_modes = {"asm", "c", "numba", "parallel"}

    modes = [mode for mode in modes if mode in valid_modes] or ["asm"]

    for mode in modes:
        try:
            if mode in ("asm", "c"):
                func = get_native_function(mode)
                run = lambda: match_native(a, b, func)
            else:
                run = methods[mode]
                if mode == "numba":
                    match_numba(a[:1], b[:1])

            start = time.perf_counter()
            result = run()
            elapsed_time = (time.perf_counter() - start) * 1000

            logging.info("%-8s %.5f ms", mode, elapsed_time)

        except Exception as exc:
            logging.warning("%s unavailable: %s", mode, exc)
            continue

        if first is None and result is not None:
            first = result

        if first is not None and not np.array_equal(first, result):
            raise RuntimeError(f"{mode}: results not matched")

    if first is None:
        raise RuntimeError("No method succeeded")

    return first


def main():
    """
    Setup:
        Say we have two cameras, each filming the same scene. We make
        a prediction based on this scene (e.g. detect a human pose).
        To improve the robustness of the detection algorithm,
        we average the predictions from both cameras at each moment.
        The camera data is a pair (frame, timestamp), where the timestamp
        represents the moment when the frame was captured by the camera.
    Problem:
        For each frame of camera1, we need to find the index of the
        corresponding frame received by camera2. The frame i from camera2
        corresponds to the frame j from camera1, if
        abs(timestamps[i] - timestamps[j]) is minimal for all i.
    """
    # generate timestamps for the first camera
    timestamps1 = make_timestamps(30, time.time(), time.time() + 3600)
    # generate timestamps for the second camera
    timestamps2 = make_timestamps(60, time.time(), time.time() + 3600)
    matching = match_timestamps(timestamps1, timestamps2)


if __name__ == '__main__':
    main()
