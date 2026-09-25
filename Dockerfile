FROM ghcr.io/astral-sh/uv:0.11.3@sha256:90bbb3c16635e9627f49eec6539f956d70746c409209041800a0280b93152823 AS uv
FROM python:3.13.12-slim-trixie@sha256:f1927c75e81efd1e091dbd64b6c0ecaa5630b38635a3d1c04034ac636e1f94c8
COPY --from=uv /uv /uvx /usr/local/bin/
# Snapshot pins transitive Debian packages as well as Git; no floating apt mirror.
RUN rm -f /etc/apt/sources.list.d/debian.sources && \
    printf 'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/20260920T000000Z trixie main\n' > /etc/apt/sources.list && \
    apt-get update && apt-get install -y --no-install-recommends git ca-certificates curl shellcheck && \
    rm -rf /var/lib/apt/lists/*
ARG TARGETARCH
ARG JJ_VERSION=0.45.1
RUN case "$TARGETARCH" in \
      amd64) triple=x86_64-unknown-linux-musl; checksum=f35438350b5d61963aac5dd74ede510b31d6b9690769d1a6268cf058cc825f72 ;; \
      arm64) triple=aarch64-unknown-linux-musl; checksum=7349a43dd5a20dbc998b10114daa0ee63d2ab863fb822c7eb6b0ebca5903cc69 ;; \
      *) exit 1 ;; esac && \
    curl -fsSL "https://github.com/jj-vcs/jj/releases/download/v${JJ_VERSION}/jj-v${JJ_VERSION}-${triple}.tar.gz" -o /tmp/jj.tar.gz && \
    echo "$checksum  /tmp/jj.tar.gz" | sha256sum -c - && \
    tar -xzf /tmp/jj.tar.gz -C /usr/local/bin ./jj && rm /tmp/jj.tar.gz
ENV UV_CACHE_DIR=/opt/uv-cache
WORKDIR /opt/lab
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-install-project
COPY . .
RUN uv sync --locked
ENV LAB_ROOT=/lab UV_OFFLINE=1 UV_NO_SYNC=1 UV_PYTHON_DOWNLOADS=never \
    PATH="/opt/lab/.venv/bin:$PATH" HOME=/lab/home \
    XDG_CONFIG_HOME=/lab/home/.config GIT_CONFIG_NOSYSTEM=1 \
    GIT_CONFIG_GLOBAL=/dev/null JJ_CONFIG=/opt/lab/lab-config.toml \
    GIT_AUTHOR_NAME=Alice GIT_AUTHOR_EMAIL=alice@example.test \
    GIT_COMMITTER_NAME=Alice GIT_COMMITTER_EMAIL=alice@example.test \
    GIT_TERMINAL_PROMPT=0 GIT_ALLOW_PROTOCOL=file \
    EDITOR=true VISUAL=true PAGER=cat GIT_PAGER=cat TZ=UTC LANG=C.UTF-8
RUN mkdir -p /lab/home && git --version > /opt/lab/git-version.txt
ENTRYPOINT ["uv", "run", "--locked", "lab"]
CMD ["--help"]
