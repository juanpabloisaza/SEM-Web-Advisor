import { Link } from "react-router-dom";
import { ArrowRight, BookOpen, Brain, Database, Network, ScanSearch, SlidersHorizontal } from "lucide-react";

const PASOS = [
  { icono: ScanSearch, titulo: "1. El Agente Analista visita su página",
    texto: "Descarga la página una sola vez (respetando si el sitio no permite robots) y mide cuánto tarda, si las imágenes tienen descripción, si hay errores en el código, si tiene título, etc." },
  { icono: SlidersHorizontal, titulo: "2. La lógica difusa interpreta los números",
    texto: "En lugar de cortes rígidos («más de 3 segundos es lento»), entiende que 2,9 s es «casi lento». Combina velocidad y errores con reglas como: «si es lento Y tiene muchos errores, el mantenimiento es urgente»." },
  { icono: Network, titulo: "3. La ontología aporta el conocimiento",
    texto: "Es una base de conocimiento sobre buenas prácticas web (SEO, accesibilidad, rendimiento). El Agente Experto la consulta para saber qué problema tiene su sitio, por qué importa y cómo se soluciona." },
  { icono: Database, titulo: "4. El Agente Notificador guarda el informe",
    texto: "Lo guarda en MongoDB en formato JSON-LD (datos enlazados), para que otros sistemas también puedan entenderlo." },
];

const GLOSARIO = [
  ["SEO", "Optimización para buscadores: lo que hace que Google encuentre y muestre bien su sitio."],
  ["Accesibilidad", "Que todas las personas puedan usar el sitio, incluidas las que usan lectores de pantalla."],
  ["Texto alternativo (alt)", "Descripción de una imagen que leen en voz alta los lectores de pantalla."],
  ["Meta descripción", "Resumen corto de la página que Google muestra debajo del título en los resultados."],
  ["Agente inteligente", "Programa autónomo que percibe su entorno, razona y actúa para cumplir un objetivo."],
  ["FIPA-ACL", "Lenguaje estándar con el que los agentes se envían mensajes (solicitar, aceptar, informar…)."],
  ["Ontología", "Modelo formal de un tema: sus conceptos y cómo se relacionan, escrito en OWL."],
  ["JSON-LD", "Formato de datos enlazados: un JSON que además explica el significado de cada campo."],
];

export default function ComoFunciona() {
  return (
    <>
      <section className="hero" style={{ paddingBottom: 20 }}>
        <span className="etiqueta-hero"><Brain size={15} /> Así piensa SEM-Web-Advisor</span>
        <h1>Tres agentes que trabajan en <span>equipo</span></h1>
        <p className="sub">Cada uno tiene una tarea y se comunican entre sí con mensajes, como un equipo de personas.</p>
      </section>

      <section className="tarjeta pasos">
        {PASOS.map(({ icono: Icono, titulo, texto }) => (
          <div className="paso" key={titulo}>
            <div className="icono-titulo"><Icono size={26} /></div>
            <div><h3>{titulo}</h3><p>{texto}</p></div>
          </div>
        ))}
      </section>

      <section className="seccion tarjeta">
        <h2 className="titulo-seccion"><span className="icono-titulo"><BookOpen size={20} /></span> Glosario</h2>
        <dl className="glosario">
          {GLOSARIO.map(([t, d]) => <div key={t}><dt>{t}</dt><dd>{d}</dd></div>)}
        </dl>
      </section>

      <div style={{ textAlign: "center", margin: "36px 0" }}>
        <Link className="btn" to="/">Analizar mi sitio <ArrowRight size={18} /></Link>
      </div>
    </>
  );
}
