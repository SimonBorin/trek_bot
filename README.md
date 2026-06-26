# Star Trek Text Game Bot

Python port of a Tiny Basic 'trek' game
Ported to python3 </br>
[StarTrekWikiPage](https://en.wikipedia.org/wiki/Star_Trek_(1971_video_game))</br>
[Manual Page](https://github.com/SimonBorin/trek_bot/wiki/Manual)

## Local checks

The bot still uses the legacy `python-telegram-bot` v13 API, so run it on
Python 3.11 for now.

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements pytest
.venv/bin/python -m pytest
```

## Podman

Create `.env` from `.env.example` and fill in `BOT_TOKEN` and `MONGO_PASS`.

```bash
podman build -f Containerfile -t trek-bot .
podman compose -f compose.yml up -d
```

If `podman compose` is not installed on the VM, install the compose provider
or run the same `compose.yml` with `podman-compose`.
