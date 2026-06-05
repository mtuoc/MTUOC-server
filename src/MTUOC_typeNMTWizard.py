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

from MTUOC_translate import translate_para

# REVISIÓ: Rebem el context que agrupa totes les dependències
def start_NMTWizard_server(server_context):
    cli = sys.modules['flask.cli']
    cli.show_server_banner = lambda *x: None
    STATUS_OK = "ok"
    STATUS_ERROR = "error"
    print("MTUOC server started as NMTWizard server")
    out = {}
    
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
            
            try:
                # 1. Obtenim el primer element de la llista "src"
                primer_element = inputs["src"][0]
                
                # 2. Comprovem si és un diccionari (com el codi original esperava) o un text directe
                if isinstance(primer_element, dict):
                    sourcetext = primer_element["text"]
                else:
                    sourcetext = str(primer_element) # Si és un string, el guardem directament
                
                # 3. Executem la traducció injectant el context
                targettext = translate_para(sourcetext, server_context)
                out = {"tgt": [[{"text": targettext['tgt']}]]}
                
            except Exception as e:
                print(f"Error a NMTWizard routing: {e}")
                out['error'] = f"Error: {str(e)}"
                out['status'] = STATUS_ERROR
                
            return jsonify(out)
            
        from waitress import serve
        serve(app, host=host, port=port, threads=1)    

    url_root = "/"
    ip = get_IP_info()
    debug = "store_true"
    
    print("MTUOC server IP:   ", ip)
    # REVISIÓ: Llegim el port del context enviat per MTUOC-server.py
    print("MTUOC server port: ", server_context["port"])
    print("MTUOC server type:", "NMTWizard")
    
    start(url_root=url_root, host="0.0.0.0", port=server_context["port"], debug=debug)
