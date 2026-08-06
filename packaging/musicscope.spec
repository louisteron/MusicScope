"""Native PyInstaller build specification for MusicScope."""

import sys
from pathlib import Path


project_root = Path(SPECPATH).parent
assets_directory = project_root / "src" / "musicscope" / "assets"

analysis = Analysis(
    [str(project_root / "src" / "musicscope" / "__main__.py")],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=[(str(assets_directory), "musicscope/assets")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(analysis.pure)
executable = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="MusicScope",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)

if sys.platform == "darwin":
    app = BUNDLE(
        executable,
        analysis.binaries,
        analysis.zipfiles,
        analysis.datas,
        name="MusicScope.app",
        icon=None,
        bundle_identifier="io.musicscope.app",
    )
else:
    app = COLLECT(
        executable,
        analysis.binaries,
        analysis.zipfiles,
        analysis.datas,
        strip=False,
        upx=False,
        name="MusicScope",
    )
