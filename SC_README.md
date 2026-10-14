# SarasaMonoSC-Emoji

[简体中文](README.md) · [Original TC project documentation](UPSTREAM_README.md)

Automated **Sarasa Mono SC + Noto Emoji** font releases. The four variants from [sspig0127/SarasaMonoTC-Emoji](https://github.com/sspig0127/SarasaMonoTC-Emoji) are preserved:

| Variant | Family | Emoji |
| --- | --- | --- |
| Color | `SarasaMonoSCEmoji` | CBDT/CBLC bitmap color |
| Lite | `SarasaMonoSCEmojiLite` | Monochrome outline |
| COLRv1 | `SarasaMonoSCEmojiCOLRv1` | Vector color |
| Nerd Lite | `SarasaMonoSCEmojiLiteNerd` | Monochrome + Nerd Fonts icons |

Each variant contains Regular, Italic, Bold and BoldItalic (16 TTF files total). Each ZIP also contains an offline `visual-check.html` and `coverage.json`: open the page and select matching TTF files, without installing or uploading them. The inspector verifies SHA-256, supports style/size switching, alignment grids and searchable coverage, and suppresses known missing or empty samples. To compare variants, import their coverage reports before loading their fonts. Coverage is source-relative cmap/direct ccmp structure, not a full shaping or Unicode conformance test.

## How it works

GitHub Actions checks for upstream changes **daily** (and can be manually dispatched). A low-frequency housekeeping commit prevents GitHub from suspending the schedule after 60 days of inactivity. Changes to any of these sources result in a new version fingerprint:

1. `sspig0127/SarasaMonoTC-Emoji` **main commit** (the Python/fontTools merge engine)
2. `be5invis/Sarasa-Gothic` **latest release** (`SarasaMonoSC-TTF-...7z`)
3. `googlefonts/noto-emoji` latest commits touching its **two 2D font files** (bitmap and COLRv1)
4. `google/fonts` latest commit affecting **NotoEmoji[wght].ttf**
5. `ryanoasis/nerd-fonts` **latest release**
6. Content hash of SC overlay scripts and CI config (so keepalive/doc edits do not trigger builds)

For a new fingerprint, the workflow downloads the exact source revisions, applies the SC adaptation, builds all four variants, runs all upstream regression tests and additional SC-specific font checks, then creates a GitHub Release with four ZIP files. A failed build/test **never publishes a Release**. Interrupted uploads retain a draft that subsequent runs repair; only a published release with all four uploaded packages is skipped. Fingerprint tags are `sc-auto-<hash>`; `provenance.json` is included with each variant for reproducibility.

**This is an auto-following source overlay, not a blind upstream Git merge.** The merge engine is taken from the upstream project, with a guarded SC adaptation that also preserves Color emoji sequence glyphs when internal names collide with CJK glyph names. SC-specific edits are not overwritten by Git merges. Any incompatible upstream change blocks the Release and surfaces a failed Actions run. Scheduled runs may be delayed by GitHub.

## Setup (GitHub)

This repository maintains the SC overlay and its workflow alongside the inherited TC source. The overlay can also be installed into another GitHub fork of the TC project. If using a fork, the installer archives inherited upstream workflows (`Release` and `Check upstream`) under `.github/upstream-workflows/`, outside the Actions workflow directory. This repository also guards its retained TC workflows to run only in the original upstream repository. The SC auto-build workflow is self-contained and does not require a Git remote named `upstream`. The installer preserves the target fork's `LICENSE` and `README.md`. In this repository, the original TC README is archived as `UPSTREAM_README.md`.

1. Fork this repository and enable Actions, or clone this repository and use `python sc/install_into_fork.py /path/to/another-tc-fork` to copy SC-specific files into an existing TC fork (see `SETUP_SC_CN.md`).
2. Push this overlay to its `main` branch. If you use a fork, its original files can remain, but the `sc/` overlay and `sc-autobuild.yml` control SC releases.
3. In **Settings → Actions → General → Workflow permissions**, choose **Read and write permissions** (needed to create Releases with `GITHUB_TOKEN`). Ensure Actions are enabled.
4. Open **Actions → Auto-build Sarasa Mono SC Emoji → Run workflow** to build immediately. Thereafter, the scheduled job automatically checks for changes daily.
5. Download the resulting variant packages under **Releases**.

No personal access token is needed for public upstream sources. API reads are authenticated using `GITHUB_TOKEN` to avoid unauthenticated rate limits.

## Development / testing

`python tests/test_overlay.py` runs local overlay tests without downloading fonts. GitHub Actions performs full font builds and regression checks on Linux. You can run the upstream source adapter manually as `python sc/adapt.py /path/to/upstream-clone`.

## Known limitations

- Auto-following the latest upstream commit can introduce breaking changes. This is intentional **fail-closed** behavior; the workflow goes red and does not silently produce an unverified font.
- Some COLRv1 emoji are necessarily omitted due to the TrueType glyph budget; the TC project's existing selection/priority logic is reused. SC may have a different budget, so a future upstream update may need explicit adaptation.
- Noto's 2026 GitHub 3D-only releases are **not** appropriate input for the original 2D merge engine. This workflow follows `googlefonts/noto-emoji` font-file commits and downloads from `2D/fonts/`.
- The font files are intentionally not committed to Git; releases carry the binaries.
- GitHub schedules are approximately daily, not a real-time webhook from third-party repositories.

## License and attribution

The merged fonts are derived from Sarasa Gothic, Noto Emoji and (Nerd Lite only) Nerd Fonts Symbols Only. Preserve the upstream copyright statements and licensing text. GitHub Release ZIPs include the upstream merge project's `LICENSE` (SIL Open Font License 1.1); Nerd Lite also includes the Nerd Fonts upstream `LICENSE`. The SC overlay's automation scripts are provided under `LICENSE-AUTOMATION` (MIT); do not replace the parent fork's OFL `LICENSE` file, but **the resulting fonts remain subject to their respective font licenses**, not MIT.

Upstream merge engine: https://github.com/sspig0127/SarasaMonoTC-Emoji

Sarasa Gothic: https://github.com/be5invis/Sarasa-Gothic

Noto Emoji: https://github.com/googlefonts/noto-emoji

Nerd Fonts: https://github.com/ryanoasis/nerd-fonts
