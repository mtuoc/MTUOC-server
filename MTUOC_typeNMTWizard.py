#    MTUOC_typeNMTWizard v. 202410
#    Copyright (C) 2024  Antoni Oliver
#    v. 07/06/2023
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
from flask import Flask, jsonify, request

from MTUOC_misc import get_IP_info
from MTUOC_misc import printLOG
import config

from MTUOC_translate import translate_para

def start_NMTWizard_server():
    cli = sys.modules['flask.cli']
    cli.show_server_banner = lambda *x: None
    STATUS_OK = "ok"
    STATUS_ERROR = "error"
    printLOG(1,"MTUOC server started as NMTWizard server")
    out={}
    def start(url_root="",
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
        def translateONMT():
            inputs = request.get_json(force=True)
            sourcetext=inputs["src"][0]["text"]
            try:
                targettext=translate_para(sourcetext)
                out={"tgt": [[{"text": targettext['tgt']}]]}
            except:
                out['error'] = "Error"
                out['status'] = STATUS_ERROR
            return jsonify(out)
        from waitress import serve
        serve(app, host=host, port=port,threads= 1)    
        #app.run(debug=debug, host=host, port=port, use_reloader=False,threaded=True)
    url_root="/"
    ip="0.0.0.0"
    ip=get_IP_info()
    debug="store_true"
    
    printLOG(1,"MTUOC server IP:   ", ip, timestamp=False)
    printLOG(1,"MTUOC server port: ", config.MTUOCServer_port, timestamp=False)
    printLOG(1,"MTUOC server type:", "NMTWizard",timestamp=False)
    
    start(url_root=url_root, host=ip, port=config.MTUOCServer_port,debug=debug)
