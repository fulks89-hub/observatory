#!/usr/bin/env python3
"""Build the sanitized Observatory walkthrough with Playwright, Kokoro, and FFmpeg."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from walkthrough_contract import (
    ContractError,
    atomic_publish,
    build_receipt,
    load_receipt,
    read_regular,
    validate_receipt,
)

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / ".derived/demo-output"


def run(args: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None) -> None:
    print("+", " ".join(args))
    subprocess.run(args, cwd=cwd, env=env, check=True)


def output(args: list[str]) -> str:
    return subprocess.run(args, cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def wait_for_server(url: str, process: subprocess.Popen[bytes]) -> None:
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise SystemExit("Mission Control exited before capture")
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.25)
    raise SystemExit("Timed out waiting for Mission Control")


def synthetic_preflight() -> None:
    forbidden = [
        name for name in os.environ if name.startswith("MC_") or name.startswith("AI_RADAR_")
    ]
    if forbidden:
        raise SystemExit(
            f"Unset private dashboard environment variables: {', '.join(sorted(forbidden))}"
        )
    seed = json.loads((ROOT / "mission-control/config/seed.json").read_text())
    if seed.get("airadar", {}).get("x", {}).get("enabled") is not False:
        raise SystemExit("Synthetic seed must keep X disabled")
    if seed.get("airadar", {}).get("x", {}).get("bookmarks"):
        raise SystemExit("Synthetic seed must not contain bookmarks")
    projects = json.loads((ROOT / "mission-control/config/projects.json").read_text())
    if any(project.get("repo") for project in projects):
        raise SystemExit("Synthetic project configuration must not contain repositories")


def denylist_scan(denylist_path: Path, extra_paths: list[Path]) -> None:
    resolved = denylist_path.resolve()
    try:
        resolved.relative_to(ROOT)
    except ValueError:
        pass
    else:
        raise SystemExit("Keep the private denylist outside the repository")
    values = [
        line.strip().encode().lower()
        for line in read_regular(resolved).decode("utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not values:
        raise SystemExit("The private denylist is empty")
    tracked = output(["git", "ls-files", "--cached", "--others", "--exclude-standard"]).splitlines()
    for relative in tracked:
        lowered_path = relative.encode().lower()
        for index, value in enumerate(values, start=1):
            if value in lowered_path:
                raise SystemExit(f"Private denylist entry #{index} matched path {relative}")
        path = ROOT / relative
        if "/node_modules/" in f"/{relative}" or relative.startswith("node_modules/"):
            continue
        try:
            content = read_regular(path, boundary=ROOT).lower()
        except ContractError as error:
            raise SystemExit(f"Could not safely scan {relative}: {error}") from error
        for index, value in enumerate(values, start=1):
            if value in content:
                raise SystemExit(f"Private denylist entry #{index} matched {relative}")
    for path in extra_paths:
        try:
            content = read_regular(path, boundary=ROOT).lower()
        except ContractError as error:
            raise SystemExit(f"Could not safely scan candidate {path}: {error}") from error
        for index, value in enumerate(values, start=1):
            if value in content:
                raise SystemExit(f"Private denylist entry #{index} matched candidate media")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--voices", type=Path, required=True)
    parser.add_argument(
        "--kokoro-python",
        type=Path,
        help="existing reviewed Python runtime for Kokoro when the locked wheel is broken locally",
    )
    parser.add_argument(
        "--denylist", type=Path, help="private newline-delimited values; keep outside Git"
    )
    parser.add_argument(
        "--publish-reviewed",
        action="store_true",
        help="publish already-built derived media after human review",
    )
    parser.add_argument(
        "--review-token",
        help="exact token printed by the build whose complete output was reviewed",
    )
    args = parser.parse_args()
    for asset in (args.model, args.voices):
        if not asset.is_file():
            raise SystemExit(f"Missing Kokoro asset: {asset}")
    runtime_for_manifest = args.kokoro_python or Path(sys.executable)
    if not runtime_for_manifest.is_file():
        raise SystemExit(f"Kokoro Python runtime is unavailable: {runtime_for_manifest}")
    for command in ("node", "npm", "ffmpeg", "ffprobe"):
        if shutil.which(command) is None:
            raise SystemExit(f"Required command is unavailable: {command}")
    synthetic_preflight()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    mp4 = OUTPUT / "observatory-overview.mp4"
    gif = OUTPUT / "observatory-overview-readme.gif"
    captions = ROOT / "docs/media/observatory-overview.vtt"
    receipt_path = OUTPUT / "build-receipt.json"

    if args.publish_reviewed:
        if not args.denylist or not args.denylist.is_file():
            raise SystemExit("--publish-reviewed requires an existing private --denylist file")
        if not args.review_token:
            raise SystemExit("--publish-reviewed requires --review-token from the reviewed build")
        for artifact in (mp4, gif):
            if not artifact.is_file():
                raise SystemExit(f"Build and review the derived artifact first: {artifact}")
        try:
            receipt = load_receipt(receipt_path, boundary=ROOT)
            validate_receipt(
                ROOT,
                receipt,
                model=args.model,
                voices=args.voices,
                mp4=mp4,
                gif=gif,
                review_token_value=args.review_token,
            )
        except ContractError as error:
            raise SystemExit(f"Candidate receipt validation failed: {error}") from error
        run(
            [
                sys.executable,
                str(ROOT / "scripts/demo/verify-walkthrough.py"),
                "--mp4",
                str(mp4),
                "--gif",
                str(gif),
                "--captions",
                str(captions),
                "--receipt",
                str(receipt_path),
            ]
        )
        denylist_scan(
            args.denylist,
            [mp4, gif, captions, ROOT / "docs/media/observatory-overview-script.txt"],
        )
        with tempfile.TemporaryDirectory(prefix="observatory-demo-publish-") as temporary:
            manifest = Path(temporary) / "observatory-overview-manifest.json"
            run(
                [
                    str(runtime_for_manifest),
                    str(ROOT / "scripts/demo/verify-walkthrough.py"),
                    "--mp4",
                    str(mp4),
                    "--gif",
                    str(gif),
                    "--captions",
                    str(captions),
                    "--write-manifest",
                    "--manifest",
                    str(manifest),
                    "--receipt",
                    str(receipt_path),
                    "--review-token",
                    args.review_token,
                    "--model",
                    str(args.model),
                    "--voices",
                    str(args.voices),
                    "--python",
                    str(runtime_for_manifest),
                ]
            )
            atomic_publish(
                {
                    mp4: ROOT / "docs/media/observatory-overview.mp4",
                    gif: ROOT / "docs/media/observatory-overview-readme.gif",
                    manifest: ROOT / "docs/media/observatory-overview-manifest.json",
                }
            )
        run([sys.executable, str(ROOT / "scripts/demo/verify-walkthrough.py")])
        print("Published the reviewed artifacts and wrote their provenance manifest.")
        return

    demo_venv = ROOT / ".derived/demo-venv"
    demo_python = demo_venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not demo_python.exists():
        run([sys.executable, "-m", "venv", str(demo_venv)])
    run(
        [
            str(demo_python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--require-hashes",
            "-r",
            str(ROOT / "scripts/demo/requirements-kokoro.txt"),
        ]
    )
    kokoro_python = args.kokoro_python or demo_python
    if not kokoro_python.is_file():
        raise SystemExit(f"Kokoro Python runtime is unavailable: {kokoro_python}")
    run(["npm", "ci"], cwd=ROOT / "mission-control")
    run(["npm", "run", "check"], cwd=ROOT / "mission-control")
    run(["npm", "test"], cwd=ROOT / "mission-control")
    run(["npm", "ci"], cwd=ROOT / "scripts/demo")
    run(["npx", "playwright", "install", "chromium"], cwd=ROOT / "scripts/demo")

    clean_env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("MC_") and not key.startswith("AI_RADAR_")
    }
    server = subprocess.Popen(
        ["npm", "run", "dev", "--", "--port", "4173", "--strictPort"],
        cwd=ROOT / "mission-control",
        env=clean_env,
    )
    try:
        wait_for_server("http://127.0.0.1:4173/", server)
        run(["npm", "run", "record"], cwd=ROOT / "scripts/demo", env=clean_env)
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()

    audio = OUTPUT / "observatory-kokoro-af-heart.wav"
    run(
        [
            str(kokoro_python),
            str(ROOT / "scripts/demo/generate-kokoro-narration.py"),
            "--model",
            str(args.model),
            "--voices",
            str(args.voices),
            "--voice",
            "af_heart",
            "--output",
            str(audio),
        ]
    )
    raw = OUTPUT / "observatory-walkthrough-raw.webm"
    duration = output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(raw),
        ]
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(raw),
            "-i",
            str(audio),
            "-i",
            str(captions),
            "-filter_complex",
            "[0:v]fps=30,scale=1280:720:flags=lanczos[v];[1:a]apad[a]",
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-map",
            "2:0",
            "-t",
            duration,
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-c:s",
            "mov_text",
            "-metadata",
            "title=Observatory product walkthrough",
            str(mp4),
        ]
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(mp4),
            "-filter_complex",
            "fps=12,scale=640:360:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer",
            str(gif),
        ]
    )
    run(
        [
            str(kokoro_python),
            str(ROOT / "scripts/demo/verify-walkthrough.py"),
            "--mp4",
            str(mp4),
            "--gif",
            str(gif),
            "--captions",
            str(captions),
        ]
    )
    review = OUTPUT / "review-frames"
    review.mkdir(exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(mp4),
            "-vf",
            "fps=1/15,scale=640:-1",
            str(review / "frame-%02d.png"),
        ]
    )
    print(f"Review frames with audio before publication: {review}")
    tools = {
        "ffmpeg": output(["ffmpeg", "-version"]).splitlines()[0],
        "ffprobe": output(["ffprobe", "-version"]).splitlines()[0],
        "python": output([str(kokoro_python), "--version"]),
        "node": output(["node", "--version"]),
        "npm": output(["npm", "--version"]),
    }
    try:
        receipt = build_receipt(
            ROOT,
            model=args.model,
            voices=args.voices,
            audio=audio,
            mp4=mp4,
            gif=gif,
            tools=tools,
        )
    except ContractError as error:
        raise SystemExit(f"Could not create a provenance-bound build receipt: {error}") from error
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Exact review token: {receipt['review_token']}")
    print("Run the repository denylist/Gitleaks audit before committing regenerated media.")


if __name__ == "__main__":
    main()
