"""Perceptual hashing layer for image-reuse fraud detection.

The hash distance between two photos approximates how similar they look
even after compression, resizing or light edits. We use 64-bit average
hash by default; production deployments may swap in pHash or wHash via
the same interface.

Use cases:
- Detect when the same farmer submits the same photo twice (different
  caption, same image).
- Cross-check incoming photos against a small corpus of known stock
  images (alamy, shutterstock samples) so they can be flagged.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from typing import Iterable

from PIL import Image

logger = logging.getLogger(__name__)


def average_hash(image_bytes: bytes, size: int = 8) -> int:
    """Compute a `size*size`-bit average hash. Returns an int for cheap
    Hamming-distance comparison via XOR + bin(...).count('1')."""
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            img = img.convert("L").resize((size, size), Image.Resampling.LANCZOS)
            # Avoid the deprecated Image.getdata(); raw bytes are equivalent
            # for an 8-bit "L"-mode image.
            pixels = list(img.tobytes())
    except Exception:
        logger.exception("perceptual_hash: image decode failed")
        return 0
    avg = sum(pixels) / len(pixels)
    bits = 0
    for i, p in enumerate(pixels):
        if p > avg:
            bits |= 1 << i
    return bits


def hamming_distance(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


@dataclass
class HashMatch:
    other_id: str
    distance: int            # 0 = identical, 64 = unrelated (for 8×8 hash)
    threshold: int           # what we considered "close enough"


def find_close_matches(
    target: int,
    corpus: Iterable[tuple[str, int]],
    threshold: int = 8,
) -> list[HashMatch]:
    """Return all (id, distance) pairs in `corpus` within `threshold` bits
    of `target`. For an 8×8 (64-bit) hash, ≤8 is a very strong match."""
    hits: list[HashMatch] = []
    for other_id, other_hash in corpus:
        d = hamming_distance(target, other_hash)
        if d <= threshold:
            hits.append(HashMatch(other_id=other_id, distance=d, threshold=threshold))
    return sorted(hits, key=lambda h: h.distance)
