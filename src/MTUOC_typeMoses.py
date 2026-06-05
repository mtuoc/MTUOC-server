#    MTUOC_typeMoses v. 20210 (Dependency Injection - Updated 2026)
#    Copyright (C) 2024 Antoni Oliver

import sys
from xmlrpc.server import SimpleXMLRPCServer
from MTUOC_misc import get_IP_info
from MTUOC_translate import translate_para

def start_Moses_server(server_context):
    # Creem el servidor XML-RPC fent servir el port del context
    server = SimpleXMLRPCServer(("", server_context["port"]), logRequests=True)
    
    # Definim la funció "translate" AQUÍ DINS. 
    # Com que està a dins de start_Moses_server, té accés a 'server_context' automàticament.
    def translate(segment):
        # El client només envia el segment, però nosaltres hi injectem el context localment
        translation = translate_para(segment['text'], server_context)
        
        translationdict = {}
        translationdict["text"] = translation['tgt']
        return translationdict

    # Registrem la funció interna que ara només demana el paràmetre 'segment'
    server.register_function(translate)
    server.register_introspection_functions()
    
    # Inicialitzem el servidor
    try:
        ip = get_IP_info()
        print("MTUOC server IP:   ", ip)
        print("MTUOC server port: ", server_context["port"])
        print("MTUOC server type: ", "Moses")
        server.serve_forever()
    except KeyboardInterrupt:
        print('Exiting')
