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
import yaml
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


configfile="config-server.yaml"
stream = open(configfile, 'r',encoding="utf-8")
config=yaml.load(stream, Loader=yaml.FullLoader)

MTUOCServer_port=config["MTUOCServer"]["port"]
MTEngine=config["MTEngine"]["MTengine"]

try:
    stopcommand2="fuser -k "+str(MTUOCServer_port)+"/tcp"
    print(stopcommand2)
    os.system(stopcommand2)
    print("MT Engine stopped.")
except:
    print("Unable to stop MT Engine",sys.exc_info())


if MTEngine=="Marian":
    startMarianServer=config["Marian"]["startMarianServer"]
    MarianIP=config["Marian"]["IP"]
    MarianPort=config["Marian"]["port"]
    if startMarianServer and MarianIP in ["localhost","127.0.0.1"]:
        try:
            stopcommand2="fuser -k "+str(MarianPort)+"/tcp"
            print(stopcommand2)
            os.system(stopcommand2)
            print("Marian server stopped.")
        except:
            print("Unable to stop Marian server.",sys.exc_info())
