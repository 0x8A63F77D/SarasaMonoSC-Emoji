#!/usr/bin/env python3
"""Inspect release completeness and resume interrupted asset publication."""
import argparse
import json
import os
from pathlib import Path
import subprocess

FAMILIES = ("SarasaMonoSCEmoji", "SarasaMonoSCEmojiLite", "SarasaMonoSCEmojiCOLRv1", "SarasaMonoSCEmojiLiteNerd")


def gh(*args):
    return subprocess.run(["gh", *args], capture_output=True, text=True)


def require(*args):
    result = gh(*args)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result


def inspect(repository, tag):
    result = gh("release", "view", tag, "--repo", repository, "--json", "isDraft,assets")
    if result.returncode:
        if "release not found" in result.stderr.lower():
            return None
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return json.loads(result.stdout)


def expected_names(tag):
    return {f"{family}-{tag}.zip" for family in FAMILIES}


def complete(release, tag, sizes=None):
    if release is None:
        return False
    assets = {asset["name"]: asset for asset in release["assets"]}
    for name in expected_names(tag):
        asset = assets.get(name)
        if not asset or asset.get("state") != "uploaded" or asset.get("size", 0) <= 0:
            return False
        if sizes is not None and asset["size"] != sizes[name]:
            return False
    return True


def should_build(repository, tag):
    release = inspect(repository, tag)
    return release is None or release["isDraft"] or not complete(release, tag)


def publish(repository, tag, sarasa_tag, target, directory):
    paths = [directory / name for name in sorted(expected_names(tag))]
    sizes = {path.name: path.stat().st_size for path in paths}
    if any(size <= 0 for size in sizes.values()):
        raise RuntimeError("Empty release package")
    title = f"Sarasa Mono SC Emoji — {sarasa_tag} ({tag})"
    release = inspect(repository, tag)
    if release is None:
        require("release", "create", tag, "--repo", repository, "--draft", "--target", target,
                "--title", title, "--notes-file", str(directory / "release-notes.md"))
    require("release", "upload", tag, *map(str, paths), "--repo", repository, "--clobber")
    release = inspect(repository, tag)
    if not complete(release, tag, sizes):
        raise RuntimeError("Release assets are incomplete; leaving draft for retry")
    require("release", "edit", tag, "--repo", repository, "--draft=false", "--latest",
            "--title", title, "--notes-file", str(directory / "release-notes.md"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("check", "publish"))
    args = parser.parse_args()
    repository, tag = os.environ["GITHUB_REPOSITORY"], os.environ["TAG"]
    if args.mode == "check":
        build = os.environ.get("EVENT_NAME") == "pull_request" or should_build(repository, tag)
        with open(os.environ["GITHUB_OUTPUT"], "a") as output:
            output.write(f"build={str(build).lower()}\n")
        print(f"{tag}: {'build/repair required' if build else 'published with all four packages'}")
    else:
        publish(repository, tag, os.environ["SARASA_TAG"], os.environ["GITHUB_SHA"], Path("dist"))


if __name__ == "__main__":
    main()
