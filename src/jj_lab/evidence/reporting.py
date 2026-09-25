"""Generate findings and the behavior matrix exclusively from recorded results."""

import json
from pathlib import Path

from jj_lab.core.doctor import JJ_VERSION
from jj_lab.core.environment import Environment, LabError

COLUMNS = {
    "Operation succeeds": "operation_succeeds",
    "Conflicted revision created": "conflicted_revision_created",
    "Conflict sides": "conflict_sides",
    "Can postpone": "can_postpone",
    "Can transform/rebase unresolved": "can_transform_unresolved",
    "jj resolve applicable": "resolve_applicable",
    "Manual resolution possible": "manual_resolution_possible",
    "Descendants affected": "descendants_affected",
    "Git view reliable": "git_view_reliable",
    "Known limitation": "known_limitation",
}


def cell(value: object) -> str:
    if value is None:
        return "not measured / not applicable"
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value).replace("|", "\\|").replace("\n", " ")


def latest_results(root: Path) -> list[tuple[dict, Path]]:
    results = {}
    for path in sorted((root / "artifacts" / "evidence").glob("*/*/metadata.json")):
        metadata = json.loads(path.read_text())
        if not metadata["jj_version"].startswith(f"jj {JJ_VERSION}"):
            continue
        results[metadata["name"]] = (metadata, path.parent)
    return [results[key] for key in sorted(results)]


def generate(environment: Environment) -> Path:
    from jj_lab.scenarios.registry import scenarios

    results = latest_results(environment.root)
    expected = {s.name for s in scenarios()}
    missing = expected - {m["name"] for m, p in results}
    if missing:
        raise LabError("Run lab scenario verify first; missing: " + ", ".join(sorted(missing)))
    output = environment.guard(environment.root / "research")
    output.mkdir(exist_ok=True)
    headers = ["Scenario", "Category", *COLUMNS, "Evidence path"]
    matrix = "# Generated behavior matrix\n\n"
    matrix += f"jj {JJ_VERSION}. Generated from latest recorded run per scenario. "
    matrix += "Blank knowledge is reported explicitly, never converted to a negative result. "
    matrix += (
        "`jj resolve applicable` measures the built-in `:ours` tool, not every external tool. "
    )
    matrix += (
        "File/tree cases are exploratory; successful probes apply only to their fixtures. "
        "Manual resolution measures replacement of materialized regular files, not every "
        "possible tree-restructuring strategy. Git view reliability means interpretation "
        "of logical conflicts by ordinary Git, not validity of stored objects.\n\n"
    )
    matrix += "| " + " | ".join(headers) + " |\n|" + "|".join(["---"] * len(headers)) + "|\n"
    findings = "# Generated findings\n\nOnly PASS assertions below are reproduced observations. "
    findings += "Exploratory fixture observations are not universal invariants.\n\n"
    invariants = (
        "# Verified fixture invariants\n\nDocumentation-linked assertions that passed; "
        "scope is the named fixture on the pinned toolchain.\n\n"
    )
    limitations = "# Generated limitations\n\n"
    baseline = []
    for meta, path in results:
        observations = meta["observations"]
        evidence = str(path.relative_to(environment.root))
        if meta["category"] != "fundamentals":
            values = [meta["name"] + " (" + meta["status"] + ")", meta["category"]]
            values += [cell(observations.get(key)) for key in COLUMNS.values()]
            values += [f"[{evidence}](../{evidence}/summary.md)"]
            matrix += "| " + " | ".join(values) + " |\n"
        checks = json.loads((path / "assertions.json").read_text())
        findings += f"## {meta['name']} — {meta['status']} / {meta['classification']}\n\n"
        findings += f"Evidence: [{evidence}](../{evidence}/summary.md)\n\n"
        if meta["status"] == "PASS":
            findings += "".join("- " + c["name"] + "\n" for c in checks if c["passed"])
            if meta["classification"] == "DOCUMENTED_AND_REPRODUCED":
                invariants += (
                    f"- **{meta['name']}**: "
                    + "; ".join(c["name"] for c in checks if c["passed"])
                    + ".\n"
                )
        else:
            findings += "Failed: " + str(meta["error"]) + "\n"
        findings += "\n"
        if observations.get("known_limitation"):
            limitations += (
                f"- **{meta['name']}** ({meta['classification']}): "
                f"{observations['known_limitation']}\n"
            )
        baseline.append(
            dict(
                name=meta["name"],
                status=meta["status"],
                classification=meta["classification"],
                assertions=[dict(name=c["name"], passed=c["passed"]) for c in checks],
                observations={key: observations.get(key) for key in COLUMNS.values()},
            )
        )
    limitations += "\n## Documented boundaries (DOCUMENTED)\n\n"
    limitations += (
        "Git attributes, hooks, LFS and partial clones are unsupported or incomplete; "
        "submodules are not materialized; native jj workspaces differ from git-worktree. "
        "See https://docs.jj-vcs.dev/latest/git-compatibility/. "
        "These features are not experimentally covered by this harness.\n\n"
        "Runtime tests establish only the platform actually recorded. GitHub policies and "
        "authentication are outside local bare-remote transport. Simultaneous mutations "
        "of one fixture are unsupported; independent tests use independent roots.\n"
    )
    for name, text in [
        ("behavior-matrix.md", matrix),
        ("findings.md", findings),
        ("invariants.md", invariants),
        ("limitations.md", limitations),
    ]:
        (output / name).write_text(text)
    directory = output / "baselines" / f"jj-{JJ_VERSION}"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "results.json").write_text(json.dumps(baseline, indent=2) + "\n")
    return output
