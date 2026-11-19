import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Accessibility, AlertCircle, ArrowRight, Gauge, Globe, Loader2, SearchCheck, Sparkles } from "lucide-react";
import { api } from "../api.js";

const EJEMPLOS = ["example.com", "wikipedia.org", "politecnicojic.edu.co"];

const PILARES = [
  { icono: SearchCheck, titulo: "SEO", texto: "¿Google entiende de qué trata su página? Revisamos título, descripción y encabezados." },
  { icono: Accessibility, titulo: "Accesibilidad", texto: "¿Pueden usarla personas con discapacidad visual? Revisamos imágenes, enlaces e idioma." },
  { icono: Gauge, titulo: "Rendimiento", texto: "¿Carga rápido? Medimos cuánto tarda en responder y qué tan pesada es." },
];

export default function Inicio() {
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);
  const navegar = useNavigate();

  async function analizar(destino = url) {
    if (!destino.trim()) {
      setError("Escriba la dirección de su sitio web, por ejemplo: www.misitio.com");
      return;
    }
    setError("");
    setEnviando(true);
    try {
      const { conversacion } = await api.iniciarAnalisis(destino);
      navegar(`/analisis/${conversacion}`, { state: { url: destino } });
    } catch (e) {
      setError(e.message);
      setEnviando(false);
    }
  }

  return (
    <>
      <section className="hero">
        <span className="etiqueta-hero"><Sparkles size={15} /> Lógica difusa · Ontologías · Agentes inteligentes</span>
        <h1>¿Su sitio web necesita <span>mantenimiento</span>?</h1>
        <p className="sub">
          Escriba la dirección de su página y nuestros agentes inteligentes la revisarán en segundos.
          Le diremos qué tan urgente es y qué hacer, en palabras sencillas.
        </p>

        <form className="buscador" onSubmit={(e) => { e.preventDefault(); analizar(); }}>
          <label className="campo">
            <Globe size={20} />
            <input
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="www.misitio.com"
              aria-label="Dirección del sitio web"
              autoFocus
              disabled={enviando}
            />
          </label>
          <button className="btn" disabled={enviando}>
            {enviando ? <Loader2 size={18} className="girar" /> : <ArrowRight size={18} />}
            {enviando ? "Enviando…" : "Analizar"}
          </button>
        </form>

        <div className="ejemplos">
          Pruebe con:
          {EJEMPLOS.map((e) => (
            <button key={e} className="chip-btn" type="button" disabled={enviando}
                    onClick={() => { setUrl(e); analizar(e); }}>{e}</button>
          ))}
        </div>

        {error && <div className="error-caja"><AlertCircle size={20} /> {error}</div>}
      </section>

      <section className="seccion rejilla-3">
        {PILARES.map(({ icono: Icono, titulo, texto }) => (
          <article key={titulo} className="tarjeta pilar">
            <div className="icono-titulo"><Icono size={22} /></div>
            <h3>{titulo}</h3>
            <p>{texto}</p>
          </article>
        ))}
      </section>
    </>
  );
}
