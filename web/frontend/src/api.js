// Cliente de la API Flask (web/app.py)

async function pedir(ruta, opciones = {}) {
  const r = await fetch(`/api${ruta}`, {
    headers: { "Content-Type": "application/json" },
    ...opciones,
  });
  const datos = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(datos.error || `Error ${r.status}`);
  return datos;
}

export const api = {
  salud: () => pedir("/salud"),
  iniciarAnalisis: (url) => pedir("/analisis", { method: "POST", body: JSON.stringify({ url }) }),
  estadoAnalisis: (conv) => pedir(`/analisis/${conv}`),
  informes: (sitio = "") => pedir(`/informes?limite=100${sitio ? `&sitio=${encodeURIComponent(sitio)}` : ""}`),
  informe: (id) => pedir(`/informes/${id}`),
  estadisticas: () => pedir("/estadisticas"),
  urlJsonld: (id) => `/api/informes/${id}/jsonld`,
};

// Utilidades de presentación compartidas
export const claseNivel = (nivel) =>
  ({ Urgente: "nivel-urgente", Preventivo: "nivel-preventivo", "Al día": "nivel-aldia" })[nivel] || "";

export const clasePrioridad = (p) => ({ Alta: "p-alta", Media: "p-media", Baja: "p-baja" })[p] || "";

export const fechaLegible = (iso) =>
  new Date(iso).toLocaleString("es-CO", { dateStyle: "medium", timeStyle: "short" });

export const dominio = (url) => {
  try { return new URL(url).hostname.replace(/^www\./, ""); } catch { return url; }
};
