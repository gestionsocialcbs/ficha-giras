# Ficha de Giras de Prestaciones Sociales

Ficha por OOAD de las Prestaciones Sociales del IMSS en dos hojas tamaño carta. Incluye:

- responsables;
- ranking de productividad;
- avance de inscripciones y asistencias por área;
- georreferencia de UOPSI y municipios prioritarios;
- gimnasios, plantilla, infraestructura acuática y acervo;
- Top 10 de actividades;
- dignificación de la infraestructura (PPI del APEF 2027 y mantenimiento);
- unidades por tipo, teatros, georreferencia de velatorios y tiendas, y Mundialito IMSS.

Es un sitio estático: no requiere servidor, base de datos ni instalación.

## Publicar en GitHub Pages

1. En GitHub, crea un repositorio nuevo, por ejemplo `ficha-giras`.
2. Sube **todo el contenido de esta carpeta**: `index.html`, `.nojekyll`, `README.md` y las carpetas `assets/`, `datos/` y `herramientas/`. Puedes arrastrar los archivos en *Add file → Upload files*.
3. En el repositorio, entra a **Settings → Pages**. En *Source* elige **Deploy from a branch**, luego la rama **main** y la carpeta **/ (root)**, y guarda.
4. En uno o dos minutos la ficha queda publicada en `https://<tu-usuario>.github.io/ficha-giras/`.

> **Importante:** si el repositorio es público, cualquier persona con la liga puede ver la ficha y sus datos, incluidos los nombres de los responsables. Si la información es de uso interno, publícala en un repositorio privado de una organización con GitHub Pages restringido, o compártela solo como archivos.

## Uso

- **Selector de OOAD:** cambia toda la ficha. La dirección se actualiza (`?ooad=5`), así que puedes compartir la liga de una OOAD específica.
- **Mapas (5 y 17):** botones + / − / ⟲ para acercar, alejar y restablecer; arrastra para moverte, doble clic para acercar y Ctrl + rueda del ratón para hacer zoom.
- **Descargar PDF:** genera un PDF con las dos hojas carta de la OOAD seleccionada. Funciona en Chrome, Edge y Firefox.
- **Imprimir:** Ctrl + P también imprime las dos hojas en tamaño carta.
- **Sin conexión:** abrir `index.html` con doble clic también funciona, porque todo está dentro de la carpeta.

## Actualizar los datos

Los datos viven en `assets/data.js`. Para regenerarlos desde los Excel de origen:

```bash
pip install pandas openpyxl
python herramientas/actualizar_datos.py \
  --catalogos General_Catalogos.xlsx \
  --inscritos Claude_inscritos.xlsx \
  --asistencias Asistencias.xlsx \
  --plantilla Plantilla.xlsx \
  --patrimonio 2026_REGISTRO_REVISADO_DEL_PATRIMONIO_CULTURAL_IMSS.xlsx \
  --plantilla-unidades 1_Plantilla.xlsx
```

Después sube a GitHub el `assets/data.js` actualizado.

Los datos que no vienen en Excel están en la carpeta `datos/` en formato JSON y se editan ahí:

- `ppi_apef2027.json`: PPI del Anteproyecto de Presupuesto de Egresos de la Federación 2027, CBS, 20 de octubre de 2026;
- `mantenimiento.json`: por ahora solo Coahuila;
- `plantilla_nombres_unidad.json`: nombre oficial de cada unidad de `1_Plantilla.xlsx` (por clave de adscripción). Si llega una unidad nueva, agrega aquí su nombre.

| Hoja o archivo de origen | Alimenta |
|---|---|
| `General_Catalogos.xlsx` · OOAD, Ranking, Directorio, Mun_prioritarios | Selector, ranking (2), responsables (1), municipios prioritarios (6) |
| `General_Catalogos.xlsx` · UOPSI | Mapa (5), unidades, CSS y teatros (13 a 16), mapa de velatorios y tiendas (17) |
| `General_Catalogos.xlsx` · Cat_Gym, Instal_Acuáticas, Top_Actividades, Mundialito_IMSS | Gimnasios (7), acuática (9), Top 10 (11), Mundialito (18). Del Mundialito no se publican responsable ni contacto. |
| `Claude_inscritos.xlsx` | Avance de inscripciones (3) |
| `Asistencias.xlsx` | Avance de asistencias (4); se omite la fila de total nacional |
| `Plantilla.xlsx` | Plazas autorizadas, cubiertas y vacantes (8) |
| `1_Plantilla.xlsx` | Personas voluntarias (8); el detalle por puesto y unidad queda en los datos |
| `2026_REGISTRO_REVISADO_DEL_PATRIMONIO_CULTURAL_IMSS.xlsx` | Acervo cultural (10): bienes por OOAD y tipología de obra, con la arquitectura (bienes inmuebles) como «Piezas de arquitectura»; los registros de Nivel Central no se asignan a ninguna OOAD |

## Créditos y licencias

- **Tipografía:** Noto Sans (SIL Open Font License), incrustada en `assets/fonts.css`.
- **Gráficos:** [D3 v7.9.0](https://d3js.org) (licencia ISC), en `assets/d3.v7.9.0.min.js`.
- **Cartografía:** Marco Geoestadístico INEGI 2023, en la versión de CONABIO, tomada de [PhantomInsights/mexico-geojson](https://github.com/PhantomInsights/mexico-geojson) (MIT) y simplificada.

## Estructura

```
ficha-giras/
├── index.html              Ficha (diseño, cálculos y gráficos)
├── .nojekyll               Indica a GitHub Pages que sirva los archivos tal cual
├── assets/
│   ├── data.js             Datos de las 35 OOAD
│   ├── dash-shim.js        Carga de datos, selector y descarga del PDF
│   ├── d3.v7.9.0.min.js    Librería de gráficos
│   ├── fonts.css           Noto Sans incrustada
│   ├── mx_estados.js       Límites estatales
│   └── mun_prioritarios.js Polígonos de municipios prioritarios
├── datos/                  Datos capturados a mano (PPI, mantenimiento)
└── herramientas/
    └── actualizar_datos.py Regenera assets/data.js desde los Excel
```
