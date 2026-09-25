"""Durable raw evidence and separately normalized human evidence, even on failure."""

import io
import json
import re
from dataclasses import asdict

from rich.console import Console

from jj_lab.core.doctor import versions
from jj_lab.core.environment import LabError
from jj_lab.inspect.compare import compare
from jj_lab.ui import render


def normalized(text: str, root: str) -> str:
    text = text.replace(root, "<LAB_ROOT>")
    text = re.sub(r"\b[0-9a-f]{40,128}\b", lambda m: m[0][:12], text)
    return re.sub(r"\d{4}-\d\d-\d\d[T ]\d\d:\d\d:[\d.+:-]+Z?", "<TIME>", text)


def rendered(fn, *args) -> str:
    stream = io.StringIO()
    fn(Console(file=stream, width=110, color_system=None), *args)
    return stream.getvalue()


def record(run) -> None:
    path = run.path
    s = run.scenario
    root = str(run.runner.environment.root)
    version = run.runner.run(
        "jj", ["--version"], run.runner.environment.root, allow_failure=True
    ).stdout.strip()
    try:
        toolchain = versions(run.runner)
    except LabError as exc:
        toolchain = {"error": str(exc)}
    metadata = {
        "schema_version": 1,
        "toolchain": toolchain,
        "name": s.name,
        "purpose": s.summary,
        "category": s.category,
        "operation": s.operation,
        "invariant": s.invariant,
        "sources": s.sources,
        "tags": s.tags,
        "classification": s.classification,
        "jj_version": version,
        "status": run.status,
        "error": run.error,
        "initial_state": "empty local origin"
        if s.empty
        else "seeded main; colocated Alice; Git Bob/Carol",
        "observations": run.context.observations,
        "evidence_path": str(path),
    }

    def write_json(name, value):
        (path / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")

    write_json("metadata.json", metadata)
    (path / "commands.jsonl").write_text(
        "".join(json.dumps(v) + "\n" for v in run.runner.serialized())
    )
    for label, state, views in [
        ("before", run.before, run.before_views),
        ("after", run.after, run.after_views),
    ]:
        write_json(label + ".json", asdict(state) if state else None)
        text = "\n\n".join(f"$ {key}\n{value}" for key, value in views.items())
        (path / (label + ".txt")).write_text(normalized(text, root))
    write_json("assertions.json", [asdict(c) for c in run.context.checks])
    write_json("checkpoints.json", {k: asdict(v) for k, v in run.context.checkpoints.items()})
    comparisons = (
        rendered(render.differences, compare(run.before, run.after))
        if run.before and run.after
        else "Unavailable: " + str(run.error)
    )
    (path / "compare.txt").write_text(normalized(comparisons, root))
    (path / "xray.txt").write_text(
        normalized(rendered(render.xray, run.after), root) if run.after else "No after snapshot\n"
    )
    summary = f"# {s.name}: {run.status}\n\n{s.summary}\n\nOperation: {s.operation}\n\n"
    summary += f"Classification: {s.classification}\nVersion: {version}\n\n"
    for c in run.context.checks:
        summary += (
            f"- {'PASS' if c.passed else 'FAIL'} {c.name}: "
            f"expected {c.expected!r}; actual {c.actual!r}\n"
        )
    if run.error:
        summary += f"\nError: {run.error}\n"
    summary += (
        "\n## Observations\n\n```json\n"
        + json.dumps(run.context.observations, indent=2)
        + "\n```\n"
    )
    summary += "\nSources:\n" + "\n".join("- " + url for url in s.sources) + "\n"
    (path / "summary.md").write_text(normalized(summary, root))
