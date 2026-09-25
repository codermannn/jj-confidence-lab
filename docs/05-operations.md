# Operations and troubleshooting

## Normal session

```sh
# Start or rebuild the isolated lab and its services.
./lab start
./lab scenario list
./lab state
./lab scenario run working-copy
./lab xray
./lab why
./lab forge run
./lab forge status
```

The same common workflows are available through the readable Make targets:

```sh
# List all available shortcuts.
make help
# Start the lab, run the quality gate, or run the hosted PR experiment.
make start
make check
make forge
```

`Makefile` is only a convenience facade. `./lab` remains the canonical
interface because it owns Docker/Podman detection, Compose forwarding, and
interactive shell handling.

`./lab shell` opens a shell in the lab container. Inside it, the current
fixture path is available as `/lab/active`; enter Alice's workspace with:

```sh
# Enter Alice’s generated workspace and inspect jj state.
cd "$(cat /lab/active)/alice"
jj status
jj log -r '@ | @-'
```

Commands outside that shell run on the host. Type `exit` when the in-container
inspection is complete.

## If the UI is unavailable

```sh
# Inspect or run the local Forgejo-backed workflow.
./lab forge doctor
docker compose -f compose.yaml -f compose.forgejo.yaml ps
docker compose -f compose.yaml -f compose.forgejo.yaml logs --tail=100 forgejo
```

The UI is published only at [http://localhost:3080](http://localhost:3080).
The API is reachable from the lab client as `http://forgejo:3000`.

## If a fixture is stale

```sh
# Reset disposable fixtures while retaining evidence.
./lab reset
./lab state
```

For all generated scenario repositories:

```sh
# Reset disposable fixtures while retaining evidence.
./lab reset --all
```

These commands preserve evidence. A full volume reset is the separate,
destructive `docker compose down -v` operation documented in
[Storage and volumes](03-storage-and-volumes.md).

## Inspect an unexpected result

```sh
# List the recent repository operations.
jj op log -n 8

# Show the patch made by the current operation.
jj op show -p @

# Undo the latest local operation.
jj undo
```

For a specific checkpoint, copy its operation ID from `jj op log`:

```sh
# Inspect an earlier state without mutating the repository.
jj --at-op <operation-id> log -r '@ | @-'

# Restore that state by creating a new operation.
jj op restore <operation-id>
```

## Verify source/image parity after edits

The image contains the source as it existed at build time. After editing Python
or shell code, rebuild before testing:

```sh
# Start or rebuild the isolated lab and its services.
./lab start
./lab check
```

For native development only, `uv run --locked lab ...` runs the checkout
directly, while normal learner commands should use `./lab` so the pinned image,
isolated environment, and named volume are in effect.
