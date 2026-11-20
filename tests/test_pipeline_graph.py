"""Pipeline graph model tests."""

from astrostudio.core.pipeline_graph import PipelineGraph


def test_pipeline_graph_reorder_disable_duplicate_and_export(tmp_path):
    graph = PipelineGraph.from_argv(
        [["convert", "a.png"], ["convert", "b.png"], ["convert", "c.png"]],
        ["A", "B", "C"],
    )
    assert graph.move(0, 1)
    assert [node.label for node in graph.nodes] == ["B", "A", "C"]
    graph.set_enabled(1, False)
    assert graph.argv_list() == [["convert", "b.png"], ["convert", "c.png"]]
    assert graph.duplicate(0)
    assert [node.label for node in graph.nodes] == ["B", "B copy", "A", "C"]
    assert graph.remove(1)
    assert len(graph.nodes) == 3

    script = graph.export(str(tmp_path / "pipeline.sh"))
    text = open(script, encoding="utf-8").read()
    assert "convert b.png" in text and "convert c.png" in text
    assert "convert a.png" not in text
