#!/usr/bin/env python3
"""Render the public Observatory walkthrough narration with local Kokoro."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import soundfile as sf
from kokoro_onnx import Kokoro


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--voices", type=Path, required=True)
    parser.add_argument("--voice", default="af_heart")
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument(
        "--script",
        type=Path,
        default=root / "docs/media/observatory-overview-script.txt",
    )
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    for asset in (args.model, args.voices, args.script):
        if not asset.is_file():
            raise SystemExit(f"Required input does not exist: {asset}")

    engine = Kokoro(str(args.model), str(args.voices))
    available_voices = engine.get_voices()
    if args.voice not in available_voices:
        raise SystemExit(
            f"Unknown voice {args.voice!r}. Available voices: {', '.join(available_voices)}"
        )

    text = args.script.read_text(encoding="utf-8")
    started = time.perf_counter()
    samples, sample_rate = engine.create(
        text,
        voice=args.voice,
        speed=args.speed,
        lang="en-us",
    )
    generation_seconds = time.perf_counter() - started
    audio_seconds = len(samples) / sample_rate

    args.output.parent.mkdir(parents=True, exist_ok=True)
    sf.write(args.output, samples, sample_rate, subtype="PCM_16")
    print(
        json.dumps(
            {
                "output": str(args.output.resolve()),
                "voice": args.voice,
                "sample_rate_hz": sample_rate,
                "audio_seconds": round(audio_seconds, 2),
                "generation_seconds": round(generation_seconds, 2),
                "realtime_factor": round(generation_seconds / audio_seconds, 3),
                "characters": len(text),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
