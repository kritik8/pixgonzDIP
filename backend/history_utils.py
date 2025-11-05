"""Simple file-backed undo/redo history utilities.

This provides a tiny, optional server-side history store keyed by session_id.
It's intentionally small and not suitable for production as-is (no auth, no GC,
no concurrency controls). It's useful for demos and to wire up undo/redo while
you build your frontend.
"""
from pathlib import Path
from PIL import Image
import time
import shutil

BASE = Path(__file__).parent
TMP = BASE / "tmp_history"


def _session_dir(session_id: str) -> Path:
    return TMP / str(session_id)


def push_state(session_id: str, img: Image.Image) -> None:
    """Push the provided PIL image to the session undo stack.

    Creates directories if needed. Push clears the redo stack.
    """
    sd = _session_dir(session_id)
    undo = sd / "undo"
    redo = sd / "redo"
    undo.mkdir(parents=True, exist_ok=True)
    if redo.exists():
        # clear redo on new action
        shutil.rmtree(redo)

    ts = int(time.time() * 1000)
    fname = undo / f"state_{ts}.png"
    img.save(fname, format="PNG")


def undo(session_id: str):
    """Pop last state into redo and return the previous image (PIL) or None.

    If there's only a single state, it will be returned (no-op undo).
    """
    sd = _session_dir(session_id)
    undo = sd / "undo"
    redo = sd / "redo"
    if not undo.exists():
        return None

    files = sorted(undo.glob("state_*.png"))
    if not files:
        return None

    # move last to redo
    last = files[-1]
    redo.mkdir(parents=True, exist_ok=True)
    target = redo / last.name
    shutil.move(str(last), str(target))

    # now the new last (if any) is the state to return
    remaining = sorted(undo.glob("state_*.png"))
    if not remaining:
        return None
    return Image.open(remaining[-1]).convert("RGB")


def redo(session_id: str):
    """Pop from redo back to undo and return that image (PIL) or None."""
    sd = _session_dir(session_id)
    undo = sd / "undo"
    redo_dir = sd / "redo"
    if not redo_dir.exists():
        return None
    files = sorted(redo_dir.glob("state_*.png"))
    if not files:
        return None
    last = files[-1]
    undo.mkdir(parents=True, exist_ok=True)
    target = undo / last.name
    shutil.move(str(last), str(target))
    return Image.open(target).convert("RGB")
