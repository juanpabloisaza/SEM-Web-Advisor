import { useEffect, useState } from "react";

// Velocímetro semicircular 0-100 con las tres zonas de la lógica difusa.
const CX = 150, CY = 150, R = 115;

function punto(valor, radio = R) {
  const ang = Math.PI * (1 - valor / 100);
  return [CX + radio * Math.cos(ang), CY - radio * Math.sin(ang)];
}

function arco(desde, hasta) {
  const [x1, y1] = punto(desde);
  const [x2, y2] = punto(hasta);
  return `M ${x1} ${y1} A ${R} ${R} 0 0 1 ${x2} ${y2}`;
}

const ZONAS = [
  { desde: 0, hasta: 35, color: "var(--ok)", nombre: "Al día" },
  { desde: 35, hasta: 65, color: "var(--aviso)", nombre: "Preventivo" },
  { desde: 65, hasta: 100, color: "var(--peligro)", nombre: "Urgente" },
];

export default function Medidor({ valor }) {
  const [animado, setAnimado] = useState(0);
  useEffect(() => {
    const t = setTimeout(() => setAnimado(valor), 80);
    return () => clearTimeout(t);
  }, [valor]);

  const ang = -90 + (animado / 100) * 180;

  return (
    <svg className="medidor" viewBox="0 0 300 185" role="img"
         aria-label={`Necesidad de mantenimiento: ${valor} de 100`}>
      {ZONAS.map((z) => (
        <path key={z.nombre} d={arco(z.desde + 0.8, z.hasta - 0.8)} stroke={z.color}
              strokeWidth="22" fill="none" strokeLinecap="round" opacity=".9" />
      ))}
      {[0, 50, 100].map((v) => {
        const [x, y] = punto(v, R - 34);
        return <text key={v} x={x} y={y + 4} textAnchor="middle" fontSize="11" fill="var(--texto-3)">{v}</text>;
      })}
      <g style={{ transform: `rotate(${ang}deg)`, transformOrigin: `${CX}px ${CY}px`,
                  transition: "transform 1.2s cubic-bezier(.2,.9,.25,1.15)" }}>
        <path d={`M ${CX - 7} ${CY} L ${CX} ${CY - R + 18} L ${CX + 7} ${CY} Z`} fill="var(--texto)" />
      </g>
      <circle cx={CX} cy={CY} r="13" fill="var(--texto)" />
      <circle cx={CX} cy={CY} r="5" fill="var(--superficie)" />
      <text x={CX} y={CY + 32} textAnchor="middle" fontSize="13" fontWeight="600" fill="var(--texto-2)">
        {valor} / 100
      </text>
    </svg>
  );
}
