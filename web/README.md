# Fase 5: Interfaz de guía, React + Flask (20%)

Dashboard pensado para **una persona que no sabe de programación**: escribe la dirección de su
sitio, ve en vivo cómo trabajan los agentes y recibe un veredicto claro con qué hacer y por qué.

```
Navegador (React)  ──/api──►  Flask (web/app.py)  ──ACL──►  Agentes SPADE (hilo de fondo)
                                     │                              │
                                     └────────── MongoDB (JSON-LD) ◄┘
```

## Pantallas

| Pantalla | Qué muestra |
|---|---|
| **Analizar** (`/`) | Campo para la URL, ejemplos y explicación de las 3 áreas (SEO, Accesibilidad, Rendimiento) |
| **Análisis en curso** (`/analisis/:id`) | Los 3 agentes se encienden a medida que trabajan, con la conversación FIPA-ACL **real** en tiempo real |
| **Informe** (`/informe/:id`) | Veredicto con velocímetro (lógica difusa), estado y mensaje (ontología), recomendaciones con «¿Por qué importa?» y «¿Cómo lo soluciono?», métricas medidas, el razonamiento (pertenencias difusas y reglas activadas), los mensajes ACL y el JSON-LD guardado |
| **Historial** (`/historial`) | Estadísticas por nivel y lista buscable de todos los informes de MongoDB |
| **¿Cómo funciona?** | Explicación paso a paso y glosario en lenguaje sencillo |

### Decisiones de diseño (criterio: ¿la guía es clara para un no programador?)

- **Lenguaje sencillo**: «Imágenes sin descripción» en lugar de «img sin alt», y «Descripción para
  Google» en lugar de «meta description». Cada recomendación explica por qué importa y cómo arreglarlo.
- **La explicación semántica sale de la ontología**: los textos de «¿Por qué importa?», los pasos
  de solución y el significado de cada estado se consultan con SPARQL en `mantenimiento_web.owl`.
- **Bien o mal lo decide la ontología**: una métrica aparece en rojo solo si generó una recomendación.
- **Transparencia**: si el Experto subió el nivel por problemas graves (ajuste semántico), un recuadro
  explica por qué el veredicto no es el de la lógica difusa.
- **Colores de semáforo**: verde (Al día), ámbar (Preventivo) y rojo (Urgente). Modo claro y oscuro
  según el sistema operativo, y diseño adaptable a celular.

## API (Flask)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/salud` | Estado de los agentes y de MongoDB, tripletas de la ontología, creencias BDI |
| POST | `/api/analisis` `{url}` | Inicia un análisis (202) y devuelve el id de conversación ACL |
| GET | `/api/analisis/<id>` | Avance: estado y mensajes ACL hasta el momento |
| GET | `/api/informes?sitio=` | Lista de informes |
| GET | `/api/informes/<id>` | Informe completo (métricas, diagnóstico, mensajes, JSON-LD) |
| GET | `/api/informes/<id>/jsonld` | Descarga el documento como `application/ld+json` |
| GET | `/api/estadisticas` | Cantidad de informes por nivel |

## Ejecutar

```bash
# desde la raíz del repo, con el entorno virtual activado
python -m web.app
```

Abrir **http://127.0.0.1:5000**. La interfaz ya compilada (`web/frontend/dist`) está en el repositorio,
así que para usarla no hace falta Node.js.

### Modificar la interfaz (requiere Node.js 20 o superior)

```bash
cd web/frontend
npm install
npm run dev      # http://localhost:5173 con recarga automática (necesita python -m web.app corriendo)
npm run build    # regenera web/frontend/dist: hacerlo antes de cada commit
```

Código en `web/frontend/src/`: `paginas/` (una por pantalla), `componentes/` (Nav, Medidor,
Conversacion, JsonLd), `api.js` (cliente de la API) y `estilos.css`.

## Notas técnicas

- Los agentes corren en un hilo de fondo con su propio loop asyncio (`web/runtime.py`). El servidor
  XMPP embebido intenta registrar un manejador de Ctrl+C, y Python solo lo permite en el hilo
  principal, así que esa llamada se ignora fuera de él.
- El servidor XMPP usa el puerto **5222**. Cierre el dashboard antes de correr las pruebas, porque la
  prueba de extremo a extremo también levanta uno.
- Al cerrar con Ctrl+C aparece un `KeyboardInterrupt` de un subproceso de pyjabber. Es normal.
- Si MongoDB no está corriendo, el dashboard funciona igual, pero guarda los informes en memoria
  (lo indica la pastilla «Memoria» arriba a la derecha).
