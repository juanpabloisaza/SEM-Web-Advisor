import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  Activity, AlertTriangle, ArrowLeft, BrainCircuit, Calendar, CheckCircle2, ChevronDown, ChevronRight, Clock,
  Code2, Download, FileCode2, FileText, Globe, Heading1, Image, Languages, Link2, ListChecks,
  Loader2, MessagesSquare, RefreshCw, Scale, Weight, XCircle,
} from "lucide-react";
import { api, claseNivel, clasePrioridad, dominio, fechaLegible } from "../api.js";
import Medidor from "../componentes/Medidor.jsx";
import Conversacion from "../componentes/Conversacion.jsx";
import JsonLd from "../componentes/JsonLd.jsx";

// Cómo mostrar cada métrica a una persona que no programa.
// "Bien" o "Mal" lo decide la ontología: una métrica está mal si generó una recomendación.
const METRICAS = [
  { clave: "tiempo_carga", icono: Clock, nombre: "Velocidad de carga", valor: (m) => `${m.tiempo_carga} segundos` },
  { clave: "errores_sintaxis", icono: Code2, nombre: "Errores en el código", valor: (m) => `${m.errores_sintaxis} errores` },
  { clave: "imagenes_sin_alt", icono: Image, nombre: "Imágenes sin descripción",
    valor: (m) => `${m.imagenes_sin_alt} de ${m.total_imagenes} imágenes` },
  { clave: "enlaces_sin_texto", icono: Link2, nombre: "Enlaces sin texto",
    valor: (m) => `${m.enlaces_sin_texto} de ${m.total_enlaces} enlaces` },
  { clave: "sin_titulo", icono: FileText, nombre: "Título de la página", valor: (m) => (m.sin_titulo ? "No tiene" : "Sí tiene") },
  { clave: "sin_meta_descripcion", icono: Globe, nombre: "Descripción para Google",
    valor: (m) => (m.sin_meta_descripcion ? "No tiene" : "Sí tiene") },
  { clave: "sin_idioma", icono: Languages, nombre: "Idioma declarado", valor: (m) => (m.sin_idioma ? "No declarado" : "Declarado") },
  { clave: "h1_incorrecto", icono: Heading1, nombre: "Encabezado principal",
    valor: (m) => (m.total_h1 === 1 ? "Uno, correcto" : m.total_h1 === 0 ? "No tiene" : `Tiene ${m.total_h1}`) },
  { clave: "peso_html_kb", icono: Weight, nombre: "Tamaño de la página", valor: (m) => `${m.peso_html_kb} KB` },
];

const SINGULAR = { "imágenes": "imagen", enlaces: "enlace", errores: "error", segundos: "segundo" };

function hallazgo(r) {
  if (!r.unidad) return null;
  const unidad = Number(r.valor) === 1 ? SINGULAR[r.unidad] || r.unidad : r.unidad;
  const ideal = r.umbral === 0 ? "0" : `máximo ${r.umbral} ${r.unidad}`;
  return `Encontramos ${r.valor} ${unidad}. Lo recomendable: ${ideal}.`;
}

function Recomendacion({ r, n }) {
  const [abierta, setAbierta] = useState(n === 1);
  return (
    <article className={`tarjeta rec ${clasePrioridad(r.prioridad)}`}>
      <div className="rec-cab">
        <div className="rec-num">{n}</div>
        <div>
          <div className="etiquetas">
            <span className="tag prio">Prioridad {r.prioridad}</span>
            {r.areas.map((a) => <span key={a} className="tag">{a}</span>)}
          </div>
          <h3>{r.titulo}</h3>
          <p className="por-que"><b>¿Por qué importa?</b> {r.explicacion}</p>
          {hallazgo(r) && <p className="por-que" style={{ marginTop: 6 }}>{hallazgo(r)}</p>}
        </div>
      </div>
      <div className="rec-pie">
        <button onClick={() => setAbierta(!abierta)} aria-expanded={abierta}>
          {abierta ? <ChevronDown size={18} /> : <ChevronRight size={18} />} ¿Cómo lo soluciono?
        </button>
        {abierta && (
          <div className="rec-pasos">
            <p className="accion">{r.accion}</p>
            <p>{r.pasos}</p>
          </div>
        )}
      </div>
    </article>
  );
}

function Pertenencias({ titulo, valores }) {
  return (
    <div>
      <b>{titulo}</b>
      {Object.entries(valores).map(([nombre, v]) => (
        <div className="pertenencia" key={nombre}>
          <span>{nombre}</span>
          <div className="barra"><i style={{ width: `${v * 100}%` }} /></div>
          <span>{Math.round(v * 100)}%</span>
        </div>
      ))}
    </div>
  );
}

export default function Informe() {
  const { id } = useParams();
  const [inf, setInf] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setInf(null);
    api.informe(id).then(setInf).catch((e) => setError(e.message));
  }, [id]);

  if (error) return <div className="cargando">No se encontró el informe. <Link to="/historial">Ver historial</Link></div>;
  if (!inf) return <div className="cargando"><Loader2 className="girar" size={32} /></div>;

  const d = inf.diagnostico;
  const m = inf.metricas;
  const malas = new Set(d.recomendaciones.map((r) => r.metrica));
  const pt = d.pertenencias.tiempo_carga;
  const pe = d.pertenencias.errores_sintaxis;

  return (
    <>
      <div className="acciones" style={{ margin: "24px 0 16px" }}>
        <Link className="btn sec chico" to="/"><ArrowLeft size={16} /> Analizar otro sitio</Link>
        <Link className="btn sec chico" to={`/historial?sitio=${encodeURIComponent(dominio(inf.sitio))}`}>
          <RefreshCw size={16} /> Análisis anteriores de este sitio
        </Link>
      </div>

      {/* --------------------------------------------------------- Veredicto */}
      <section className={`veredicto ${claseNivel(d.nivel)}`}>
        <Medidor valor={d.puntaje} />
        <div>
          <div className="sitio"><Globe size={17} /> {inf.sitio}</div>
          <h1>Mantenimiento {d.nivel === "Al día" ? "al día" : d.nivel.toLowerCase()}</h1>
          <p className="mensaje">{d.mensaje}</p>
          <div className="datos-veredicto">
            <span className="insignia">
              {d.nivel === "Al día" ? <CheckCircle2 size={17} /> : <AlertTriangle size={17} />} Estado: {d.estado}
            </span>
            <span className="insignia" style={{ background: "var(--fondo-2)", color: "var(--texto-2)" }}>
              <Calendar size={16} /> {fechaLegible(inf.fecha)}
            </span>
          </div>
          {d.ajuste_semantico && (
            <div className="aviso-ajuste">
              <Scale size={20} />
              <div><b>¿Por qué «{d.nivel}» y no «{d.nivel_difuso}»?</b><br />{d.ajuste_semantico}</div>
            </div>
          )}
        </div>
      </section>

      {/* --------------------------------------------------------- Qué hacer */}
      <section className="seccion">
        <h2><span className="icono-titulo"><ListChecks size={20} /></span> Qué debe hacer</h2>
        <p className="desc">
          {d.recomendaciones.length
            ? `Encontramos ${d.recomendaciones.length} ${d.recomendaciones.length === 1 ? "aspecto" : "aspectos"} por mejorar, ordenados de lo más urgente a lo menos urgente.`
            : "No encontramos problemas en los aspectos que revisamos."}
        </p>
        <div className="recs">
          {d.recomendaciones.length === 0 && (
            <div className="tarjeta vacio"><CheckCircle2 size={40} /><h3>¡Todo en orden!</h3>Su sitio cumple las buenas prácticas revisadas.</div>
          )}
          {d.recomendaciones.map((r, i) => <Recomendacion key={r.recomendacion} r={r} n={i + 1} />)}
        </div>
      </section>

      {/* --------------------------------------------------------- Lo que revisamos */}
      <section className="seccion">
        <h2><span className="icono-titulo"><Activity size={20} /></span> Lo que revisamos</h2>
        <p className="desc">Estos son los datos que midió el Agente Analista en su página.</p>
        <div className="metricas">
          {METRICAS.map(({ clave, icono: Icono, nombre, valor }) => {
            const mal = malas.has(clave);
            return (
              <div key={clave} className={`tarjeta metrica ${mal ? "mal" : "bien"}`}>
                <div className="ic">{mal ? <XCircle size={20} /> : <Icono size={20} />}</div>
                <div><small>{nombre}</small><b>{valor(m)}</b></div>
              </div>
            );
          })}
        </div>
      </section>

      {/* --------------------------------------------------------- Razonamiento */}
      <section className="seccion">
        <h2><span className="icono-titulo"><BrainCircuit size={20} /></span> Cómo llegó el sistema a esta conclusión</h2>
        <p className="desc">
          Una computadora no sabe qué es «lento». Con <b>lógica difusa</b> el sistema interpreta los números como lo haría una
          persona, y con la <b>ontología</b> (una base de conocimiento sobre buenas prácticas web) decide qué recomendar y por qué.
        </p>
        <div className="rejilla-2">
          <div className="tarjeta">
            <h3 style={{ marginTop: 0 }}>1. Cómo interpretó los datos</h3>
            <Pertenencias titulo={`Tiempo de carga: ${m.tiempo_carga} s`} valores={pt} />
            <div style={{ height: 14 }} />
            <Pertenencias titulo={`Errores de código: ${m.errores_sintaxis}`} valores={pe} />
            <p className="desc" style={{ marginTop: 14, marginBottom: 0 }}>{d.explicacion_difusa}</p>
          </div>
          <div className="tarjeta">
            <h3 style={{ marginTop: 0 }}>2. Qué reglas aplicó</h3>
            {d.reglas_activadas.map((r) => (
              <div className="regla" key={r.regla}>
                <div className="si" dangerouslySetInnerHTML={{
                  __html: r.texto.replace(/(SI|Y|ENTONCES)/g, "<em>$1</em>"),
                }} />
                <small>{r.justificacion}</small>
                <div className="pertenencia" style={{ gridTemplateColumns: "1fr 48px", margin: 0 }}>
                  <div className="barra"><i style={{ width: `${r.fuerza * 100}%` }} /></div>
                  <span>{Math.round(r.fuerza * 100)}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="tarjeta" style={{ marginTop: 16 }}>
          <h3 style={{ marginTop: 0 }}>3. Qué dice la ontología</h3>
          <p className="desc" style={{ margin: 0 }}>
            El nivel <b>{d.nivel}</b> corresponde al estado <b>{d.estado}</b>: {d.explicacion_estado}{" "}
            Las recomendaciones, sus explicaciones y sus pasos se consultaron con SPARQL en la ontología{" "}
            <code>mantenimiento_web.owl</code>
            {d.areas_afectadas.length > 0 && <> y afectan las áreas de <b>{d.areas_afectadas.join(" y ")}</b></>}.
          </p>
        </div>
      </section>

      {/* --------------------------------------------------------- Agentes */}
      <section className="seccion">
        <h2><span className="icono-titulo"><MessagesSquare size={20} /></span> Conversación entre agentes</h2>
        <p className="desc">Mensajes FIPA-ACL que intercambiaron los agentes para producir este informe.</p>
        <div className="tarjeta">
          {inf.mensajes.length ? <Conversacion mensajes={inf.mensajes} />
            : <p className="desc" style={{ margin: 0 }}>Este informe es anterior al registro de conversaciones.</p>}
        </div>
      </section>

      {/* --------------------------------------------------------- JSON-LD */}
      <section className="seccion">
        <details className="tarjeta plegable">
          <summary>
            <span className="icono-titulo"><FileCode2 size={20} /></span>
            Datos semánticos guardados en MongoDB (JSON-LD)
            <ChevronRight className="giro" size={20} style={{ marginLeft: "auto" }} />
          </summary>
          <p className="desc" style={{ marginTop: 14 }}>
            El informe se guarda como <b>Linked Data</b>: el <code>@context</code> enlaza cada campo con schema.org y con la
            ontología, para que otros sistemas semánticos puedan leerlo. Equivale a <b>{inf.tripletas} tripletas RDF</b>.
          </p>
          <div className="acciones" style={{ marginBottom: 14 }}>
            <a className="btn chico" href={api.urlJsonld(inf.id)}><Download size={16} /> Descargar .jsonld</a>
          </div>
          <JsonLd documento={inf.jsonld} />
        </details>
      </section>
    </>
  );
}
