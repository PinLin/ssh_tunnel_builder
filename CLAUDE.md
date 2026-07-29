# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

SSH Tunnel Builder is a single-file Python CLI tool (`tunnel.py`) that creates persistent SSH tunnel system services. Services start at boot and auto-reconnect on disconnect.

## Usage

```bash
# Create a tunnel
python3 tunnel.py new <name> <ssh_args>

# List tunnels
python3 tunnel.py ls

# Remove a tunnel
python3 tunnel.py rm <name>
```

The old command names (`make`, `list`, `remove`) are still accepted as hidden
aliases — they are registered as separate subparsers (not `add_parser(aliases=)`,
which Python 2 lacks) and normalized through `COMMAND_ALIASES` in `main()`.

## Architecture

Everything lives in `tunnel.py`. The script detects the OS at runtime (`platform.system()`) and delegates to one of two backend classes:

- **`Systemd`** (Linux) — writes a `.service` file to `/etc/systemd/system/`, then enables and starts it via `systemctl`.
- **`Launchd`** (macOS/Darwin) — writes a `.plist` file to `/Library/LaunchDaemons/`, then loads it via `launchctl`.

Both classes follow the same interface: `make_tunnel(name, ssh_args)`, `list_tunnels()`, `remove_tunnel(name)`.

Template files are in `systemd/ssh-tunnel.service` and `launchd/com.ssh-tunnel.plist`. They use Python `.format()` placeholders (`{username}`, `{ssh_args}`, `{service_name}`). The Launchd template splits `ssh_args` on spaces as separate `<string>` XML elements; the Systemd template inlines them as a single string.

SSH options baked into both templates: `-NT -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3`.

Service naming convention:
- Systemd: `ssh-tunnel-<name>.service`
- Launchd: `com.ssh-tunnel-<name>.plist` (label: `com.ssh-tunnel-<name>`)

The script auto-prepends `sudo` when not running as root (`os.getuid() != 0`).
