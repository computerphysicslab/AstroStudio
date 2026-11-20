"""Non-destructive, reorderable pipeline graph built from serialized argv jobs."""

from dataclasses import dataclass, field
from typing import List, Sequence

from .pipeline_export import write_makefile, write_shell


@dataclass
class PipelineNode:
    argv: List[str]
    label: str = ""
    enabled: bool = True
    children: List["PipelineNode"] = field(default_factory=list)


class PipelineGraph:
    def __init__(self, nodes: Sequence[PipelineNode] = None) -> None:
        self.nodes: List[PipelineNode] = list(nodes or [])

    @classmethod
    def from_argv(cls, jobs: Sequence[Sequence[str]], labels: Sequence[str] = None) -> "PipelineGraph":
        nodes = []
        for index, argv in enumerate(jobs):
            label = labels[index] if labels and index < len(labels) else "Job %03d" % (index + 1)
            nodes.append(PipelineNode(list(argv), label))
        return cls(nodes)

    def move(self, index: int, delta: int) -> bool:
        target = index + delta
        if index < 0 or target < 0 or target >= len(self.nodes):
            return False
        self.nodes.insert(target, self.nodes.pop(index))
        return True

    def set_enabled(self, index: int, enabled: bool) -> None:
        if 0 <= index < len(self.nodes):
            self.nodes[index].enabled = enabled

    def duplicate(self, index: int) -> bool:
        if not 0 <= index < len(self.nodes):
            return False
        node = self.nodes[index]
        self.nodes.insert(index + 1, PipelineNode(list(node.argv), node.label + " copy", node.enabled))
        return True

    def remove(self, index: int) -> bool:
        if not 0 <= index < len(self.nodes):
            return False
        self.nodes.pop(index)
        return True

    def argv_list(self) -> List[List[str]]:
        return [list(node.argv) for node in self.nodes if node.enabled]

    def export(self, path: str) -> str:
        jobs = self.argv_list()
        if path.endswith(".mk") or path.endswith("Makefile"):
            write_makefile(jobs, path)
        else:
            if not path.endswith(".sh"):
                path += ".sh"
            write_shell(jobs, path)
        return path
