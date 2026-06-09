#    MTUOC_stop_server v. 24.02
#    Copyright (C) 2024  Antoni Oliver
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.


import sys
import os
import platform
import yaml

# --- FIX COMPATIBILITAT DE CONSOLA PER A WINDOWS LEGACY (TEXT PUR) ---
if sys.platform.startswith('win'):
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1, errors='replace')
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1, errors='replace')
# --------------------------------------------------------------------

def kill_port_process(port):
    """Kills any process occupying the specified port on Windows, Linux, and macOS."""
    try:
        system_platform = platform.system()
        
        if system_platform == "Windows":
            # Native Windows CMD command to find the PID holding the port and taskkill it forcefully (/F)
            command = f'for /f "tokens=5" %a in (\'netstat -aon ^| findstr :{port}\') do taskkill /f /pid %a'
            os.system(command)
            
        elif system_platform == "Darwin":
            # Comanda nativa per a macOS (Darwin) que utilitza lsof i kill sense requerir fuser
            command = f"kill -9 $(lsof -t -i:{port}) 2>/dev/null"
            os.system(command)
            
        else:
            # Native Linux/Unix command to release the socket allocation
            command = f"fuser -k {port}/tcp"
            os.system(command)
            
        print(f"[OK] Port {port} successfully cleared.")
    except Exception as e:
        print(f"[ERROR] Anomalous behavior detected while clearing port {port}: {e}")

# Determine configuration filename from command-line argument or default baseline
configfile = sys.argv[1] if len(sys.argv) > 1 else "config-server.yaml"

if not os.path.exists(configfile):
    print(f"[ERROR] Target initialization blueprint '{configfile}' does not exist.")
    sys.exit(1)

# 1. Load Server Configuration Schema
try:
    with open(configfile, 'r', encoding="utf-8") as stream:
        config = yaml.load(stream, Loader=yaml.FullLoader)
    
    main_port = config["MTUOCServer"]["port"]
    engine_name = config["MTengine"]
    model_config_path = config.get("model_config", None)
except Exception as e:
    print(f"[ERROR] Parsing main server configuration structural mapping: {e}")
    sys.exit(1)

# Terminate Primary MTUOC Framework Server Engine
print(f"[INFO] Decommissioning primary framework gateway on port {main_port}...")
kill_port_process(main_port)

# 2. Dynamic Evaluation for Secondary Engines (Marian, Eole, etc.)
# If the main configuration or the selected engine points to a nested configuration, scan it
if model_config_path and os.path.exists(model_config_path):
    try:
        with open(model_config_path, 'r', encoding="utf-8") as sub_stream:
            sub_config = yaml.load(sub_stream, Loader=yaml.FullLoader)
            
        secondary_port = None
        
        # Extract engine specific port parameter maps based on architecture type
        if engine_name == "Marian" and "Marian" in sub_config:
            secondary_port = sub_config["Marian"].get("port", None)
        elif engine_name == "Eole" and "Eole" in sub_config:
            secondary_port = sub_config["Eole"].get("EolePort", None)
            
        if secondary_port:
            print(f"[INFO] Nested engine deployment detected ({engine_name}). Decommissioning sub-node on port {secondary_port}...")
            kill_port_process(secondary_port)
            
    except Exception as e_sub:
        print(f"[WARNING] Failed to evaluate nested layout mapping constraints at '{model_config_path}': {e_sub}")
else:
    # Legacy hardcoded fallback arrays for standard configuration templates if path resolving was skipped
    try:
        if engine_name == "Marian" and os.path.exists("config-Marian.yaml"):
            with open("config-Marian.yaml", 'r', encoding="utf-8") as m_stream:
                m_cfg = yaml.load(m_stream, Loader=yaml.FullLoader)
                kill_port_process(m_cfg["Marian"]["port"])
        elif engine_name == "Eole" and os.path.exists("config-Eole.yaml"):
            with open("config-Eole.yaml", 'r', encoding="utf-8") as e_stream:
                e_cfg = yaml.load(e_stream, Loader=yaml.FullLoader)
                kill_port_process(e_cfg["Eole"]["EolePort"])
    except Exception as e_legacy:
        print(f"[ERROR] Legacy infrastructure parsing failure: {e_legacy}")

print("[INFO] MTUOC Infrastructure stack successfully stopped.")
