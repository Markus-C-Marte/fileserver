#!/usr/bin/env python3
"""
fileserver_flask.py -- HTTP file server with custom web UI (Flask).
Requires: pip install flask
Usage: python3 fileserver_flask.py [--port N] [--bind ADDR] [--directory DIR]
"""
import argparse
import html
import json
import os
import posixpath
import urllib.parse
from pathlib import Path

from flask import Flask, Response, abort, redirect, request, send_file

# ── Pinned quick-links (shown on homepage at /) ───────────────────────────────
# Loaded from pins.json next to this script.
# Format: [{"label": "Name", "path": "/url/path/to/directory"}, ...]
# If the file is missing or empty, no homepage is shown.
def _load_pinned():
    p = Path(__file__).with_name('pins.json')
    if not p.exists():
        return []
    with open(p) as f:
        data = json.load(f)
    return [(entry['label'], entry['path']) for entry in data]

PINNED = _load_pinned()

# ── HTML template ─────────────────────────────────────────────────────────────
_PAGE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>@@TITLE@@</title>
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: system-ui, -apple-system, sans-serif;
    background: #1a1a1a;
    color: #e0e0e0;
    display: flex;
    flex-direction: column;
    height: 100dvh;
    overflow: hidden;
}
#top {
    padding: 10px 16px 8px;
    background: #252525;
    border-bottom: 1px solid #333;
    flex-shrink: 0;
}
#breadcrumb {
    font-size: 0.8rem;
    color: #888;
    margin-bottom: 8px;
    word-break: break-all;
    line-height: 1.6;
}
#breadcrumb a { color: #7ab4ff; text-decoration: none; }
#breadcrumb a:active { text-decoration: underline; }
#breadcrumb .cur { color: #e0e0e0; }
#addr-form { display: flex; gap: 8px; }
#addr-input {
    flex: 1;
    background: #333;
    border: 1px solid #444;
    color: #e0e0e0;
    padding: 7px 10px;
    border-radius: 4px;
    font-size: 0.9rem;
    min-width: 0;
    font-family: monospace;
}
#addr-input:focus { outline: none; border-color: #7ab4ff; }
#go-btn {
    padding: 7px 14px;
    background: #3a3a3a;
    border: 1px solid #555;
    color: #e0e0e0;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
    white-space: nowrap;
    -webkit-tap-highlight-color: transparent;
}
#go-btn:active { background: #4a4a4a; }
#middle {
    flex: 1;
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
}
.entry {
    display: flex;
    align-items: center;
    padding: 0 16px;
    min-height: 48px;
    border-bottom: 1px solid #242424;
    cursor: pointer;
    user-select: none;
    text-decoration: none;
    color: inherit;
    gap: 10px;
    -webkit-tap-highlight-color: transparent;
}
.entry:active { background: #2a2a2a; }
.entry.selected { background: #1e3a5f; }
.badge {
    font-size: 0.65rem;
    font-family: monospace;
    padding: 2px 5px;
    border-radius: 3px;
    flex-shrink: 0;
    letter-spacing: 0.05em;
}
.entry.dir .badge  { background: #3a2f00; color: #f0c070; }
.entry.dir .name   { color: #f0c070; }
.entry.file .badge { background: #282828; color: #666; }
.entry.file.selected .name { color: #7ab4ff; }
.name { font-size: 0.95rem; word-break: break-all; }
#bottom {
    padding: 12px 16px;
    background: #252525;
    border-top: 1px solid #333;
    display: flex;
    justify-content: center;
    flex-shrink: 0;
}
#get-btn {
    padding: 11px 52px;
    background: #2a6fdb;
    border: none;
    color: #fff;
    font-size: 1rem;
    font-weight: 600;
    border-radius: 6px;
    cursor: pointer;
    letter-spacing: 0.08em;
    min-width: 140px;
    -webkit-tap-highlight-color: transparent;
}
#get-btn:active { background: #1a5fc8; }
#overlay {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.65);
    z-index: 100;
    align-items: center;
    justify-content: center;
}
#overlay.show { display: flex; }
#overlay-box {
    background: #2c2c2c;
    border: 1px solid #555;
    border-radius: 8px;
    padding: 28px 44px;
    font-size: 1rem;
    color: #ccc;
    text-align: center;
}
</style>
</head>
<body>
<div id="top">
  <div id="breadcrumb">@@BREADCRUMB@@</div>
  <form id="addr-form" onsubmit="navigate(event)">
    <input id="addr-input" type="text" value="@@URL_PATH@@" autocomplete="off" spellcheck="false">
    <button id="go-btn" type="submit">Go</button>
  </form>
</div>
<div id="middle">
@@ENTRIES@@
</div>
<div id="bottom">
  <button id="get-btn" onclick="doGet()">GET</button>
</div>
<div id="overlay" onclick="closeOverlay()">
  <div id="overlay-box">No file selected</div>
</div>
<script>
var selected = null;

function selectFile(el) {
    if (selected && selected !== el) selected.classList.remove('selected');
    if (selected === el) { selected = null; el.classList.remove('selected'); return; }
    el.classList.add('selected');
    selected = el;
}

function doGet() {
    if (!selected) { document.getElementById('overlay').classList.add('show'); return; }
    window.location.href = selected.dataset.url;
}

function closeOverlay() {
    document.getElementById('overlay').classList.remove('show');
}

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeOverlay();
});

function navigate(e) {
    e.preventDefault();
    var val = document.getElementById('addr-input').value.trim();
    if (!val) return;
    if (!val.startsWith('/')) val = '/' + val;
    window.location.href = val;
}
</script>
</body>
</html>
"""


def _render_page(title, breadcrumb, url_path, entries):
    return (
        _PAGE
        .replace('@@TITLE@@',      title)
        .replace('@@BREADCRUMB@@', breadcrumb)
        .replace('@@URL_PATH@@',   html.escape(url_path, quote=True))
        .replace('@@ENTRIES@@',    entries)
    )


def _make_breadcrumb(url_path):
    parts = [p for p in url_path.split('/') if p]
    items = ['<a href="/">root</a>']
    for i, part in enumerate(parts):
        href  = '/' + '/'.join(parts[:i + 1]) + '/'
        label = html.escape(urllib.parse.unquote(part))
        if i == len(parts) - 1:
            items.append(f'<span class="cur">{label}</span>')
        else:
            items.append(f'<a href="{html.escape(href)}">{label}</a>')
    return ' / '.join(items)


def _make_entries(fs_path, url_path):
    try:
        names = os.listdir(fs_path)
    except PermissionError:
        return '<div style="padding:16px;color:#c66">Permission denied.</div>'
    except OSError as exc:
        return f'<div style="padding:16px;color:#c66">{html.escape(str(exc))}</div>'

    dirs  = sorted(n for n in names if (fs_path / n).is_dir())
    files = sorted(n for n in names if not (fs_path / n).is_dir())
    lines = []

    stripped = url_path.rstrip('/')
    if stripped:
        parent = str(Path(stripped).parent)
        if parent != '/':
            parent += '/'
        lines.append(
            f'<a class="entry dir" href="{html.escape(parent)}">'
            f'<span class="badge">dir</span>'
            f'<span class="name">..</span></a>'
        )

    for name in dirs:
        entry_url = url_path.rstrip('/') + '/' + urllib.parse.quote(name) + '/'
        lines.append(
            f'<a class="entry dir" href="{html.escape(entry_url)}">'
            f'<span class="badge">dir</span>'
            f'<span class="name">{html.escape(name)}</span></a>'
        )

    for name in files:
        entry_url = url_path.rstrip('/') + '/' + urllib.parse.quote(name)
        lines.append(
            f'<div class="entry file" data-url="{html.escape(entry_url)}" onclick="selectFile(this)">'
            f'<span class="badge">file</span>'
            f'<span class="name">{html.escape(name)}</span></div>'
        )

    return '\n'.join(lines)


def _make_homepage():
    items = [
        '<a class="entry dir" href="/?browse">'
        '<span class="badge">dir</span>'
        '<span class="name">/ (browse root)</span></a>'
    ]
    for label, url in PINNED:
        u = url.rstrip('/') + '/'
        items.append(
            f'<a class="entry dir" href="{html.escape(u)}">'
            f'<span class="badge">dir</span>'
            f'<span class="name">{html.escape(label)}</span></a>'
        )
    return _render_page(
        title='Home',
        breadcrumb='<span class="cur">home</span>',
        url_path='/',
        entries='\n'.join(items),
    )


# ── Flask app ─────────────────────────────────────────────────────────────────
app  = Flask(__name__)
ROOT = Path('.')  # set in main()


def _resolve(url_path):
    """Resolve a URL path to a filesystem path, or abort if outside ROOT."""
    clean = posixpath.normpath('/' + url_path.lstrip('/'))
    try:
        fs = (ROOT / clean.lstrip('/')).resolve()
        fs.relative_to(ROOT)
    except (OSError, ValueError):
        abort(403)
    return fs, clean


@app.route('/', defaults={'url_path': ''})
@app.route('/<path:url_path>')
def serve(url_path):
    if not url_path and PINNED and 'browse' not in request.args:
        return Response(_make_homepage(), mimetype='text/html; charset=utf-8')

    fs_path, clean = _resolve(url_path)

    if not fs_path.exists():
        abort(404)

    if fs_path.is_dir():
        if not ('/' + url_path).endswith('/'):
            return redirect('/' + url_path + '/')
        dir_url = '/' + url_path.rstrip('/') + '/'
        page = _render_page(
            title=dir_url,
            breadcrumb=_make_breadcrumb(dir_url),
            url_path=dir_url,
            entries=_make_entries(fs_path, dir_url),
        )
        return Response(page, mimetype='text/html; charset=utf-8')

    return send_file(fs_path, as_attachment=True)


def main():
    global ROOT
    ap = argparse.ArgumentParser(description='File server with custom web UI (Flask)')
    ap.add_argument('--port',      '-p', type=int, default=8080,      help='Port (default 8080)')
    ap.add_argument('--bind',      '-b', default='0.0.0.0',           help='Bind address')
    ap.add_argument('--directory', '-d', default='.',  metavar='DIR', help='Root directory to serve')
    args = ap.parse_args()

    ROOT = Path(args.directory).resolve()
    print(f'Serving  {ROOT}')
    print(f'Listening http://{args.bind}:{args.port}/')
    app.run(host=args.bind, port=args.port)


if __name__ == '__main__':
    main()
