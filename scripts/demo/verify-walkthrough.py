#!/usr/bin/env python3
"""Verify and inventory the synthetic Observatory walkthrough artifacts."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from walkthrough_contract import (
    ARTIFACT_PATHS,
    ContractError,
    file_metadata,
    load_receipt,
    read_regular,
    validate_receipt,
    verify_manifest,
)

ROOT = Path(__file__).resolve().parents[2]
def run(*args: str) -> str:
    result = subprocess.run(args, cwd=ROOT, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def media_probe(path: Path) -> dict[str, object]:
    return json.loads(
        run(
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration:format_tags:stream=index,codec_name,codec_type,width,height,channels:stream_tags",
            "-of",
            "json",
            str(path),
        )
    )


def caption_text(value: str) -> str:
    lines = []
    for line in value.splitlines():
        stripped = line.strip()
        if not stripped or stripped == "WEBVTT" or "-->" in stripped or stripped.isdigit():
            continue
        lines.append(stripped)
    return " ".join(lines)


def validate_media(path: Path, captions: Path) -> dict[str, object]:
    probe = media_probe(path)
    streams = probe.get("streams", [])
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
    subtitle = next((item for item in streams if item.get("codec_type") == "subtitle"), None)
    if (
        not video
        or video.get("codec_name") != "h264"
        or (video.get("width"), video.get("height")) != (1280, 720)
    ):
        raise SystemExit("Walkthrough must contain 1280x720 H.264 video")
    if not audio or audio.get("codec_name") != "aac":
        raise SystemExit("Walkthrough must contain AAC narration")
    if not subtitle or subtitle.get("codec_name") != "mov_text":
        raise SystemExit("Walkthrough must contain embedded mov_text captions")
    embedded_captions = run(
        "ffmpeg",
        "-v",
        "error",
        "-i",
        str(path),
        "-map",
        "0:s:0",
        "-f",
        "webvtt",
        "pipe:1",
    )
    if caption_text(embedded_captions) != caption_text(captions.read_text()):
        raise SystemExit("Embedded captions do not match the WebVTT sidecar")
    duration = float(probe["format"]["duration"])
    if not 45 <= duration <= 90:
        raise SystemExit(f"Unexpected walkthrough duration: {duration}")
    timestamps = re.findall(r"(?:\d{2}:)?(\d{2}):(\d{2}\.\d{3})", captions.read_text())
    if timestamps:
        last_seconds = int(timestamps[-1][0]) * 60 + float(timestamps[-1][1])
        if last_seconds > duration + 0.25:
            raise SystemExit("Captions extend beyond the walkthrough")
    serialized = json.dumps(probe)
    if re.search(r"/(?:Users|home)/|[A-Za-z]:\\", serialized):
        raise SystemExit("Media metadata contains a local filesystem path")
    silence = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "info",
            "-i",
            str(path),
            "-af",
            "silencedetect=n=-45dB:d=12",
            "-f",
            "null",
            "-",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if "silence_duration:" in silence.stderr:
        raise SystemExit("Walkthrough contains a silent segment of at least 12 seconds")
    return probe


def write_manifest(
    args: argparse.Namespace, probe: dict[str, object], receipt: dict[str, object]
) -> None:
    artifact_sources = {
        ARTIFACT_PATHS[0]: args.mp4,
        ARTIFACT_PATHS[1]: args.gif,
        ARTIFACT_PATHS[2]: ROOT / ARTIFACT_PATHS[2],
        ARTIFACT_PATHS[3]: args.captions,
    }
    manifest = {
        "schema_version": 1,
        "status": "verified-local-synthetic-walkthrough",
        "source_revision": receipt["source_revision"],
        "source_input_tree_sha256": receipt["source_input_tree_sha256"],
        "source_files": receipt["source_files"],
        "build_receipt_review_token": receipt["review_token"],
        "narration": receipt["narration"],
        "tools": receipt["tools"],
        "media_probe": probe,
        "artifacts": {
            relative: file_metadata(path, boundary=ROOT)
            for relative, path in artifact_sources.items()
        },
        "release_commit": None,
        "privacy_review": {
            "synthetic_seed_required": True,
            "frame_review_required": True,
            "denylist_scan_required": True,
        },
    }
    args.manifest.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mp4", type=Path, default=ROOT / ARTIFACT_PATHS[0])
    parser.add_argument("--gif", type=Path, default=ROOT / ARTIFACT_PATHS[1])
    parser.add_argument("--captions", type=Path, default=ROOT / ARTIFACT_PATHS[3])
    parser.add_argument(
        "--manifest", type=Path, default=ROOT / "docs/media/observatory-overview-manifest.json"
    )
    parser.add_argument("--write-manifest", action="store_true")
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--review-token")
    parser.add_argument("--model", type=Path)
    parser.add_argument("--voices", type=Path)
    parser.add_argument("--python", default="python3")
    args = parser.parse_args()
    try:
        for path in (args.mp4, args.gif, args.captions):
            file_metadata(path, boundary=ROOT)
        probe = validate_media(args.mp4, args.captions)
        if args.write_manifest:
            if not all((args.model, args.voices, args.receipt, args.review_token)):
                raise ContractError(
                    "--model, --voices, --receipt, and --review-token are required "
                    "to write provenance"
                )
            receipt = load_receipt(args.receipt, boundary=ROOT)
            validate_receipt(
                ROOT,
                receipt,
                model=args.model,
                voices=args.voices,
                mp4=args.mp4,
                gif=args.gif,
                review_token_value=args.review_token,
            )
            write_manifest(args, probe, receipt)
        elif args.manifest.is_file():
            manifest = json.loads(read_regular(args.manifest, boundary=ROOT))
            verify_manifest(ROOT, manifest)
    except (ContractError, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise SystemExit(f"Walkthrough verification failed: {error}") from error
    print("Walkthrough verification passed.")


if __name__ == "__main__":
    main()
