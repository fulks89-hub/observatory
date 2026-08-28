from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/demo"))

import walkthrough_contract as contract  # noqa: E402


def write(path: Path, content: bytes = b"fixture") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def receipt_fixture(tmp_path: Path):
    subprocess.run(["git", "init", "-q", tmp_path], check=True)
    paths = {
        "model": write(tmp_path / "assets/model.onnx"),
        "voices": write(tmp_path / "assets/voices.bin"),
        "audio": write(tmp_path / ".derived/demo-output/narration.wav"),
        "mp4": write(tmp_path / ".derived/demo-output/candidate.mp4"),
        "gif": write(tmp_path / ".derived/demo-output/candidate.gif"),
    }
    tracked = [
        write(tmp_path / "mission-control/source.js"),
        write(tmp_path / "scripts/demo/generate-kokoro-narration.py"),
        write(tmp_path / "scripts/demo/requirements-kokoro.txt"),
        write(tmp_path / "scripts/demo/scenes.json"),
        write(tmp_path / "docs/media/observatory-overview-script.txt"),
        write(tmp_path / "docs/media/observatory-overview.vtt"),
    ]
    subprocess.run(
        ["git", "add", *[str(path.relative_to(tmp_path)) for path in tracked]],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "-qm",
            "fixture",
        ],
        cwd=tmp_path,
        check=True,
    )
    receipt = contract.build_receipt(
        tmp_path,
        model=paths["model"],
        voices=paths["voices"],
        audio=paths["audio"],
        mp4=paths["mp4"],
        gif=paths["gif"],
        tools={"ffmpeg": "fixture"},
    )
    return receipt, paths


def test_receipt_binds_token_candidates_and_source_tree(tmp_path: Path):
    receipt, paths = receipt_fixture(tmp_path)
    args = dict(
        model=paths["model"],
        voices=paths["voices"],
        mp4=paths["mp4"],
        gif=paths["gif"],
        review_token_value=receipt["review_token"],
    )
    contract.validate_receipt(tmp_path, receipt, **args)
    with pytest.raises(contract.ContractError, match="review token"):
        contract.validate_receipt(tmp_path, receipt, **{**args, "review_token_value": "wrong"})
    paths["mp4"].write_bytes(b"changed after review")
    with pytest.raises(contract.ContractError, match="changed after build"):
        contract.validate_receipt(tmp_path, receipt, **args)


def test_receipt_rejects_untracked_and_symlinked_demo_sources(tmp_path: Path):
    receipt, paths = receipt_fixture(tmp_path)
    write(tmp_path / "scripts/demo/untracked.py")
    with pytest.raises(contract.ContractError, match="untracked demo source"):
        contract.validate_receipt(
            tmp_path,
            receipt,
            model=paths["model"],
            voices=paths["voices"],
            mp4=paths["mp4"],
            gif=paths["gif"],
            review_token_value=receipt["review_token"],
        )
    (tmp_path / "scripts/demo/untracked.py").unlink()
    outside = write(tmp_path.parent / f"{tmp_path.name}-outside")
    (tmp_path / "scripts/demo/link").symlink_to(outside)
    subprocess.run(["git", "add", "scripts/demo/link"], cwd=tmp_path, check=True)
    with pytest.raises(contract.ContractError, match="symbolic links"):
        contract.build_receipt(
            tmp_path,
            model=paths["model"],
            voices=paths["voices"],
            audio=paths["audio"],
            mp4=paths["mp4"],
            gif=paths["gif"],
            tools={},
        )


def test_atomic_publish_rolls_back_all_destinations(tmp_path: Path, monkeypatch):
    sources = [write(tmp_path / f"candidate/{index}", b"new") for index in range(2)]
    destinations = [write(tmp_path / f"published/{index}", b"old") for index in range(2)]
    real_replace = contract.os.replace
    calls = 0

    def fail_second(source, destination):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated publish failure")
        return real_replace(source, destination)

    monkeypatch.setattr(contract.os, "replace", fail_second)
    with pytest.raises(OSError, match="simulated publish failure"):
        contract.atomic_publish(dict(zip(sources, destinations, strict=True)))
    assert [path.read_bytes() for path in destinations] == [b"old", b"old"]
