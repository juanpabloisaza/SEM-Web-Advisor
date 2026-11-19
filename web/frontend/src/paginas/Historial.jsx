import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { AlertOctagon, AlertTriangle, CheckCircle2, ChevronRight, History, Inbox, Loader2, Search } from "lucide-react";
import { api, claseNivel, fechaLegible } from "../api.js";

export default function Historial() {
  const [params, setParams] = useSearchParams();
  const sitio = params.get("sitio") || "";
  const [filtro, setFiltro] = useState(sitio);
  const [informes, setInformes] = useState(null);
  const [stats, setStats] = useState(null);

  useEffect(() => { api.estadisticas().then(setStats).catch(() => {}); }, []);

  useEffect(() => {
    const t = setTimeout(() => {
      api.informes(filtro).then(setInformes).catch(() => setInformes([]));
      setParams(filtro ? { sitio: filtro } : {}, { replace: true });
    }, 250);
    return () => clearTimeout(t);
    // setParams cambia de identidad en cada navegación: no se incluye para no entrar en bucle
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtro]);

  return (
    <section className="seccion" style={{ marginTop: 36 }}>
      <h2><span className="icono-titulo"><History size={20} /></span> Historial de análisis</h2>
      <p className="desc">Todos los informes guardados en la base de datos semántica.</p>

      {stats && (
        <div className="stats">
          <div className="tarjeta stat"><b>{stats.total}</b><small>Análisis realizados</small></div>
          <div className="tarjeta stat urgente"><b>{stats.por_nivel.Urgente}</b><small>Urgentes</small></div>
          <div className="tarjeta stat preventivo"><b>{stats.por_nivel.Preventivo}</b><small>Preventivos</small></div>
          <div className="tarjeta stat aldia"><b>{stats.por_nivel["Al día"]}</b><small>Al día</small></div>
        </div>
      )}

      <label className="filtro" style={{ marginBottom: 16 }}>
        <Search size={18} />
        <input value={filtro} onChange={(e) => setFiltro(e.target.value)} placeholder="Buscar por sitio…" />
      </label>

      {!informes && <div className="cargando"><Loader2 className="girar" size={28} /></div>}
      {informes?.length === 0 && (
        <div className="tarjeta vacio">
          <Inbox size={36} color="var(--texto-3)" />
          <p>No hay análisis {filtro ? "para esa búsqueda" : "todavía"}.</p>
          <Link className="btn chico" to="/">Analizar un sitio</Link>
        </div>
      )}

      <div className="lista">
        {informes?.map((i) => (
          <Link key={i.id} to={`/informe/${i.id}`} className={`tarjeta fila ${claseNivel(i.nivel)}`}>
            <div className="score" title={`Necesidad de mantenimiento: ${i.puntaje}/100`}>
              {i.nivel === "Urgente" ? <AlertOctagon size={26} />
                : i.nivel === "Preventivo" ? <AlertTriangle size={26} /> : <CheckCircle2 size={26} />}
            </div>
            <div>
              <div className="url">{i.sitio}</div>
              <small>{fechaLegible(i.fecha)} · {i.recomendaciones} recomendaciones</small>
            </div>
            <div className="etiquetas" style={{ margin: 0 }}>
              {i.areas.map((a) => <span key={a} className="tag">{a}</span>)}
            </div>
            <span className="insignia">{i.nivel} <ChevronRight size={16} /></span>
          </Link>
        ))}
      </div>
    </section>
  );
}
