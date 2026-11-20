import os
import re
from collections import Counter

from flask import Flask, request, Response
from markupsafe import escape

app = Flask(__name__)

# [1] Validacion de entrada: solo letras, numeros, espacios y guion, maximo 50 caracteres
NOMBRE_VALIDO = re.compile(r"^[\w\s\-]{1,50}$", re.UNICODE)

# Contador de peticiones para monitoreo (Prometheus/Grafana)
CONTADOR = Counter()


@app.route('/hello')
def hello():
    name = request.args.get('name', 'invitado')
    if not NOMBRE_VALIDO.match(name):
        return Response("Parametro 'name' invalido", status=400, mimetype='text/plain')
    # [2] Codificacion de salida: escape() convierte < > " ' & en texto inofensivo
    return f"Hello, {escape(name)}!"


@app.route('/metrics')
def metrics():
    lineas = [
        '# HELP app_http_requests_total Total de peticiones HTTP por ruta y codigo',
        '# TYPE app_http_requests_total counter',
    ]
    for (ruta, codigo), total in sorted(CONTADOR.items()):
        lineas.append(f'app_http_requests_total{{path="{ruta}",status="{codigo}"}} {total}')
    return Response("\n".join(lineas) + "\n", mimetype='text/plain; version=0.0.4')


@app.after_request
def cabeceras_seguridad(resp):
    if request.path != '/metrics':
        ruta = request.path if request.path == '/hello' else 'otra'
        CONTADOR[(ruta, resp.status_code)] += 1
    # [3] Cabeceras de seguridad (las que reporto OWASP ZAP)
    resp.headers['Content-Security-Policy'] = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
    resp.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    resp.headers['X-Frame-Options'] = 'DENY'
    resp.headers['Referrer-Policy'] = 'no-referrer'
    resp.headers['Cache-Control'] = 'no-store'
    resp.headers['Permissions-Policy'] = 'geolocation=(), camera=(), microphone=()'
    resp.headers['Cross-Origin-Resource-Policy'] = 'same-origin'
    resp.headers['Server'] = 'app'
    return resp


if __name__ == '__main__':
    # [4] debug desactivado por defecto: el depurador de Werkzeug permite ejecutar codigo remoto
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    # 0.0.0.0 es necesario dentro del contenedor; el acceso se controla con los puertos de Docker
    host = os.environ.get('APP_HOST', '0.0.0.0')  # nosec B104
    app.run(host=host, port=5000, debug=debug)