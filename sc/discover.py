#!/usr/bin/env python3
"""Resolve source revisions and compute reproducible, content-addressed Release tags."""
from __future__ import annotations

import hashlib
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://api.github.com/"


def api(path: str):
    req = urllib.request.Request(
        urllib.parse.urljoin(API, path),
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "SarasaMonoSC-Emoji-upstream-check",
            **({"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"} if os.environ.get("GITHUB_TOKEN") else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=45) as response:
        return json.load(response)


def source_fingerprint(sources: dict) -> str:
    raw = json.dumps(sources, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def overlay_fingerprint(root: Path) -> str:
    """Hash only build-relevant overlay files, not keepalive/documentation commits."""
    names = [Path('.github/workflows/sc-autobuild.yml'), Path('tests/test_overlay.py'), Path('tests/test_coverage.py')]
    names += [p.relative_to(root) for p in sorted((root / 'sc').glob('*.py'))]
    names += [p.relative_to(root) for p in sorted((root / 'sc' / 'preview').glob('*.html'))]
    hasher = hashlib.sha256()
    for name in sorted(names):
        path = root / name
        hasher.update(name.as_posix().encode('utf-8'))
        hasher.update(b'\0')
        hasher.update(path.read_bytes())
        hasher.update(b'\0')
    return hasher.hexdigest()


def discover() -> dict:
    google_font_path = "ofl/notoemoji/NotoEmoji[wght].ttf"
    query = urllib.parse.urlencode({"path": google_font_path, "per_page": "1"})
    google_history = api(f"repos/google/fonts/commits?{query}")

    def last_changed(path: str) -> str:
        q = urllib.parse.urlencode({"path": path, "per_page": "1"})
        result = api(f"repos/googlefonts/noto-emoji/commits?{q}")
        if not result:
            raise ValueError(f"No commits found for {path}")
        return result[0]["sha"]

    if not google_history:
        raise ValueError(f"No commits found for {google_font_path}")
    sources = {
        "merge_project": {
            "repo": "sspig0127/SarasaMonoTC-Emoji",
            "ref": api("repos/sspig0127/SarasaMonoTC-Emoji/commits/main")["sha"],
        },
        "sarasa": {
            "repo": "be5invis/Sarasa-Gothic",
            "tag": api("repos/be5invis/Sarasa-Gothic/releases/latest")["tag_name"],
        },
        "noto_emoji": {
            "repo": "googlefonts/noto-emoji",
            # New Noto release tags may contain 3D-only assets. Pin each 2D font to its last file commit.
            "color_path": "2D/fonts/NotoColorEmoji.ttf",
            "color_ref": last_changed("2D/fonts/NotoColorEmoji.ttf"),
            "colrv1_path": "2D/fonts/Noto-COLRv1.ttf",
            "colrv1_ref": last_changed("2D/fonts/Noto-COLRv1.ttf"),
        },
        "noto_mono": {
            "repo": "google/fonts",
            "ref": google_history[0]["sha"],
            "path": google_font_path,
        },
        "nerd_fonts": {
            "repo": "ryanoasis/nerd-fonts",
            "tag": api("repos/ryanoasis/nerd-fonts/releases/latest")["tag_name"],
        },
        "sc_overlay": {
            "repository": os.environ.get("GITHUB_REPOSITORY", "local"),
            "content_sha256": overlay_fingerprint(Path(__file__).resolve().parents[1]),
        },
    }
    return sources


def main() -> None:
    sources = discover()
    tag = "sc-auto-" + source_fingerprint(sources)
    payload = {"tag": tag, "sources": sources, "discovered_at": datetime.now(timezone.utc).isoformat()}
    Path("provenance.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as f:
            f.write(f"tag={tag}\n")
            f.write(f"merge_sha={sources['merge_project']['ref']}\n")
            f.write(f"sarasa_tag={sources['sarasa']['tag']}\n")
            f.write(f"noto_color_sha={sources['noto_emoji']['color_ref']}\n")
            f.write(f"noto_colrv1_sha={sources['noto_emoji']['colrv1_ref']}\n")
            f.write(f"mono_sha={sources['noto_mono']['ref']}\n")
            f.write(f"nerd_tag={sources['nerd_fonts']['tag']}\n")
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
