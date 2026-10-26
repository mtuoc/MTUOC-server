# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# --- DETECTOR DINÀMIC PER A HF_XET DINS DEL DESCARREGADOR ---
import importlib.util
import os
import sys

download_datas = []
try:
    # 1. Busquem la carpeta de codi de hf_xet
    spec_xet = importlib.util.find_spec('hf_xet')
    if spec_xet and spec_xet.submodule_search_locations:
        xet_dir = spec_xet.submodule_search_locations[0]
        download_datas.append((xet_dir, 'hf_xet'))
        print(f"--> PyInstaller: S'ha localitzat la carpeta binària de 'hf_xet'")
        
        # 2. SEGELL DE REGISTRE: Busquem la seva carpeta de metadades (.dist-info) al site-packages
        site_packages_dir = os.path.dirname(xet_dir)
        for folder in os.listdir(site_packages_dir):
            if folder.startswith('hf_xet-') and folder.endswith('.dist-info'):
                dist_info_path = os.path.join(site_packages_dir, folder)
                download_datas.append((dist_info_path, folder))
                print(f"--> PyInstaller: S'ha localitzat i s'injectarà el registre oficial: {folder}")
except Exception as e_xet:
    print(f"Avís detector de hf_xet: {e_xet}")
# -----------------------------------------------------------

# --- DETECTOR DINÀMIC DE BINARIS CUBLAS PER A CTRANSLATE2 ---
cublas_binaries = []
try:
    # Busquem on està instal·lada exactament la llibreria nvidia-cublas al teu entorn virtual
    spec_cublas = importlib.util.find_spec('nvidia.cublas.lib')
    if spec_cublas and spec_cublas.submodule_search_locations:
        cublas_dir = spec_cublas.submodule_search_locations[0]
        # Cerquem qualsevol fitxer libcublas de la GPU (.so a Linux, .dll a Windows, .dylib a Mac)
        for f in os.listdir(cublas_dir):
            if 'libcublas' in f:
                cublas_binaries.append((os.path.join(cublas_dir, f), '.'))
                print(f"--> PyInstaller: S'ha trobat i s'injectarà la llibreria gràfica: {f}")
except Exception as e_cublas:
    print(f"Avís detector de Cublas: {e_cublas}")
# -----------------------------------------------------------


# 1. GESTOR GRÀFIC
a_manager = Analysis(
    ['MTUOC-server-manager.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['psutil', 'huggingface_hub', 'PyQt6'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 2. SERVIDOR PRINCIPAL
a_server = Analysis(
    ['MTUOC-server.py'],
    pathex=[],
    binaries=cublas_binaries,  
    datas=[('src', 'src')],   
    hiddenimports=[
        'html', 'pyyaml', 'requests', 'flask', 'waitress', 'websocket-client',
        'sentencepiece', 'sacremoses', 'ftfy', 'protobuf', 'jieba', 'fugashi',
        'torch', 'transformers', 'ctranslate2', 'nvidia-cublas-cu12', 'ollama', 'pydantic', 
        'accelerate', 'deepl', 'google.cloud.translate', 'huggingface_hub'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['eole'],  # S'elimina 'pydantic' d'aquí per evitar el conflicte amb hiddenimports
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 3. GESTOR D'ATURADA
a_stop = Analysis(
    ['MTUOC-stop-server.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['requests', 'pyyaml'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 4. DESCARREGADOR
a_download = Analysis(
    ['MTUOC-downloader.py'],
    pathex=[],
    binaries=[],
    datas=download_datas,  
    hiddenimports=['requests', 'pyyaml', 'huggingface_hub', 'hf_xet', 'fsspec', 'tqdm', 'filelock'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 5. SERVIDOR DE PROVES ESTÀNDARD
a_test = Analysis(
    ['MTUOC-test-server.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['requests', 'pyyaml', 'flask', 'PyQt6'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 6. SERVIDOR DE PROVES PER A VLLM
a_test_vllm = Analysis(
    ['MTUOC-test-VLLM-server.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['openai', 'pyyaml', 'PyQt6'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# MERGE DE DEPENDÈNCIES FUSIONADES (Unificació dels 6 processos)
MERGE(
    (a_manager, 'MTUOC-server-manager', 'MTUOC-server-manager'),
    (a_server, 'MTUOC-server', 'MTUOC-server'),
    (a_stop, 'MTUOC-stop-server', 'MTUOC-stop-server'),
    (a_download, 'MTUOC-downloader', 'MTUOC-downloader'),
    (a_test, 'MTUOC-test-server', 'MTUOC-test-server'),
    (a_test_vllm, 'MTUOC-test-VLLM-server', 'MTUOC-test-VLLM-server')
)

pyz_manager = PYZ(a_manager.pure, a_manager.zipped_data, cipher=block_cipher)
pyz_server = PYZ(a_server.pure, a_server.zipped_data, cipher=block_cipher)
pyz_stop = PYZ(a_stop.pure, a_stop.zipped_data, cipher=block_cipher)
pyz_download = PYZ(a_download.pure, a_download.zipped_data, cipher=block_cipher)
pyz_test = PYZ(a_test.pure, a_test.zipped_data, cipher=block_cipher)
pyz_test_vllm = PYZ(a_test_vllm.pure, a_test_vllm.zipped_data, cipher=block_cipher)

# EMBAQUETAT DE CADA EXECUTABLE DINS DE LA CARPETA COMUNA
exe_manager = EXE(
    pyz_manager, a_manager.scripts, [], exclude_binaries=True,
    name='MTUOC-server-manager', debug=False, bootloader_ignore_signals=False,
    strip=False, upx=True, console=False, disable_windowed_traceback=False,
    argv_emulation=False, target_arch=None, codesign_identity=None, entitlements_file=None,
)

exe_server = EXE(
    pyz_server, a_server.scripts, [], exclude_binaries=True,
    name='MTUOC-server', debug=False, bootloader_ignore_signals=False,
    strip=False, upx=True, console=True, disable_windowed_traceback=False,
    argv_emulation=False, target_arch=None, codesign_identity=None, entitlements_file=None,
)

exe_stop = EXE(
    pyz_stop, a_stop.scripts, [], exclude_binaries=True,
    name='MTUOC-stop-server', debug=False, bootloader_ignore_signals=False,
    strip=False, upx=True, console=True, disable_windowed_traceback=False,
    argv_emulation=False, target_arch=None, codesign_identity=None, entitlements_file=None,
)

exe_download = EXE(
    pyz_download, a_download.scripts, [], exclude_binaries=True,
    name='MTUOC-downloader', debug=False, bootloader_ignore_signals=False,
    strip=False, upx=True, console=True, disable_windowed_traceback=False,
    argv_emulation=False, target_arch=None, codesign_identity=None, entitlements_file=None,
)

exe_test = EXE(
    pyz_test, a_test.scripts, [], exclude_binaries=True,
    name='MTUOC-test-server', debug=False, bootloader_ignore_signals=False,
    strip=False, upx=True, console=True, disable_windowed_traceback=False,
    argv_emulation=False, target_arch=None, codesign_identity=None, entitlements_file=None,
)

exe_test_vllm = EXE(
    pyz_test_vllm, a_test_vllm.scripts, [], exclude_binaries=True,
    name='MTUOC-test-VLLM-server', debug=False, bootloader_ignore_signals=False,
    strip=False, upx=True, console=True, disable_windowed_traceback=False,
    argv_emulation=False, target_arch=None, codesign_identity=None, entitlements_file=None,
)

coll = COLLECT(
    exe_manager, a_manager.binaries, a_manager.zipfiles, a_manager.datas,
    exe_server, a_server.binaries, a_server.zipfiles, a_server.datas,
    exe_stop, a_stop.binaries, a_stop.zipfiles, a_stop.datas,
    exe_download, a_download.binaries, a_download.zipfiles, a_download.datas,
    exe_test, a_test.binaries, a_test.zipfiles, a_test.datas,
    exe_test_vllm, a_test_vllm.binaries, a_test_vllm.zipfiles, a_test_vllm.datas,
    strip=False, upx=True, upx_exclude=[],
    name='MTUOC-suite',
)
