"""Native PyInstaller build specification for MusicScope."""

import sys
from importlib.util import find_spec
from pathlib import Path


project_root = Path(SPECPATH).parent
assets_directory = project_root / "src" / "musicscope" / "assets"
glfw_package = Path(find_spec("glfw").origin).parent
system_glfw_directories = (
    Path("/usr/lib/x86_64-linux-gnu"),
    Path("/usr/lib/aarch64-linux-gnu"),
    Path("/usr/lib/arm-linux-gnueabihf"),
    Path("/usr/local/lib"),
)
glfw_libraries = tuple(
    library
    for pattern in ("libglfw*.dylib", "libglfw*.so*", "glfw3.dll")
    for library in glfw_package.rglob(pattern)
)
system_glfw_libraries = tuple(
    library
    for directory in system_glfw_directories
    if directory.exists()
    for pattern in ("libglfw*.so*",)
    for library in directory.glob(pattern)
)
glfw_datas = [
    (
        str(library),
        str(Path("glfw") / library.relative_to(glfw_package).parent),
    )
    for library in glfw_libraries
]
# Linux distributions install GLFW outside of the Python package.  Put this
# fallback in pyGLFW's X11 lookup directory so the frozen executable remains
# self-contained.
glfw_datas.extend((str(library), "glfw/x11") for library in system_glfw_libraries)
icon_file = {
    "darwin": project_root / "packaging" / "musicscope.icns",
    "win32": project_root / "packaging" / "musicscope.ico",
}.get(sys.platform)

analysis = Analysis(
    [str(project_root / "src" / "musicscope" / "__main__.py")],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=[
        (str(assets_directory), "musicscope/assets"),
        *glfw_datas,
    ],
    hiddenimports=["_struct"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(project_root / "packaging" / "pyi_rth_glfw.py")],
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
    icon=str(icon_file) if icon_file is not None else None,
)

if sys.platform == "darwin":
    app = BUNDLE(
        executable,
        analysis.binaries,
        analysis.zipfiles,
        analysis.datas,
        name="MusicScope.app",
        icon=str(icon_file) if icon_file is not None else None,
        bundle_identifier="io.musicscope.app",
        info_plist={
            "NSCameraUsageDescription": "MusicScope uses the camera for its live visual background.",
        },
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
