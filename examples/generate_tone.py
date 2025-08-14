#!/usr/bin/env python3
"""Generate a short sine tone WAV file for demo/testing without external deps."""

import math
import wave
import struct
from pathlib import Path


def write_tone(
    path: str, seconds: float = 0.25, freq: float = 440.0, rate: int = 16000
):
    nframes = int(rate * seconds)
    amp = 16000
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        for i in range(nframes):
            sample = int(amp * math.sin(2 * math.pi * freq * (i / rate)))
            wf.writeframes(struct.pack("<h", sample))


if __name__ == "__main__":
    out = Path("tone.wav")
    write_tone(str(out))
    print(f"Wrote {out.resolve()}")
