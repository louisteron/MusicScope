# MusicScope V1 release checklist

V1 is the first public release. Local playlist playback is supported
on macOS and Linux when `mpv` is installed. CD support additionally requires a
working optical drive and `libdiscid`.

Before publishing a tag:

- Run `uv run ruff check .` and `uv run pytest`.
- Test an MP3 and FLAC playlist, drag/reorder/delete controls, audio output and
  lyrics on each target system.
- Test one physical audio CD and eject shortcut on macOS and Linux.
- On Windows, test visualisation and local playback; MPV IPC-driven track
  progression, seek and synchronized lyrics remain experimental.
- Confirm `.env` is absent from the commit and release artifacts.

## Artifacts

Pushing a tag such as `v1.0.0` launches the Release workflow. It builds one
native ZIP archive per operating system and publishes a normal GitHub release.
Tags containing a hyphen, such as `v1.1.0-beta.1`, are published as prereleases:

- macOS ARM64: `MusicScope-macos-arm64.zip`
- Linux x86_64: `MusicScope-linux-x86_64.zip`
- Windows x86_64: `MusicScope-windows-x86_64.zip`

Each artifact is built on its own target OS; do not reuse a macOS build on
Windows or Linux.

The Windows archive embeds the upstream [mpv Windows build](https://github.com/
shinchiro/mpv-winbuild-cmake) and its accompanying files. Keep these files in
the `mpv/` directory when redistributing the archive.
