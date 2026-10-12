import base64
import io
from pathlib import Path

from PIL import Image

import tray_icon

SRC_DIR = Path(__file__).resolve().parents[1] / "src"


def test_png_base64_returns_valid_png():
    data = tray_icon.png_base64(64)
    img = Image.open(io.BytesIO(base64.b64decode(data)))
    assert img.format == "PNG"
    assert img.size == (64, 64)
    assert img.mode == "RGBA"


def test_build_ico_writes_multi_size_ico(tmp_path):
    path = tmp_path / "app.ico"
    tray_icon.build_ico(path)
    assert path.exists()
    img = Image.open(path)
    assert img.format == "ICO"
    sizes = {tuple(s) for s in img.info.get("sizes", set())}
    assert (16, 16) in sizes
    assert (48, 48) in sizes
    assert (256, 256) in sizes


def test_computerlock_sets_window_icon():
    src = (SRC_DIR / "ComputerLock.py").read_text(encoding="utf-8")
    assert "iconphoto" in src
