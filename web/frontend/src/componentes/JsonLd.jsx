// Visor con resaltado simple del documento JSON-LD guardado en MongoDB.
function resaltar(json) {
  const escapado = json.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  return escapado.replace(
    /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)/g,
    (m) => {
      let c = "n";
      if (/^"/.test(m)) c = /:$/.test(m) ? "k" : "s";
      return `<span class="${c}">${m}</span>`;
    },
  );
}

export default function JsonLd({ documento }) {
  // El detalle técnico es largo: se muestra resumido para que se aprecie la estructura semántica.
  const vista = { ...documento, detail: "{ … métricas, diagnóstico y mensajes ACL (literal rdf:JSON) … }" };
  return (
    <pre className="codigo" dangerouslySetInnerHTML={{ __html: resaltar(JSON.stringify(vista, null, 2)) }} />
  );
}
