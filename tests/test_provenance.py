"""Derivation tree tests."""

from astrostudio.core.provenance import build_tree, flatten


def test_tree_contains_operations_and_preview():
    root = build_tree("orig.fits", ["resize-down", "blur"], "w.tiff", "p.png")
    rows = flatten(root)
    labels = [label for label, _detail in rows]
    assert labels[0].strip() == "Original"
    assert any("resize-down" in label for label in labels)
    assert any("blur" in label for label in labels)
    assert any("Preview PNG" in label for label in labels)
