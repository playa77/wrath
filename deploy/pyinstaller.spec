# Version: 0.2.0 | 2026-11-02
"""One-folder desktop bundle including read-only content, font and metadata."""
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, copy_metadata

root=Path(SPECPATH).parent
analysis=Analysis([str(root/'src/cradle/main.py')],pathex=[str(root/'src')],
    binaries=[],datas=[(str(root/'src/cradle/content'),'cradle/content'),
                       (str(root/'src/cradle/assets'),'cradle/assets')]+copy_metadata('cradle-wrath'),
    hiddenimports=collect_submodules('cradle.engine'),hookspath=[],runtime_hooks=[],excludes=[])
pyz=PYZ(analysis.pure)
exe=EXE(pyz,analysis.scripts,[],exclude_binaries=True,name='cradle',debug=False,
    bootloader_ignore_signals=False,strip=False,upx=False,console=True)
collection=COLLECT(exe,analysis.binaries,analysis.datas,strip=False,upx=False,name='cradle')
