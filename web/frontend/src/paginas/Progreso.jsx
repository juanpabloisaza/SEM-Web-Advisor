import { Fragment, useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { AlertTriangle, ArrowLeft, Brain, ChevronRight, Database, ScanSearch } from "lucide-react";
import { api } from "../api.js";
import Conversacion from "../componentes/Conversacion.jsx";

const AGENTES = [
  { id: "analista", nombre: "Analista", tarea: "Lee su página y mide", icono: ScanSearch },
  { id: "experto", nombre: "Experto", tarea: "Razona con lógica difusa y la ontología", icono: Brain },
  { id: "notificador", nombre: "Notificador", tarea: "Arma el informe y lo guarda", icono: Database },
];

// Deduce qué agente está trabajando a partir de los mensajes ACL reales.
function estadoAgentes(mensajes, terminado) {
  const hubo = (de, para, perf = "inform") => mensajes.some((m) => m.de === de && m.para === para && m.performativa === perf);
  const analistaListo = hubo("analista", "experto");
  const expertoListo = hubo("experto", "notificador");
  const notificadorListo = hubo("notificador", "interfaz") || terminado;
  return {
    analista: analistaListo ? "hecho" : "trabajando",
    experto: expertoListo ? "hecho" : analistaListo ? "trabajando" : "",
    notificador: notificadorListo ? "hecho" : expertoListo ? "trabajando" : "",
  };
}

export default function Progreso() {
  const { conv } = useParams();
  const { state } = useLocation();
  const navegar = useNavigate();
  const [estado, setEstado] = useState(null);

  useEffect(() => {
    let vivo = true;
    let temporizador;
    const consultar = async () => {
      try {
        const e = await api.estadoAnalisis(conv);
        if (!vivo) return;
        setEstado(e);
        if (e.estado === "listo") {
          temporizador = setTimeout(() => navegar(`/informe/${e.informe_id}`, { replace: true }), 900);
          return;
        }
        if (e.estado === "error") return;
      } catch {
        if (!vivo) return;
        setEstado({ estado: "error", error: "Se perdió el análisis. Intente de nuevo.", mensajes: [] });
        return;
      }
      temporizador = setTimeout(consultar, 350);
    };
    consultar();
    return () => { vivo = false; clearTimeout(temporizador); };
  }, [conv, navegar]);

  const mensajes = estado?.mensajes || [];
  const fallo = estado?.estado === "error";
  const agentes = estadoAgentes(mensajes, estado?.estado === "listo");

  return (
    <section className="progreso">
      <div style={{ textAlign: "center" }}>
        <span className="etiqueta-hero">Análisis en curso</span>
        <h1 style={{ margin: "16px 0 6px", letterSpacing: "-.02em" }}>
          {fallo ? "No pudimos analizar el sitio" : "Nuestros agentes están revisando su sitio"}
        </h1>
        <p className="desc" style={{ wordBreak: "break-all" }}>{estado?.url || state?.url}</p>
      </div>

      {!fallo && (
        <div className="agentes-fila">
          {AGENTES.map(({ id, nombre, tarea, icono: Icono }, i) => (
            <Fragment key={id}>
              <div className={`agente ${agentes[id]}`}>
                <div className="avatar"><Icono size={28} /></div>
                <h4>Agente {nombre}</h4>
                <p>{agentes[id] === "hecho" ? "¡Listo!" : tarea}</p>
              </div>
              {i < AGENTES.length - 1 && (
                <ChevronRight key={`f${id}`} size={28}
                              className={`flecha ${agentes[AGENTES[i + 1].id] === "trabajando" ? "activa" : ""}`} />
              )}
            </Fragment>
          ))}
        </div>
      )}

      {fallo && (
        <div className="tarjeta" style={{ display: "flex", gap: 14, alignItems: "flex-start", margin: "24px 0" }}>
          <AlertTriangle color="var(--peligro)" style={{ flexShrink: 0 }} />
          <div>
            <b>{estado.error}</b>
            <p className="desc" style={{ margin: "6px 0 14px" }}>
              Algunos sitios no permiten ser revisados por robots (archivo robots.txt) y nuestro sistema
              respeta esa decisión.
            </p>
            <Link className="btn chico" to="/"><ArrowLeft size={16} /> Intentar con otra dirección</Link>
          </div>
        </div>
      )}

      <div className="tarjeta">
        <h3 className="titulo-seccion" style={{ fontSize: "1.05rem" }}>Conversación entre agentes en tiempo real</h3>
        <p className="desc">Los agentes se comunican con mensajes FIPA-ACL. Así se reparten el trabajo:</p>
        <Conversacion mensajes={mensajes} />
      </div>
    </section>
  );
}
