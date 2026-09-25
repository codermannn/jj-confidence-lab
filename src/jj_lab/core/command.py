"""One subprocess boundary, including expected failures and complete diagnostics."""

import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from jj_lab.core.environment import Environment, LabError


@dataclass(frozen=True)
class CommandResult:
    argv: tuple[str, ...]
    cwd: str
    environment: dict[str, str]
    stdout: str
    stderr: str
    exit_code: int
    duration: float
    phase: str

    def require_success(self) -> "CommandResult":
        if self.exit_code:
            raise LabError(
                f"Command failed ({self.exit_code}): {' '.join(self.argv)}\n"
                f"{self.stdout}{self.stderr}"
            )
        return self


class CommandRunner:
    def __init__(self, environment: Environment):
        self.environment = environment
        self.records: list[CommandResult] = []
        self.phase = "fixture"

    def run(
        self,
        executable: str,
        args: list[str],
        cwd: Path,
        env: dict[str, str] | None = None,
        *,
        allow_failure: bool = False,
    ) -> CommandResult:
        self.environment.guard(cwd, allow_root=True)
        process_env = env if env is not None else self.environment.process()
        argv = (executable, *args)
        started = time.monotonic()
        try:
            result = subprocess.run(
                argv,
                cwd=cwd,
                env=process_env,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=60,
                shell=False,
            )
            stdout, stderr, code = result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired as exc:
            stdout = (exc.stdout or b"").decode(errors="replace")
            stderr = (exc.stderr or b"").decode(errors="replace") + "\nTimed out after 60s"
            code = 124
        except OSError as exc:
            stdout, stderr, code = "", str(exc), 127
        record = CommandResult(
            argv,
            str(cwd),
            process_env,
            stdout,
            stderr,
            code,
            time.monotonic() - started,
            self.phase,
        )
        self.records.append(record)
        return record if allow_failure else record.require_success()

    def event(self, action: str, path: Path, content: str = "") -> None:
        self.records.append(
            CommandResult(
                ("filesystem", action, str(path)),
                str(path.parent),
                {},
                content,
                "",
                0,
                0,
                self.phase,
            )
        )

    def serialized(self) -> list[dict]:
        return [asdict(record) for record in self.records]
