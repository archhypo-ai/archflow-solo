"""Self-contained, localized OAuth callback page for the system browser."""

from __future__ import annotations

import base64
import json
import re
from html import escape
from pathlib import Path

_ASSETS = Path(__file__).parent / "assets"
_STRINGS = json.loads((_ASSETS / "oauth-page.json").read_text(encoding="utf-8"))
_ICON = base64.b64encode((_ASSETS / "app-icon.png").read_bytes()).decode("ascii")
_TOKENS = (_ASSETS / "tokens.css").read_text(encoding="utf-8")
_DAY_TOKENS = re.search(r':root\[data-theme="day"\] \{([^}]+)\}', _TOKENS)
if _DAY_TOKENS is None:
    raise RuntimeError("Design system day theme is missing")
_SYSTEM_THEME = (
    '@media (prefers-color-scheme: light) { :root[data-theme="system"] {'
    + _DAY_TOKENS.group(1)
    + "} }"
)
_CSS = (
    _TOKENS + _SYSTEM_THEME + (_ASSETS / "oauth-page.css").read_text(encoding="utf-8")
)


def render_oauth_page(*, success: bool, language: str, theme: str | None) -> str:
    locale = "pt-BR" if language.lower().startswith("pt") else "en"
    texts = _STRINGS[locale]
    prefix = "success" if success else "error"
    title, description, hint = (
        escape(texts[f"{prefix}{key}"]) for key in ("Title", "Description", "Hint")
    )
    appearance = theme if theme in {"day", "night"} else "system"
    return f'''<!doctype html>
<html lang="{locale}" data-theme="{appearance}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · ArchHypo Flow</title>
<style>{_CSS}</style>
</head>
<body><main>
<img src="data:image/png;base64,{_ICON}" alt="">
<p class="brand">ArchHypo Flow</p>
<h1>{title}</h1><p>{description}</p><p class="hint">{hint}</p>
</main></body>
</html>'''
