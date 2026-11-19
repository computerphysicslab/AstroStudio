"""Derivation tree describing how the active image was produced."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class DerivationNode:
    label: str
    detail: str = ""
    children: List["DerivationNode"] = field(default_factory=list)


def build_tree(source: str, operations: List[str], tiff_path: str, png_path: str):
    root = DerivationNode("Original", source)
    tiff = DerivationNode("Working TIFF", tiff_path)
    current = tiff
    for index, operation in enumerate(operations, start=1):
        child = DerivationNode("%d. %s" % (index, operation), "external CLI")
        current.children.append(child)
        current = child
    preview = DerivationNode("Preview PNG", png_path)
    current.children.append(preview)
    root.children.append(tiff)
    return root


def flatten(node: DerivationNode, depth: int = 0):
    rows = [("  " * depth + node.label, node.detail)]
    for child in node.children:
        rows.extend(flatten(child, depth + 1))
    return rows
