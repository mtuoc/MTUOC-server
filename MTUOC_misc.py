#    MTUOC_misc v 2402
#    Description: an MTUOC server using Sentence Piece as preprocessing step
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


import socket
from datetime import datetime
import sys

import config

def printLOG(vlevel,m1,m2="",timestamp=True):
    if timestamp:
        cadena=str(datetime.now())+"\t"+str(m1)+"\t"+str(m2)
    else:
        cadena=str(m1)+"\t"+str(m2)
    if vlevel<=config.verbosity_level:
        print(cadena)
        if config.log_file:
            config.sortidalog.write(cadena+"\n") 

def get_IP_info(): 
    try: 
        host_name = socket.gethostname() 
        host_ip = socket.gethostbyname(host_name) 
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
        return(IP)
    except: 
        IP = '127.0.0.1'
        return(IP)
    finally:
        s.close()
