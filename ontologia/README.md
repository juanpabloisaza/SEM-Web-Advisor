# Fase 1: Ontología (20%)

Archivo principal: **`mantenimiento_web.owl`** (OWL 2, formato RDF/XML). Se abre en Protégé 5.6.

Namespace: `http://www.semanticweb.org/sem-web-advisor/mantenimiento_web#` (prefijo `mw:`)

## Jerarquía de clases

```
owl:Thing
├── BuenasPracticas
│   ├── SEO
│   ├── Accesibilidad
│   └── Rendimiento
├── EstadoSitio            ≡ {Critico, Aceptable, Excelente}       (clase enumerada)
├── NivelMantenimiento     ≡ {Urgente, Preventivo, AlDia}           (salida de la lógica difusa)
├── Problema               ⊑ ∃ incumplePractica.BuenasPracticas
├── Accion
├── Recomendacion          ⊑ ∃ atiendeProblema.Problema ⊓ ∃ sugiereAccion.Accion ⊓ ∃ aplicaPractica.BuenasPracticas
│   ├── RecomendacionSEO            ≡ Recomendacion ⊓ ∃ aplicaPractica.SEO            (inferida)
│   ├── RecomendacionAccesibilidad  ≡ Recomendacion ⊓ ∃ aplicaPractica.Accesibilidad  (inferida)
│   └── RecomendacionRendimiento    ≡ Recomendacion ⊓ ∃ aplicaPractica.Rendimiento    (inferida)
├── SitioWeb               ⊑ schema:WebSite
│   ├── SitioCritico   ≡ SitioWeb ⊓ tieneEstado value Critico     (inferida)
│   ├── SitioAceptable ≡ SitioWeb ⊓ tieneEstado value Aceptable   (inferida)
│   └── SitioExcelente ≡ SitioWeb ⊓ tieneEstado value Excelente   (inferida)
└── InformeAuditoria       ⊑ schema:Report
```

Las 8 clases principales son **disjuntas** entre sí (`owl:AllDisjointClasses`).

## Propiedades de objeto

| Propiedad | Dominio → Rango | Características |
|---|---|---|
| **tieneEstado** *(enunciado)* | SitioWeb → EstadoSitio | Funcional |
| **sugiereAccion** *(enunciado)* | Recomendacion → Accion | |
| atiendeProblema | Recomendacion → Problema | Inversa de `seAtiendeCon` |
| aplicaPractica | Recomendacion → BuenasPracticas | |
| incumplePractica | Problema → BuenasPracticas | Inversa de `esIncumplidaPor` |
| presentaProblema | SitioWeb → Problema | |
| sitioIncumplePractica | SitioWeb → BuenasPracticas | **Cadena**: `presentaProblema ∘ incumplePractica` |
| correspondeAEstado | NivelMantenimiento → EstadoSitio | Funcional |
| analizaSitio, tieneNivel, incluyeRecomendacion | InformeAuditoria → … | |

Propiedades de datos: `metrica`, `umbral`, `unidad`, `gravedad`, `prioridad`, `explicacion`, `pasosSolucion`, `mensaje`, `url`.

## Cómo la usa el sistema

Cada **Problema** guarda *qué medir* (`metrica`) y *a partir de cuándo es problema* (`umbral`).
El Agente Experto recibe las métricas del Analista y, con **SPARQL**, busca los problemas cuyo
valor supera el umbral. De ahí obtiene la **Recomendación**, la **Acción** y la **explicación**
en lenguaje sencillo que se muestra en el Dashboard. Así, para cambiar un umbral o un texto
basta con editar la ontología en Protégé, sin tocar el código.

| Métrica (la mide el Analista) | Umbral | Problema | Área |
|---|---|---|---|
| `imagenes_sin_alt` | > 0 | Imágenes sin texto alternativo | Accesibilidad |
| `enlaces_sin_texto` | > 0 | Enlaces sin texto | Accesibilidad |
| `sin_idioma` (0/1) | > 0 | Idioma no declarado | Accesibilidad |
| `sin_titulo` (0/1) | > 0 | Página sin título | SEO |
| `sin_meta_descripcion` (0/1) | > 0 | Sin meta descripción | SEO |
| `h1_incorrecto` (0/1) | > 0 | Falta h1 o hay varios | SEO |
| `errores_sintaxis` | > 5 | Errores de sintaxis HTML | SEO + Accesibilidad |
| `tiempo_carga` (s) | > 3 | El servidor tarda en responder | Rendimiento |
| `peso_html_kb` | > 500 | Página demasiado pesada | Rendimiento |

## Archivos

- `mantenimiento_web.owl`: la ontología.
- `consultas.sparql`: 5 consultas de ejemplo para la pestaña *SPARQL Query* de Protégé.
- `consultas.py`: módulo Python (rdflib) que usa el Agente Experto. Para probarlo:
  ```bash
  python -m ontologia.consultas
  ```

## Probar el razonador en Protégé

1. *File → Open…* → `ontologia/mantenimiento_web.owl`
2. *Reasoner → HermiT* y luego *Reasoner → Start reasoner*
3. Resultado esperado (verificado con HermiT 1.4.3):
   - La ontología es **consistente**.
   - `SitioEjemplo` se clasifica como **SitioCritico**.
   - `SitioEjemplo` → *sitioIncumplePractica* → `PracticaCargaRapida`, `PracticaTextoAlternativo` (por la cadena de propiedades).
   - `RecValidarHTML` queda a la vez en **RecomendacionSEO** y **RecomendacionAccesibilidad**, porque su práctica (`PracticaHTMLValido`) es de ambos tipos.
