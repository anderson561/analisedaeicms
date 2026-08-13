# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

datas = []
datas += collect_data_files("customtkinter")
datas += collect_data_files("tkinterdnd2")

a = Analysis(
    ["run_app.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=["pdfplumber", "openpyxl", "xlrd"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AuditaDAE",
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

# Modo "onedir": o .exe fica em uma pasta junto com suas dependências, em vez
# de um único arquivo que precisa se auto-extrair a cada execução. Isso evita
# a demora de 10-25s no início de cada abertura observada no modo onefile
# (extração para pasta temporária + nova varredura do antivírus a cada vez
# que o conteúdo do pacote muda).
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="AuditaDAE",
)
