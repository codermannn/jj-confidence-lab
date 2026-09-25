# Toolchain selection

Selected 2026-09-25: jj 0.45.1 (7c41cdeb16b6b321c64e789a966b6adf723816a5), checked against release API. Native research binary checksum: 6171582d0b5a98a1005cd9643faebff7936812ec264d7968a39d9cef3654a99b.

Python 3.13.12 slim-trixie image index: sha256:f1927c75e81efd1e091dbd64b6c0ecaa5630b38635a3d1c04034ac636e1f94c8.

uv 0.11.3 image index: sha256:90bbb3c16635e9627f49eec6539f956d70746c409209041800a0280b93152823.

Exact container Git and Python dependencies will be appended from built-image doctor evidence; no native version is substituted for container verification.

## Verified Linux amd64 container

- jj `0.45.1-7c41cdeb16b6b321c64e789a966b6adf723816a5`
- Git `2.47.3` from Debian trixie snapshot `20260920T000000Z`
- Python `3.13.12`
- uv `0.11.3 (x86_64-unknown-linux-musl)`; bundled `uv_build==0.11.3`
- Typer `0.27.2`, Rich `14.3.4`
- pytest `9.1.1`, Ruff `0.16.9`
- Python's complete resolved runtime/dev graph, hashes and platform markers: `uv.lock`
- Docker Engine `29.7.2` on this host; runtime tests use `network_mode: none`.

GitHub release SHA-256 for Linux amd64: `f35438350b5d61963aac5dd74ede510b31d6b9690769d1a6268cf058cc825f72`.
Linux arm64: `7349a43dd5a20dbc998b10114daa0ee63d2ab863fb822c7eb6b0ebca5903cc69`.
Both are verified during the respective image build. Only amd64 execution was tested here.

Native exploratory runs used the same jj version on macOS x86_64 with Apple Git
2.50.1. The committed empirical baseline is the container result, not this host result.

## Optional hosted remote

Forgejo 16.0.5 rootless; API reports `16.0.5+gitea-1.22.0` (the suffix is compatibility
metadata, not a different Forgejo release). Verified create/update/review/merge
and Git HTTP transport on Linux amd64. Image index digest:
`sha256:5effb7305584aca479b29fde6f9631a6dbe86ae798ae02eeea33a3666f0c0bf8`.
SQLite is bundled in that image; no external database or action runner.
