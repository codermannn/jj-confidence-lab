"""A closed process environment: never inherit Git, jj or credential settings."""

import os
from dataclasses import dataclass
from pathlib import Path


class LabError(Exception):
    """An actionable laboratory failure."""


@dataclass(frozen=True)
class Environment:
    root: Path
    path: str

    @classmethod
    def load(cls) -> "Environment":
        root = Path(os.environ.get("LAB_ROOT", "/lab")).absolute()
        if root.is_symlink() or root == Path(root.anchor) or root == Path.home():
            raise LabError("LAB_ROOT must be a dedicated directory, not /, HOME or a symlink.")
        root.mkdir(parents=True, exist_ok=True)
        return cls(root.resolve(), os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"))

    def guard(self, path: Path, *, allow_root: bool = False) -> Path:
        target = path.resolve()
        if not target.is_relative_to(self.root) or (target == self.root and not allow_root):
            raise LabError(f"Path outside disposable lab area: {path}")
        return target

    def process(self, name: str = "Alice") -> dict[str, str]:
        home = self.guard(self.root / "home" / name.lower())
        home.mkdir(parents=True, exist_ok=True)
        config = self.guard(home / "jj.toml")
        contents = (
            f'[user]\nname = "{name}"\nemail = "{name.lower()}@example.test"\n'
            '[ui]\neditor = "true"\npager = "cat"\ncolor = "never"\n'
        )
        if not config.exists() or config.read_text() != contents:
            config.write_text(contents)
        return {
            "PATH": self.path,
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(home / ".config"),
            "JJ_CONFIG": str(config),
            "JJ_USER": name,
            "JJ_EMAIL": f"{name.lower()}@example.test",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_AUTHOR_NAME": name,
            "GIT_AUTHOR_EMAIL": f"{name.lower()}@example.test",
            "GIT_COMMITTER_NAME": name,
            "GIT_COMMITTER_EMAIL": f"{name.lower()}@example.test",
            "GIT_AUTHOR_DATE": "2026-01-01T12:00:00+00:00",
            "GIT_COMMITTER_DATE": "2026-01-01T12:00:00+00:00",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_ALLOW_PROTOCOL": "file",
            "GIT_CONFIG_COUNT": "3",
            "GIT_CONFIG_KEY_0": "init.defaultBranch",
            "GIT_CONFIG_VALUE_0": "main",
            "GIT_CONFIG_KEY_1": "core.hooksPath",
            "GIT_CONFIG_VALUE_1": "/dev/null",
            "GIT_CONFIG_KEY_2": "credential.helper",
            "GIT_CONFIG_VALUE_2": "",
            "EDITOR": "true",
            "VISUAL": "true",
            "PAGER": "cat",
            "GIT_PAGER": "cat",
            "TERM": "dumb",
            "NO_COLOR": "1",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "TZ": "UTC",
        }
