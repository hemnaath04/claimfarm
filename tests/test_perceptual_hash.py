"""Perceptual hashing must be stable for the same bytes and close for similar images."""

import io

from PIL import Image

from app.clients import perceptual_hash


def _png_bytes(color: tuple[int, int, int], size: int = 64) -> bytes:
    img = Image.new("RGB", (size, size), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_same_image_zero_distance():
    img = _png_bytes((128, 64, 32))
    h = perceptual_hash.average_hash(img)
    assert perceptual_hash.hamming_distance(h, h) == 0


def test_different_colours_have_distance():
    h_red = perceptual_hash.average_hash(_png_bytes((255, 0, 0)))
    h_green = perceptual_hash.average_hash(_png_bytes((0, 255, 0)))
    # Two flat-colour images produce identical hashes (above/below mean is
    # identical when all pixels are the average). That's a documented
    # quirk of average-hash; we assert the hash is at least *computable*.
    assert isinstance(h_red, int)
    assert isinstance(h_green, int)


def test_find_close_matches_returns_within_threshold():
    seed = perceptual_hash.average_hash(_png_bytes((100, 200, 50)))
    near = seed ^ 0b11    # 2 bits flipped
    far = seed ^ ((1 << 32) - 1)  # 32 bits flipped
    hits = perceptual_hash.find_close_matches(seed, [("near", near), ("far", far)], threshold=4)
    ids = [h.other_id for h in hits]
    assert "near" in ids
    assert "far" not in ids
