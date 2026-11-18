"""
Percepción del Agente Analista: descarga una URL y mide las métricas que la
ontología sabe interpretar (ver la propiedad mw:metrica de cada mw:Problema).

Se mantiene separado del agente para poder probarlo sin SPADE.

Ética y privacidad:
  - Respeta robots.txt: si el sitio no permite robots en esa ruta, no se analiza.
  - Solo lee la página pública solicitada (una petición, sin seguir enlaces).
  - No guarda el HTML ni datos personales: solo números agregados.
"""
import time
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import html5lib
import requests
from bs4 import BeautifulSoup

from agentes.config import TIEMPO_ESPERA_HTTP, USER_AGENT


class AnalisisNoPermitido(Exception):
    """El sitio prohíbe el acceso a robots en esa ruta (robots.txt)."""


def normalizar_url(url: str) -> str:
    url = url.strip()
    if not urlparse(url).scheme:
        url = "https://" + url
    partes = urlparse(url)
    if partes.scheme not in ("http", "https") or not partes.netloc:
        raise ValueError(f"URL no válida: {url!r}")
    return url


def permitido_por_robots(url: str) -> bool:
    robots_url = urljoin(url, "/robots.txt")
    try:
        r = requests.get(robots_url, timeout=5, headers={"User-Agent": USER_AGENT})
    except requests.RequestException:
        return True  # sin robots.txt accesible se asume permitido
    if r.status_code >= 400:
        return True
    rp = RobotFileParser()
    rp.parse(r.text.splitlines())
    return rp.can_fetch(USER_AGENT, url)


# Avisos de html5lib que no son errores de sintaxis del autor:
# 'invalid-codepoint' salta con caracteres Unicode válidos (emojis, otros alfabetos).
_ERRORES_IGNORADOS = {"invalid-codepoint"}


def contar_errores_sintaxis(html: str) -> int:
    """
    Errores de análisis según el estándar HTML5 (etiquetas mal cerradas, atributos
    duplicados, entidades inválidas...). Cada error se cuenta una vez por posición.
    """
    parser = html5lib.HTMLParser(strict=False)
    parser.parse(html)
    unicos = {(pos, codigo) for pos, codigo, _ in parser.errors if codigo not in _ERRORES_IGNORADOS}
    return len(unicos)


def _enlace_sin_texto(a) -> bool:
    if a.get_text(strip=True):
        return False
    if a.get("aria-label") or a.get("title"):
        return False
    return not any(img.get("alt") for img in a.find_all("img"))


def medir_html(html: str) -> dict:
    """Métricas estáticas del documento (no requieren red)."""
    soup = BeautifulSoup(html, "html.parser")
    imagenes = soup.find_all("img")
    enlaces = soup.find_all("a", href=True)
    titulo = soup.title.get_text(strip=True) if soup.title else ""
    meta = soup.find("meta", attrs={"name": lambda v: v and v.lower() == "description"})
    html_tag = soup.find("html")
    n_h1 = len(soup.find_all("h1"))
    return {
        "errores_sintaxis": contar_errores_sintaxis(html),
        "imagenes_sin_alt": sum(1 for i in imagenes if i.get("alt") is None),
        "total_imagenes": len(imagenes),
        "enlaces_sin_texto": sum(1 for a in enlaces if _enlace_sin_texto(a)),
        "total_enlaces": len(enlaces),
        "sin_titulo": int(not titulo),
        "sin_meta_descripcion": int(not (meta and meta.get("content", "").strip())),
        "sin_idioma": int(not (html_tag and html_tag.get("lang", "").strip())),
        "h1_incorrecto": int(n_h1 != 1),
        "total_h1": n_h1,
    }


def analizar_url(url: str) -> dict:
    """
    Descarga la página y devuelve sus métricas.
    Lanza AnalisisNoPermitido, ValueError o requests.RequestException si no se puede.
    """
    url = normalizar_url(url)
    if not permitido_por_robots(url):
        raise AnalisisNoPermitido(f"robots.txt de {urlparse(url).netloc} no permite analizar {url}")

    inicio = time.perf_counter()
    r = requests.get(url, timeout=TIEMPO_ESPERA_HTTP, headers={"User-Agent": USER_AGENT})
    tiempo = time.perf_counter() - inicio  # tiempo hasta recibir la página completa

    metricas = {
        "url": url,
        "url_final": r.url,
        "codigo_http": r.status_code,
        "tiempo_carga": round(tiempo, 2),
        "peso_html_kb": round(len(r.content) / 1024, 1),
    }
    metricas.update(medir_html(r.text))
    return metricas


if __name__ == "__main__":
    import json
    import sys

    print(json.dumps(analizar_url(sys.argv[1] if len(sys.argv) > 1 else "https://example.com"),
                     indent=2, ensure_ascii=False))
