"""Optional local Forgejo boundary. URLs and disposable identities are fixed."""

import base64
import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

from jj_lab.core.command import CommandResult, CommandRunner
from jj_lab.core.environment import LabError
from jj_lab.repos.factory import Actor
from jj_lab.vcs import adapters

BASE_URL = "http://forgejo:3000"
WEB_URL = "http://localhost:3080"
PASSWORD = "Lab-only-password-2026!"  # Public, disposable localhost-only lab credential.
VERSION = "16.0.5"


def authorization(actor: str) -> str:
    if actor not in {"alice", "bob"}:
        raise LabError("Forgejo lab only supports Alice and Bob.")
    return "Basic " + base64.b64encode(f"{actor}:{PASSWORD}".encode()).decode()


class ForgejoAPIError(LabError):
    def __init__(self, status: int, body: str):
        self.status = status
        self.body = body
        super().__init__(f"Forgejo HTTP {status}: {body}")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise LabError("Forgejo API redirects are not allowed.")


class Forgejo:
    def __init__(self, runner: CommandRunner):
        self.runner = runner
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def request(self, method: str, path: str, body: dict | None = None, *, actor: str = "alice"):
        if not re.fullmatch(
            r"/(version|user|user/repos|repos/alice/lab-[a-z0-9-]+(?:/[a-z0-9/-]+)?)", path
        ):
            raise LabError(f"Not a local lab API route: {path}")
        url = BASE_URL + "/api/v1" + path
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={"Authorization": authorization(actor), "Content-Type": "application/json"},
        )
        start = time.monotonic()
        status = 0
        try:
            with self.opener.open(request, timeout=15) as response:
                text = response.read().decode()
                status = response.status
        except urllib.error.HTTPError as exc:
            text, status = exc.read().decode(), exc.code
        except (OSError, urllib.error.URLError) as exc:
            text, status = str(exc), 503
        result = CommandResult(
            ("HTTP", method, url, json.dumps(body)),
            str(self.runner.environment.root),
            {"lab_actor": actor},
            text,
            f"HTTP {status}",
            0 if 200 <= status < 300 else status,
            time.monotonic() - start,
            self.runner.phase,
        )
        self.runner.records.append(result)
        if result.exit_code:
            raise ForgejoAPIError(status, text)
        return json.loads(text) if text else None

    def doctor(self) -> dict:
        version = self.request("GET", "/version")
        if version["version"].split("+", 1)[0] != VERSION:
            raise LabError(f"Expected Forgejo {VERSION}, got {version}. Run ./lab forge start.")
        for name in ("alice", "bob"):
            user = self.request("GET", "/user", actor=name)
            if user["login"] != name:
                raise LabError(f"Forgejo actor initialization failed: {name}")
        return version


@dataclass(frozen=True)
class HostedRemote:
    actor: Actor
    name: str

    @property
    def url(self) -> str:
        if not re.fullmatch(r"lab-[a-z0-9-]+", self.name):
            raise LabError("Invalid Forgejo repository name.")
        return f"{BASE_URL}/alice/{self.name}.git"

    def environment(self) -> dict[str, str]:
        env = self.actor.environment
        env.update(
            GIT_ALLOW_PROTOCOL="file:http",
            GIT_CONFIG_COUNT="5",
            GIT_CONFIG_KEY_3=f"http.{BASE_URL}/.extraHeader",
            GIT_CONFIG_VALUE_3="Authorization: " + authorization(self.actor.name.lower()),
            GIT_CONFIG_KEY_4="http.followRedirects",
            GIT_CONFIG_VALUE_4="false",
        )
        return env

    def validate(self):
        owner = self.actor.runner.environment.guard(self.actor.path.parent / ".forgejo-origin")
        if not owner.is_file() or owner.read_text() != self.url:
            raise LabError("Forgejo origin is not registered to this lab fixture.")
        for flags in ([], ["--push"]):
            actual = adapters.git(
                self.actor.runner,
                self.actor.path,
                ("remote", "get-url", *flags, "--all", "forgejo"),
                self.actor.environment,
            ).stdout.splitlines()
            if actual != [self.url]:
                raise LabError("Forgejo remote changed; refusing transport.")

    def git(self, command: str, *args: str) -> CommandResult:
        if command not in {"push", "fetch", "ls-remote"}:
            raise LabError("Hosted Git adapter only supports push/fetch/ls-remote.")
        self.validate()
        return adapters.git(
            self.actor.runner, self.actor.path, (command, "forgejo", *args), self.environment()
        )

    def jj(self, command: str, *args: str) -> CommandResult:
        if command not in {"push", "fetch"}:
            raise LabError("Hosted jj adapter only supports push/fetch.")
        self.validate()
        return adapters.jj(
            self.actor.runner,
            self.actor.path,
            ("git", command, "--remote", "forgejo", *args),
            self.environment(),
        )

    def refs(self) -> dict[str, str]:
        output = self.git("ls-remote", "refs/heads/*").stdout
        return {name: commit for commit, name in (line.split("\t") for line in output.splitlines())}
