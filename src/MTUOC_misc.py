import socket
from datetime import datetime
import sys

# Variables de control privades del mòdul
_verbosity_level = 1
_log_file_active = False
_sortidalog_stream = None

def setup_logging(verbosity_level, log_file_active, sortidalog_stream=None):
    """Initializes the engine logging metrics using values from the YAML configuration."""
    global _verbosity_level, _log_file_active, _sortidalog_stream
    _verbosity_level = int(verbosity_level)
    _log_file_active = bool(log_file_active)
    _sortidalog_stream = sortidalog_stream

def printLOG(vlevel, m1, m2="", timestamp=True):
    if timestamp:
        cadena = str(datetime.now()) + "\t" + str(m1) + "\t" + str(m2)
    else:
        cadena = str(m1) + "\t" + str(m2)
        
    # Comprovem utilitzant les variables de control internes configurades
    if vlevel <= _verbosity_level:
        print(cadena)
        if _log_file_active and _sortidalog_stream:
            try:
                _sortidalog_stream.write(cadena + "\n")
                _sortidalog_stream.flush() # Força l'escriptura immediata al fitxer de text
            except Exception as e_write:
                print(f"[ERROR] Failed writing to persistence log file: {e_write}")

def get_IP_info(): 
    try: 
        host_name = socket.gethostname() 
        host_ip = socket.gethostbyname(host_name) 
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
        return IP
    except: 
        IP = '127.0.0.1'
        return IP
    finally:
        try:
            s.close()
        except:
            pass
