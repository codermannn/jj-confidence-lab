#!/bin/sh
# Infrastructure-only initialization of disposable accounts; upstream entrypoint sets up app.ini.
set -eu
forgejo --config "$GITEA_APP_INI" migrate
for user in alice bob; do
    if ! forgejo --config "$GITEA_APP_INI" admin user list | awk '{print $2}' | grep -qx "$user"; then
        forgejo --config "$GITEA_APP_INI" admin user create \
            --username "$user" --email "$user@example.test" \
            --password 'Lab-only-password-2026!' --must-change-password=false
    fi
done
exec forgejo --config "$GITEA_APP_INI" web
