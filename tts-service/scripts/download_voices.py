"""Download Piper TTS voice models for English and Chinese."""

import sys
import urllib.request
from pathlib import Path

HF_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main"

VOICES: list[tuple[str, str]] = [
    ("en/en_US/lessac/medium", "en_US-lessac-medium.onnx"),
    ("en/en_US/lessac/medium", "en_US-lessac-medium.onnx.json"),
    ("zh/zh_CN/huayan/medium", "zh_CN-huayan-medium.onnx"),
    ("zh/zh_CN/huayan/medium", "zh_CN-huayan-medium.onnx.json"),
]


def download_voices(voice_dir: Path) -> None:
    voice_dir.mkdir(parents=True, exist_ok=True)

    for path_prefix, filename in VOICES:
        dest = voice_dir / filename
        if dest.exists():
            print(f"Skipping {filename} (already exists)")
            continue

        url = f"{HF_BASE}/{path_prefix}/{filename}"
        print(f"Downloading {filename}...")
        try:
            urllib.request.urlretrieve(url, dest)
            size_mb = dest.stat().st_size / 1_048_576
            print(f"  -> {dest} ({size_mb:.1f} MB)")
        except Exception as exc:
            print(f"  ERROR downloading {filename}: {exc}", file=sys.stderr)
            if dest.exists():
                dest.unlink()
            sys.exit(1)

    print("All voices downloaded.")


if __name__ == "__main__":
    import os

    voice_dir = Path(os.environ.get("PIPER_VOICE_DIR", "./voices"))
    download_voices(voice_dir)
