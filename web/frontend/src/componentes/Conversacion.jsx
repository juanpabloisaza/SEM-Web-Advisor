const NOMBRES = { interfaz: "Usted", analista: "Analista", experto: "Experto", notificador: "Notificador" };

const SIGNIFICADO = {
  request: "solicita",
  agree: "acepta",
  inform: "informa",
  refuse: "rechaza",
  failure: "reporta fallo",
};

// Línea de tiempo de los mensajes FIPA-ACL intercambiados por los agentes.
export default function Conversacion({ mensajes }) {
  if (!mensajes?.length) return <p className="desc">Aún no hay mensajes.</p>;
  return (
    <div className="chat">
      {mensajes.map((m, i) => (
        <div className="msg" key={i} style={{ animationDelay: `${i * 60}ms` }}>
          <div className="ruta">
            {NOMBRES[m.de] || m.de}<span>→</span>{NOMBRES[m.para] || m.para}
          </div>
          <div className="res">
            <span className={`perf ${m.performativa}`} title={SIGNIFICADO[m.performativa]}>{m.performativa}</span>
            {m.resumen}
          </div>
          <div className="hora">{m.hora}</div>
        </div>
      ))}
    </div>
  );
}
