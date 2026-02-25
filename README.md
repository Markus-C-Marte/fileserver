# fileserver

A lightweight Flask-based HTTP file server with a mobile-friendly web UI. Built to allow browsing and downloading files from a home file server via a phone connected over Tailscale.

The primary use case is accessing a ROM collection (GameCube, PS2, retro handhelds) without needing direct LAN access.

## How it works

- Serves the filesystem root (or any configured directory) over HTTP
- Homepage shows pinned quick-links defined in `pins.json`
- Mobile-optimized UI: tap a file to select it, press GET to download
- Address bar in the UI allows manual path navigation

## Files

| File | Purpose |
|------|---------|
| `fileserver_flask.py` | Main application |
| `template.html` | HTML developed with Claude assistance (see note below) |
| `pins.json` | Pinned directory shortcuts shown on the homepage |
| `run.sh` | Starts the Flask server in the correct venv |
| `flash-app.service` | systemd unit file |
| `install-service.sh` | Copies the unit file and enables the service |

## Dependencies

- Python 3
- Flask (`pip install flask`)
- A virtualenv at `/home/serv/.venvs/flask/` (as configured in `run.sh`)

## Configuration

### System-specific files

The following files are configured for a specific system and **must be adjusted** before use on any other machine:

- **`run.sh`** — hardcodes the virtualenv path (`/home/serv/.venvs/flask/`) and serve directory
- **`flash-app.service`** — hardcodes the user (`serv`), working directory, and mount path (`/srv/samba/EXT`)
- **`install-service.sh`** — hardcodes the source path when copying the unit file to `/etc/systemd/system/`

### Pinned links

Edit `pins.json` to set the quick-access directories shown on the homepage:

```json
[
  {"label": "Display Name", "path": "/absolute/path/to/directory"}
]
```

## Security warning

The server binds to `0.0.0.0` by default, meaning it listens on **all network interfaces**. This is intentional for Tailscale access but means the server is reachable from any interface the machine has.

**Do not run this on any machine that has ports forwarded to the internet.** There is no authentication. Anyone who can reach the port can browse and download the entire served directory tree.

If you need to restrict it to a specific interface (e.g. the Tailscale interface only), pass `--bind <tailscale-ip>` when starting the server.

## Notes on the web UI

The HTML/CSS/JS for the web UI (`template.html` and the inline template in `fileserver_flask.py`) was developed with assistance from Claude, as the original author is not experienced with HTML frontend work.
