# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main_menu.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets/*.png', 'assets'),
        ('sections/*.py', 'sections'),
        ('gui_autoruns_style.py', '.'),
        ('TTFD.Cleaner.Cli.exe', '.'),
    ],
    hiddenimports=[
        'PIL._tkinter_finder',
        'sections.cleaning_window',
        'sections.reports_window',
        'sections.startup_window',
        'sections.browsers_window',
        'sections.apps_window',
        'sections.exclusions_window',
        'gui_autoruns_style',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TTFD-Cleaner-Menu',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True,
    icon=None,
)
