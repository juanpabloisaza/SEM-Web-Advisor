# Cómo trabajamos en equipo

## Ramas

- `main`: siempre debe funcionar. No se sube directo a `main`.
- Una rama por tarea, con prefijo de la fase:
  - `fase1/ontologia`, `fase2/fuzzy`, `fase3/agentes`, `fase4/mongodb`, `fase5/dashboard`
  - Correcciones: `fix/<descripcion-corta>`

## Flujo diario

```bash
git checkout main
git pull                      # traer lo último
git checkout -b fase2/fuzzy   # crear tu rama (solo la primera vez)
# ... trabajar ...
git add .
git commit -m "fuzzy: agrega reglas de mantenimiento"
git push -u origin fase2/fuzzy
```

Luego abrir un **Pull Request** en GitHub hacia `main` y pedir que otro integrante lo revise.

## Mensajes de commit

Formato: `<modulo>: <qué cambió>` en español, en presente.
Ejemplos: `ontologia: agrega clase Recomendacion`, `agentes: analista envía datos por ACL`.

## Reglas

- No subir el entorno virtual (`.venv/`), contraseñas ni archivos `.env` (ya están en `.gitignore`).
- Si agregas una librería, agrégala también a `requirements.txt`.
- Comentar el código, sobre todo la lógica clave (BDI de los agentes, reglas difusas, consultas SPARQL).
