#    MTUOC_typeMTUOC v 2402
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


import sys
from flask import Flask, jsonify, request, make_response

from MTUOC_misc import get_IP_info
from MTUOC_misc import printLOG
import config

from MTUOC_translate import translate_para

def start_MTUOC_server():
    cli = sys.modules['flask.cli']
    cli.show_server_banner = lambda *x: None
    STATUS_OK = "ok"
    STATUS_ERROR = "error"
    printLOG(1,config.verbosity_level,"MTUOC server started using MTUOC protocol")
    STATUS_ERROR = "error"
    out={}
    def start(url_root="./translator",
              host="0.0.0.0",
              port=5000,
              debug=True):
        def prefix_route(route_function, prefix='', mask='{0}{1}'):
            def newroute(route, *args, **kwargs):
                return route_function(mask.format(prefix, route), *args, **kwargs)
            return newroute

        app = Flask(__name__)
        app.route = prefix_route(app.route, url_root)

        @app.route('/translate', methods=['POST'])
        def translateMTUOC():
            try:
                body = request.get_json()
                printLOG(3,"translateMTUOC body:", body,timestamp=False)
                ts=translate_para(body["src"])
                printLOG(3,"translateMTUOC ts:", ts,timestamp=False)
                jsonObject = {
                    "id": body["id"],
                    "src": body["src"],
                    "system_name": ts["system_name"],
                    "tgt": ts["tgt"], 
                    "src_tokens": ts["src_tokens"],
                    "tgt_tokens": ts["tgt_tokens"],
                    "src_subwords": ts["src_subwords"],
                    "tgt_subwords": ts["tgt_subwords"],
                    "alignment": ts["alignment"],
                    "alternate_translations": ts["alternate_translations"]
                   
                }
                try:
                    jsonobjecttoreturn=jsonify(jsonObject)
                except:
                    printLOG(3,"ERROR json:", sys.exc_info(),timestamp=False)
                printLOG(3,"translateMTUOC jsonobject:", jsonobjecttoreturn,timestamp=False)
                return jsonobjecttoreturn
            except:
                return make_response("Server Error", 500)
        
        from waitress import serve
        serve(app, host=host, port=port,threads= 1)    
        #app.run(debug=debug, host=host, port=port, use_reloader=False,threaded=True)
    url_root="/"
    ip="0.0.0.0"
    ip=get_IP_info()
    debug="store_true"
    
    printLOG(1,"MTUOC server IP:", ip,timestamp=False)
    printLOG(1,"MTUOC server port:", config.MTUOCServer_port,timestamp=False)
    printLOG(1,"MTUOC server type:", "MTUOC",timestamp=False)
    
    start(url_root=url_root, host=ip, port=config.MTUOCServer_port,debug=debug)
