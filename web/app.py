"""
Fase 5: backend Flask del Dashboard.

- Arranca los agentes SPADE en segundo plano (web/runtime.py).
- Expone una API JSON que usa la interfaz React (web/frontend).
- Sirve la interfaz ya compilada (web/frontend/dist) en http://127.0.0.1:5000

Uso (desde la raíz del repo):
    python -m web.app
"""
import json
import logging
import os
from pathlib import Path

from flask import Flask, Response, abort, jsonify, request, send_from_directory

from agentes.analizador import normalizar_url
from ontologia.consultas import cargar_grafo
from persistencia.jsonld import a_grafo
from persistencia.repositorio import RepositorioInformes, RepositorioMemoria, disponible
from web.runtime import RuntimeAgentes

DIST = Path(__file__).resolve().parent / "frontend" / "dist"


def _resumen(doc: dict) -> dict:
    d = doc["detail"]["diagnostico"]
    return {
        "id": doc["_id"],
        "sitio": doc["site"]["@id"],
        "fecha": doc["dateCreated"],
        "nivel": d["nivel"],
        "nivel_difuso": d.get("nivel_difuso"),
        "estado": d["estado"],
        "puntaje": d["puntaje"],
        "prioridad": doc["result"]["priority"],
        "areas": doc["result"]["tags"],
        "recomendaciones": len(d["recomendaciones"]),
    }


def _vista(doc: dict) -> dict:
    jsonld = {k: v for k, v in doc.items() if k != "_id"}
    detalle = doc["detail"]
    return {
        **_resumen(doc),
        "metricas": detalle["metricas"],
        "diagnostico": detalle["diagnostico"],
        "mensajes": detalle.get("mensajes_acl", []),
        "tripletas": len(a_grafo(doc)),
        "jsonld": jsonld,
    }


def crear_app(repositorio=None, iniciar_agentes: bool = True) -> Flask:
    app = Flask(__name__, static_folder=None)
    app.json.ensure_ascii = False
    app.json.sort_keys = False

    if repositorio is None:
        repositorio = RepositorioInformes() if disponible() else RepositorioMemoria()
    repositorio.crear_indices()
    runtime = RuntimeAgentes(repositorio)
    if iniciar_agentes:
        runtime.iniciar()
    app.config.update(REPO=repositorio, RUNTIME=runtime)

    # ------------------------------------------------------------------ API
    @app.get("/api/salud")
    def salud():
        return jsonify({
            "almacenamiento": repositorio.col.full_name,
            "mongodb": not isinstance(repositorio, RepositorioMemoria),
            "agentes_activos": runtime.sistema is not None,
            "tripletas_ontologia": len(cargar_grafo()),
            "informes": repositorio.contar(),
            "creencias": runtime.creencias(),
        })

    @app.post("/api/analisis")
    def iniciar_analisis():
        datos = request.get_json(silent=True) or {}
        try:
            url = normalizar_url(datos.get("url", ""))
        except ValueError:
            return jsonify({"error": "Escriba una dirección web válida, por ejemplo: www.misitio.com"}), 400
        return jsonify({"conversacion": runtime.lanzar(url), "url": url}), 202

    @app.get("/api/analisis/<conv>")
    def estado_analisis(conv):
        estado = runtime.estado(conv)
        if estado is None:
            abort(404)
        return jsonify(estado)

    @app.get("/api/informes")
    def listar_informes():
        limite = min(int(request.args.get("limite", 30)), 200)
        docs = repositorio.listar(limite, request.args.get("sitio") or None)
        return jsonify([_resumen(d) for d in docs])

    @app.get("/api/informes/<id_informe>")
    def ver_informe(id_informe):
        doc = repositorio.obtener(id_informe)
        if doc is None:
            abort(404)
        return jsonify(_vista(doc))

    @app.get("/api/informes/<id_informe>/jsonld")
    def descargar_jsonld(id_informe):
        doc = repositorio.obtener(id_informe)
        if doc is None:
            abort(404)
        cuerpo = json.dumps({k: v for k, v in doc.items() if k != "_id"}, ensure_ascii=False, indent=2)
        return Response(cuerpo, mimetype="application/ld+json",
                        headers={"Content-Disposition": f'attachment; filename="informe-{id_informe[:8]}.jsonld"'})

    @app.get("/api/estadisticas")
    def estadisticas():
        nombres = {"mw:Urgente": "Urgente", "mw:Preventivo": "Preventivo", "mw:AlDia": "Al día"}
        crudo = repositorio.estadisticas()
        return jsonify({"total": repositorio.contar(),
                        "por_nivel": {v: crudo.get(k, 0) for k, v in nombres.items()}})

    # ------------------------------------------------------- interfaz React
    @app.get("/", defaults={"ruta": ""})
    @app.get("/<path:ruta>")
    def interfaz(ruta):
        if ruta.startswith("api/"):
            abort(404)
        if not (DIST / "index.html").exists():
            return ("La interfaz no está compilada. Ejecute: cd web/frontend && npm install && npm run build",
                    503, {"Content-Type": "text/plain; charset=utf-8"})
        if ruta and (DIST / ruta).is_file():
            return send_from_directory(DIST, ruta)
        return send_from_directory(DIST, "index.html")  # rutas de React (SPA)

    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    app = crear_app()
    puerto = int(os.environ.get("PORT", 5000))
    print(f"\n  SEM-Web-Advisor listo en  http://127.0.0.1:{puerto}\n")
    # use_reloader=False: el recargador arrancaría los agentes dos veces
    app.run(host="127.0.0.1", port=puerto, debug=False, use_reloader=False, threaded=True)
