#    MTUOC_typeMTUOC v 2605 (Pure Dependency Injection - 2026)
import sys
from flask import Flask, jsonify, request, make_response
from MTUOC_misc import get_IP_info
from MTUOC_translate import translate_para

def start_MTUOC_server(server_context):
    cli = sys.modules['flask.cli']
    cli.show_server_banner = lambda *x: None
    
    print("MTUOC server started using MTUOC protocol")
    
    def start(url_root="/", host="0.0.0.0", port=5000):
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
                
                # REVISIÓ: Passem el text i el context rebut de dalt
                ts = translate_para(body["src"], server_context)
                
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
                
                return jsonify(jsonObject)
            except Exception as e:
                print("ERROR MTUOC_typeMTUOC:", sys.exc_info(), e)
                return make_response("Server Error", 500)
        
        from waitress import serve
        serve(app, host=host, port=port, threads=1)    

    ipLOG = get_IP_info()
    print("MTUOC server IP:", ipLOG)
    print("MTUOC server port:", server_context["port"])
    print("MTUOC server type:", "MTUOC")
    sys.stdout.flush()
    start(url_root="/", host="0.0.0.0", port=server_context["port"])
