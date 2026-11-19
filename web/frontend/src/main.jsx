import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import Nav from "./componentes/Nav.jsx";
import Inicio from "./paginas/Inicio.jsx";
import Progreso from "./paginas/Progreso.jsx";
import Informe from "./paginas/Informe.jsx";
import Historial from "./paginas/Historial.jsx";
import ComoFunciona from "./paginas/ComoFunciona.jsx";
import "./estilos.css";

function App() {
  return (
    <BrowserRouter>
      <Nav />
      <main className="contenedor">
        <Routes>
          <Route path="/" element={<Inicio />} />
          <Route path="/analisis/:conv" element={<Progreso />} />
          <Route path="/informe/:id" element={<Informe />} />
          <Route path="/historial" element={<Historial />} />
          <Route path="/como-funciona" element={<ComoFunciona />} />
        </Routes>
      </main>
      <footer className="pie">
        SEM-Web-Advisor · Proyecto Final Web Semántica y Agentes Inteligentes · Politécnico Colombiano Jaime Isaza Cadavid
      </footer>
    </BrowserRouter>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
