import { useEffect, useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { BookOpen, History, Search } from "lucide-react";
import { api } from "../api.js";

export default function Nav() {
  const [salud, setSalud] = useState(null);

  useEffect(() => {
    const cargar = () => api.salud().then(setSalud).catch(() => setSalud(false));
    cargar();
    const t = setInterval(cargar, 15000);
    return () => clearInterval(t);
  }, []);

  return (
    <header className="nav">
      <div className="contenedor nav-int">
        <Link to="/" className="marca">
          <img src="/favicon.svg" alt="" />
          <div>
            SEM-Web-Advisor
            <small>Mantenimiento web inteligente</small>
          </div>
        </Link>
        <nav className="nav-links">
          <NavLink to="/" end><Search size={17} /><span>Analizar</span></NavLink>
          <NavLink to="/historial"><History size={17} /><span>Historial</span></NavLink>
          <NavLink to="/como-funciona"><BookOpen size={17} /><span>¿Cómo funciona?</span></NavLink>
        </nav>
        <div className="estado-sistema" title="Estado de los componentes del sistema">
          <span className="pildora">
            <i className={`punto ${salud?.agentes_activos ? "on" : "off"}`} /> Agentes
          </span>
          <span className="pildora">
            <i className={`punto ${salud?.mongodb ? "on" : "off"}`} /> {salud?.mongodb ? "MongoDB" : "Memoria"}
          </span>
        </div>
      </div>
    </header>
  );
}
