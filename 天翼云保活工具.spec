# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['improved_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('accounts_config.json', '.'), ('my.json', '.'), ('msedgedriver.exe', '.'), ('static', 'static'), ('logs', 'logs')],
    hiddenimports=['tkinter', 'tkinter.ttk', 'tkinter.scrolledtext', 'tkinter.filedialog', 'tkinter.messagebox', 'selenium', 'selenium.webdriver', 'selenium.webdriver.edge', 'selenium.webdriver.common', 'requests', 'muggle_ocr', 'PIL', 'logging', 'json', 'threading', 'schedule'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='天翼云保活工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='天翼云保活工具',
)
